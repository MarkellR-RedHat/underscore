"""master: raw render -> broadcast-ready bed.

Chain: highpass -> compressor -> gentle shelves -> light reverb -> limiter,
then loudness normalization to the brief's target (default -14 LUFS, the
YouTube reference), fades, and an optional speech-ducked variant.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from .brief import Brief, Span

SR = 48000


def _read(path: str | Path) -> tuple[np.ndarray, int]:
    y, sr = sf.read(path, always_2d=True, dtype="float32")
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    return y, sr


def _fades(y: np.ndarray, sr: int, fade_in: float, fade_out: float) -> np.ndarray:
    n = len(y)
    ni, no = min(n, int(fade_in * sr)), min(n, int(fade_out * sr))
    if ni:
        y[:ni] *= (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ni)))[:, None]
    if no:
        y[-no:] *= (0.5 + 0.5 * np.cos(np.linspace(0, np.pi, no)))[:, None]
    return y


def _brickwall(y: np.ndarray, sr: int, ceiling_db: float = -1.0,
               lookahead_ms: float = 5.0, release_ms: float = 80.0) -> np.ndarray:
    """Transparent peak limiter: gain reduction only, never makeup gain.

    Block-based: per-block required gain, lookahead via a running minimum,
    exponential release, then linear interpolation back to sample rate.
    """
    ceiling = 10 ** (ceiling_db / 20)
    blk = max(1, int(sr * 0.001))                 # 1 ms blocks
    n = len(y)
    nb = int(np.ceil(n / blk))
    pad = nb * blk - n
    # Measure TRUE peak per block: 4x oversampling exposes the inter-sample
    # peaks that a sample-domain limiter misses, which is what the gate checks.
    import librosa
    up = librosa.resample(np.pad(y, ((0, pad), (0, 0))).T, orig_sr=sr, target_sr=sr * 4, res_type="soxr_hq")
    mag = np.abs(up).max(axis=0).reshape(nb, blk * 4).max(axis=1)
    req = np.minimum(1.0, ceiling / np.maximum(mag, 1e-9))
    look = max(1, int(lookahead_ms))               # blocks of lookahead
    g = req.copy()
    for k in range(1, look + 1):                    # running minimum over the lookahead window
        g[:-k] = np.minimum(g[:-k], req[k:])
    rel = np.exp(-1.0 / max(1.0, release_ms))      # per-block release coefficient
    out = np.empty_like(g)
    cur = 1.0
    for i in range(nb):                             # ~1000 iterations per second of audio
        cur = g[i] if g[i] < cur else cur + (g[i] - cur) * (1.0 - rel)
        out[i] = cur
    edges = np.arange(nb + 1) * blk
    centers = edges[:-1] + blk / 2
    gain = np.interp(np.arange(n), centers, out)
    return (y * gain[:, None]).astype(np.float32)


def _normalize(y: np.ndarray, sr: int, target_lufs: float) -> tuple[np.ndarray, float]:
    import pyloudnorm as pyln
    meter = pyln.Meter(sr)
    loud = meter.integrated_loudness(y.astype(np.float64))
    if not np.isfinite(loud):
        return y, loud
    gain = 10 ** ((target_lufs - loud) / 20)
    return (y * gain).astype(np.float32), loud


def master(in_wav: str | Path, out_wav: str | Path, brief: Brief,
           reference: str | Path | None = None,
           fade_in: float = 1.5, fade_out: float = 3.0) -> dict:
    from pedalboard import (Pedalboard, Compressor, HighpassFilter, LowShelfFilter,
                            HighShelfFilter, Reverb)
    y, sr = _read(in_wav)

    board = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=30),
        Compressor(threshold_db=-18, ratio=2.5, attack_ms=12, release_ms=140),
        LowShelfFilter(cutoff_frequency_hz=120, gain_db=1.5),
        HighShelfFilter(cutoff_frequency_hz=8000, gain_db=1.0),
        Reverb(room_size=0.18, wet_level=0.07, dry_level=0.93, width=0.8),
    ])
    y = board(y.T, sr).T

    matched = False
    if reference:
        try:
            import matchering as mg  # optional
            tmp_t = Path(out_wav).with_suffix(".pre.wav")
            tmp_o = Path(out_wav).with_suffix(".matched.wav")
            sf.write(tmp_t, y, sr, subtype="PCM_24")
            mg.process(target=str(tmp_t), reference=str(reference),
                       results=[mg.pcm24(str(tmp_o))])
            y, sr = _read(tmp_o)
            matched = True
            tmp_t.unlink(missing_ok=True)
        except ImportError:
            pass

    y, before = _normalize(y, sr, brief.target_lufs)
    y = _brickwall(y, sr, ceiling_db=-1.5)   # true-peak ceiling (oversampled inside the limiter)
    y, _ = _normalize(y, sr, brief.target_lufs)   # second pass: recover loudness the limiter took
    y = _brickwall(y, sr, ceiling_db=-1.5)
    y = _fades(y, sr, fade_in, fade_out)
    y = np.clip(y, -1.0, 1.0)
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_wav, y, sr, subtype="PCM_24")
    return {"master": str(out_wav), "pre_normalize_lufs": float(before),
            "target_lufs": brief.target_lufs, "reference_matched": matched}


def duck(in_wav: str | Path, out_wav: str | Path, speech: list[Span],
         depth_db: float = -18.0, ramp: float = 0.4, pre: float = 0.15) -> str:
    """Bake speech-aware volume automation into a copy of the master."""
    y, sr = _read(in_wav)
    n = len(y)
    gain = np.ones(n, dtype=np.float32)
    low = 10 ** (depth_db / 20)
    r = max(1, int(ramp * sr))
    for sp in speech:
        a = max(0, int((sp.start - pre) * sr))
        b = min(n, int((sp.end + pre) * sr))
        if b <= a:
            continue
        gain[a:b] = np.minimum(gain[a:b], low)
        ra, rb = max(0, a - r), min(n, b + r)
        if a > ra:
            gain[ra:a] = np.minimum(gain[ra:a], np.linspace(1.0, low, a - ra))
        if rb > b:
            gain[b:rb] = np.minimum(gain[b:rb], np.linspace(low, 1.0, rb - b))
    sf.write(out_wav, y * gain[:, None], sr, subtype="PCM_24")
    return str(out_wav)


def preview_mp3(wav: str | Path, mp3: str | Path) -> str | None:
    if not shutil.which("ffmpeg"):
        return None
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)], check=False)
    return str(mp3) if Path(mp3).exists() else None
