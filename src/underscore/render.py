"""render: code -> WAV.

Two engines:
  sonicpi : headless Sonic Pi via sonic-pi-tool (app must be running)
  synth   : a small built-in numpy synth that renders the BRIEF directly. It
            exists so the whole pipeline (master, measure, export) can run on a
            machine where headless Sonic Pi is not working yet, and so tests
            never depend on an external app. It also produces stems.
"""
from __future__ import annotations

import math
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import soundfile as sf

from .brief import Brief

SR = 48000


class RenderError(RuntimeError):
    """Sonic Pi ran but reported errors; the program needs recomposing."""

    def __init__(self, errors: list[str], log: str, raw: str | None = None):
        super().__init__("Sonic Pi runtime errors:\n" + "\n".join(errors))
        self.errors, self.log, self.raw = errors, log, raw


# ---------------------------------------------------------------- sonic pi --

APP_SERVER = Path("/Applications/Sonic Pi.app/Contents/Resources/app/server")
RUBY = APP_SERVER / "native" / "ruby" / "bin" / "ruby"
BOOT_LIB = APP_SERVER / "ruby" / "bin" / "headless_boot.rb"
RECORDER = Path(__file__).resolve().parents[2] / "vendor" / "underscore-record.rb"


def sonicpi_available() -> bool:
    """Sonic Pi 5 ships a headless boot library; our recorder builds on it."""
    return RUBY.exists() and BOOT_LIB.exists() and RECORDER.exists()


def render_sonicpi(program: str, brief: Brief, out_wav: Path, tail: float = 12.0) -> dict:
    """tail covers the spider's start latency on a fresh boot (synth loading can
    delay the first note by several seconds) so the outro is never truncated."""
    if not sonicpi_available():
        raise RuntimeError("Sonic Pi 5 not found at /Applications/Sonic Pi.app (brew install --cask sonic-pi)")
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    rb = out_wav.with_suffix(".rb")
    rb.write_text(program)
    raw = out_wav.with_suffix(".sonicpi.wav")
    cmd = [str(RUBY), str(RECORDER), "-o", str(raw), "-d", f"{brief.duration + tail:.2f}",
           "-f", str(rb), "-s", str(brief.seed)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=brief.duration + 120)
    log = proc.stdout + proc.stderr
    errors = [ln for ln in log.splitlines() if "ERROR" in ln]
    if proc.returncode == 1 or not raw.exists():
        raise RuntimeError("Sonic Pi headless render produced no audio:\n" + log[-1500:])
    if errors:
        raise RenderError(errors, log[-4000:], str(raw))
    y, sr = sf.read(raw, always_2d=True)
    preroll = _preroll_seconds(y, sr)
    y = _align_and_trim(y, sr, brief.duration)
    y = _resample(y, sr, SR)
    sf.write(out_wav, y, SR, subtype="PCM_24")
    return {"engine": "sonicpi", "raw": str(out_wav), "stems": {}, "source": str(rb),
            "preroll_s": round(preroll, 2), "sonicpi_errors": errors, "sonicpi_log": log[-4000:]}


def _preroll_seconds(y: np.ndarray, sr: int, floor_db: float = -50.0) -> float:
    mag = np.abs(y).max(axis=1)
    thr = 10 ** (floor_db / 20)
    return float(np.argmax(mag > thr)) / sr if (mag > thr).any() else 0.0


def _align_and_trim(y: np.ndarray, sr: int, duration: float, floor_db: float = -50.0) -> np.ndarray:
    """Drop the pre-roll silence before the first sound, then cut to duration."""
    mag = np.abs(y).max(axis=1)
    thr = 10 ** (floor_db / 20)
    idx = np.argmax(mag > thr) if (mag > thr).any() else 0
    y = y[idx:]
    n = int(duration * sr)
    if len(y) < n:
        y = np.vstack([y, np.zeros((n - len(y), y.shape[1]))])
    return y[:n]


def _resample(y: np.ndarray, sr: int, target: int) -> np.ndarray:
    if sr == target:
        return y
    import librosa
    return librosa.resample(y.T, orig_sr=sr, target_sr=target).T


# ------------------------------------------------------------------- synth --

NOTE_INDEX = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6,
              "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
MAJOR = [0, 2, 4, 5, 7, 9, 11]
MINOR = [0, 2, 3, 5, 7, 8, 10]
PROG = {"major": [0, 4, 5, 3], "minor": [0, 5, 2, 6]}   # I V vi IV / i VI III VII


def _midi(root: str, octave: int = 3) -> int:
    return 12 * (octave + 1) + NOTE_INDEX.get(root, 2)


def _f(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


def _env(n: int, a: float, r: float, sr: int = SR) -> np.ndarray:
    e = np.ones(n)
    na, nr = min(n, int(a * sr)), min(n, int(r * sr))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def _saw(freq: float, n: int, sr: int = SR) -> np.ndarray:
    t = np.arange(n) / sr
    return 2 * ((t * freq) % 1.0) - 1


def _lowpass(x: np.ndarray, cutoff: float, sr: int = SR) -> np.ndarray:
    k = max(1, int(sr / max(60.0, cutoff) / 2))
    kern = np.ones(k) / k
    return np.convolve(x, kern, mode="same")


def _chord_tones(root_midi: int, mode: str, degree: int) -> list[int]:
    sc = MAJOR if mode == "major" else MINOR
    return [root_midi + sc[(degree + k) % 7] + 12 * ((degree + k) // 7) for k in (0, 2, 4)]


def render_synth(brief: Brief, out_wav: Path) -> dict:
    rng = np.random.default_rng(brief.seed)
    sr = SR
    total = int(brief.duration * sr)
    stems = {k: np.zeros(total) for k in ("pads", "bass", "drums", "motif")}
    root = _midi(brief.key, 3)
    beat = brief.beat_len
    bar = brief.bar_len
    prog = PROG[brief.mode]
    sc = MAJOR if brief.mode == "major" else MINOR

    for s in brief.sections:
        n_bars = max(1, int(round(s.duration / bar)))
        for b in range(n_bars):
            t0 = s.start + b * bar
            if t0 >= brief.duration:
                break
            i0 = int(t0 * sr)
            n = min(int(bar * sr), total - i0)
            if n <= 0:
                break
            deg = prog[b % 4]
            tones = _chord_tones(root, brief.mode, deg)
            # pads: detuned saws, filtered, slow envelope
            pad = np.zeros(n)
            for m in tones:
                for det in (-0.06, 0.0, 0.06):
                    pad += _saw(_f(m + 12 + det), n)
            cutoff = 400 + 1800 * s.energy
            pad = _lowpass(pad, cutoff) * _env(n, min(0.6, bar * 0.3), min(0.8, bar * 0.35))
            stems["pads"][i0:i0 + n] += pad * (0.045 + 0.03 * s.energy)
            # bass: root, on beats 1 and 3 (all beats when energetic)
            hits = [0, 2] if s.energy < 0.65 else [0, 1, 2, 3]
            for k in hits:
                j0 = int(k * beat * sr)
                ln = min(int(beat * 0.9 * sr), n - j0)
                if ln > 0:
                    tt = np.arange(ln) / sr
                    bass = np.sin(2 * math.pi * _f(tones[0] - 12) * tt) * _env(ln, 0.01, 0.15)
                    stems["bass"][i0 + j0:i0 + j0 + ln] += bass * (0.18 + 0.1 * s.energy)
            # drums by energy
            if s.energy >= 0.4:
                for k in range(8):                        # hats on 8ths
                    j0 = int(k * beat / 2 * sr)
                    ln = min(int(0.03 * sr), n - j0)
                    if ln > 0:
                        stems["drums"][i0 + j0:i0 + j0 + ln] += rng.standard_normal(ln) * _env(ln, 0.001, 0.02) * (0.02 + 0.03 * s.energy)
            if s.energy > 0.65:
                for k in (0, 2):                          # kick on 1 and 3
                    j0 = int(k * beat * sr)
                    ln = min(int(0.25 * sr), n - j0)
                    if ln > 0:
                        tt = np.arange(ln) / sr
                        kick = np.sin(2 * math.pi * (55 + 80 * np.exp(-tt * 30)) * tt) * _env(ln, 0.001, 0.2)
                        stems["drums"][i0 + j0:i0 + j0 + ln] += kick * 0.35
                # motif: pentatonic arpeggio, 8ths, above the vocal range
                pent = [sc[0], sc[1], sc[2], sc[4], sc[5]]
                for k in range(8):
                    j0 = int(k * beat / 2 * sr)
                    ln = min(int(beat * 0.45 * sr), n - j0)
                    if ln > 0:
                        m = root + 24 + pent[(k * 3 + b) % 5]
                        tt = np.arange(ln) / sr
                        pl = np.sin(2 * math.pi * _f(m) * tt) * np.exp(-tt * 6) * _env(ln, 0.002, 0.05)
                        stems["motif"][i0 + j0:i0 + j0 + ln] += pl * 0.12

    for h in brief.hits:
        i0 = int(max(0.0, h.t - (1.5 if h.kind == "riser" else 0.0)) * sr)
        ln = min(int(1.5 * sr), total - i0)
        if ln <= 0:
            continue
        tt = np.arange(ln) / sr
        if h.kind == "riser":
            noise = rng.standard_normal(ln)
            sweep = _lowpass(noise, 300) * (tt / tt[-1]) ** 2
            stems["drums"][i0:i0 + ln] += sweep * 0.25
        else:
            thump = np.sin(2 * math.pi * (70 + 50 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 4)
            stems["drums"][i0:i0 + ln] += thump * 0.4

    mix = sum(stems.values())
    peak = np.abs(mix).max() or 1.0
    scale = min(1.0, 0.5 / peak)
    mix = mix * scale
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    stereo = np.stack([mix, mix], axis=1)
    sf.write(out_wav, stereo, sr, subtype="PCM_24")
    stem_paths = {}
    for k, v in stems.items():
        p = out_wav.with_name(f"{out_wav.stem}.stem-{k}.wav")
        sf.write(p, np.stack([v * scale, v * scale], axis=1), sr, subtype="PCM_24")
        stem_paths[k] = str(p)
    return {"engine": "synth", "raw": str(out_wav), "stems": stem_paths}


def render(program: str | None, brief: Brief, out_wav: str | Path, engine: str = "auto") -> dict:
    out_wav = Path(out_wav)
    if engine == "auto":
        engine = "sonicpi" if (program and sonicpi_available()) else "synth"
    if engine == "sonicpi":
        if not program:
            raise ValueError("sonicpi engine needs a program (run compose first)")
        return render_sonicpi(program, brief, out_wav)
    return render_synth(brief, out_wav)
