"""measure: the gate. Numbers, not vibes.

We cannot listen, so we measure: integrated loudness, true peak, loudness
range, spectral centroid, and per-section onset density against the energy
the brief asked for. Out of spec means the track does not ship.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .brief import Brief


def _true_peak_dbtp(y: np.ndarray, sr: int) -> float:
    import librosa
    up = librosa.resample(y.T, orig_sr=sr, target_sr=sr * 4)
    peak = float(np.abs(up).max()) or 1e-9
    return 20 * np.log10(peak)


def measure(wav: str | Path, brief: Brief, loop: bool = False) -> dict:
    import librosa
    import pyloudnorm as pyln
    y, sr = sf.read(wav, always_2d=True, dtype="float64")
    mono = y.mean(axis=1)
    meter = pyln.Meter(sr)
    lufs = float(meter.integrated_loudness(y))

    # loudness range: spread of 3 s short-term loudness (10th to 95th percentile)
    win = int(3 * sr); hop = int(1 * sr)
    st = []
    for i in range(0, max(1, len(y) - win), hop):
        seg = y[i:i + win]
        if len(seg) >= win:
            v = meter.integrated_loudness(seg)
            if np.isfinite(v) and v > -70:
                st.append(v)
    lra = float(np.percentile(st, 95) - np.percentile(st, 10)) if len(st) > 2 else 0.0

    centroid = float(librosa.feature.spectral_centroid(y=mono, sr=sr).mean())
    onset = librosa.onset.onset_strength(y=mono, sr=sr)
    frames_per_s = sr / 512
    sections = []
    for s in brief.sections:
        a, b = int(s.start * sr), int(min(s.end, brief.duration) * sr)
        seg = mono[a:b]
        rms = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
        fa, fb = int(s.start * frames_per_s), int(s.end * frames_per_s)
        dens = float(onset[fa:fb].mean()) if fb > fa else 0.0
        sections.append({"start": s.start, "end": s.end, "energy_requested": s.energy,
                         "rms_dbfs": 20 * np.log10(rms) if rms > 0 else -120.0,
                         "onset_density": dens})
    corr = None
    if len(sections) >= 3:
        req = np.array([x["energy_requested"] for x in sections])
        got = np.array([x["onset_density"] for x in sections])
        if req.std() > 0 and got.std() > 0:
            corr = float(np.corrcoef(req, got)[0, 1])

    out = {
        "duration_s": len(y) / sr,
        "sample_rate": sr,
        "lufs_integrated": lufs,
        "true_peak_dbtp": _true_peak_dbtp(y, sr),
        "loudness_range_lu": lra,
        "spectral_centroid_hz": centroid,
        "energy_correlation": corr,
        "sections": sections,
    }
    if loop:
        # the tile point: the last 50 ms must hand off to the first 50 ms
        w = max(1, int(0.05 * sr))
        def _rms_db(seg):
            r = float(np.sqrt(np.mean(seg ** 2)))
            return 20 * np.log10(r) if r > 0 else -120.0
        out["loop_seam_db"] = abs(_rms_db(mono[:w]) - _rms_db(mono[-w:]))
    return out


def gate(m: dict, brief: Brief, lufs_tolerance: float = 1.0,
         loop_trim_s: float = 0.0) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if abs(m["lufs_integrated"] - brief.target_lufs) > lufs_tolerance:
        reasons.append(f"loudness {m['lufs_integrated']:.1f} LUFS, target {brief.target_lufs:.1f} ±{lufs_tolerance}")
    if m["true_peak_dbtp"] > -1.0:
        reasons.append(f"true peak {m['true_peak_dbtp']:.2f} dBTP exceeds -1.0")
    expected = brief.duration - loop_trim_s
    if abs(m["duration_s"] - expected) > 0.25:
        reasons.append(f"duration {m['duration_s']:.2f}s, expected {expected:.2f}s")
    if m.get("loop_seam_db") is not None and m["loop_seam_db"] > 6.0:
        reasons.append(f"loop seam mismatch: first and last 50 ms differ by {m['loop_seam_db']:.1f} dB (> 6.0)")
    for s in m["sections"]:
        if s["rms_dbfs"] < -45:
            reasons.append(f"section {s['start']:.1f}-{s['end']:.1f}s is effectively silent ({s['rms_dbfs']:.0f} dBFS)")
    if m["energy_correlation"] is not None and m["energy_correlation"] < 0.3:
        reasons.append(f"energy curve does not follow the brief (corr {m['energy_correlation']:.2f} < 0.30)")
    return (not reasons), reasons
