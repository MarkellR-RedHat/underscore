"""audiogen: brief -> audio via a text-to-music model.

A third engine alongside sonicpi and synth. Sends the brief as a
natural-language prompt to an audio generation model and receives
audio directly. No Sonic Pi, no code composition step.

Nothing is bundled. Bring your own model:
  UNDERSCORE_AUDIOGEN_URL   : HTTP endpoint that accepts a prompt and
                              returns audio bytes or JSON with audio.
  UNDERSCORE_AUDIOGEN_KEY   : bearer token, when the endpoint needs one.
  UNDERSCORE_AUDIOGEN_MODEL : model name, when the endpoint serves
                              multiple (falls back to UNDERSCORE_MODEL).
  UNDERSCORE_AUDIOGEN_CLI   : CLI command; called with --output <path>
                              --duration <seconds>, prompt on stdin.
"""
from __future__ import annotations

import io
import json
import os
import shlex
import subprocess
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

from .brief import Brief
from . import collections as _collections

SR = 48000


def build_audio_prompt(brief: Brief) -> str:
    coll = _collections.get(getattr(brief, "collection", "analog") or "analog")

    energy_word = {
        (0.0, 0.3): "very low",
        (0.3, 0.45): "low",
        (0.45, 0.65): "moderate",
        (0.65, 0.8): "high",
        (0.8, 1.01): "very high",
    }

    def _energy(e: float) -> str:
        for (lo, hi), word in energy_word.items():
            if lo <= e < hi:
                return word
        return "moderate"

    section_descs = []
    for s in brief.sections:
        section_descs.append(
            f"{s.mood} mood at {_energy(s.energy)} energy for {s.duration:.0f}s"
        )

    return " ".join([
        f"Instrumental background music, {brief.duration:.0f} seconds,",
        f"{brief.bpm} BPM, {brief.key} {brief.mode}.",
        f"Style: {coll.sound}",
        "Structure: " + "; then ".join(section_descs) + ".",
        "No vocals, no lyrics, no sound effects.",
        "Suitable as background under spoken narration.",
    ])


def audiogen_available() -> bool:
    return bool(
        os.environ.get("UNDERSCORE_AUDIOGEN_URL")
        or os.environ.get("UNDERSCORE_AUDIOGEN_CLI")
    )


def _resolve_model(explicit: str | None) -> str | None:
    return (
        explicit
        or os.environ.get("UNDERSCORE_AUDIOGEN_MODEL")
        or os.environ.get("UNDERSCORE_MODEL")
        or None
    )


def _run_api(prompt: str, duration: float, model: str | None) -> bytes:
    url = os.environ.get("UNDERSCORE_AUDIOGEN_URL")
    if not url:
        raise RuntimeError(
            "set UNDERSCORE_AUDIOGEN_URL to an audio generation endpoint "
            "(see README, Backends)"
        )

    headers = {"Content-Type": "application/json"}
    key = os.environ.get("UNDERSCORE_AUDIOGEN_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"

    body: dict = {"inputs": prompt, "parameters": {"duration": duration}}
    m = _resolve_model(model)
    if m:
        body["model"] = m

    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers=headers
    )
    with urllib.request.urlopen(req, timeout=900) as resp:
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read()

    if "audio" in content_type or "octet-stream" in content_type:
        return raw

    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return raw

    if isinstance(data, dict):
        if "audio" in data:
            import base64
            return base64.b64decode(data["audio"])
        for field in ("url", "output"):
            val = data.get(field)
            if isinstance(val, str) and val.startswith("http"):
                with urllib.request.urlopen(val, timeout=300) as r:
                    return r.read()

    raise RuntimeError(
        "audiogen API returned unrecognized response; "
        "expected audio bytes, {\"audio\": base64}, or {\"url\": ...}"
    )


def _run_cli(prompt: str, duration: float, out_path: Path,
             model: str | None) -> None:
    tmpl = os.environ.get("UNDERSCORE_AUDIOGEN_CLI")
    if not tmpl:
        raise RuntimeError(
            "set UNDERSCORE_AUDIOGEN_CLI to the command that generates audio"
        )
    cmd = shlex.split(tmpl) + [
        "--output", str(out_path),
        "--duration", str(int(duration)),
    ]
    m = _resolve_model(model)
    if m:
        cmd += ["--model", m]

    proc = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, timeout=900
    )
    if proc.returncode != 0:
        raise RuntimeError(f"audiogen CLI failed: {proc.stderr.strip()[:400]}")
    if not out_path.exists():
        raise RuntimeError(
            f"audiogen CLI exited 0 but produced no audio at {out_path}"
        )


def _normalize_wav(path: Path, target_sr: int = SR,
                   target_duration: float | None = None) -> None:
    y, sr = sf.read(path, always_2d=True, dtype="float32")
    if y.shape[1] == 1:
        y = np.repeat(y, 2, axis=1)
    if sr != target_sr:
        import librosa
        y = librosa.resample(y.T, orig_sr=sr, target_sr=target_sr).T
    if target_duration is not None:
        n = int(target_duration * target_sr)
        if len(y) > n:
            y = y[:n]
        elif len(y) < n:
            y = np.vstack([y, np.zeros((n - len(y), y.shape[1]))])
    sf.write(path, y, target_sr, subtype="PCM_24")


def render_audiogen(brief: Brief, out_wav: Path,
                    model: str | None = None) -> dict:
    prompt = build_audio_prompt(brief)
    out_wav.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("UNDERSCORE_AUDIOGEN_CLI"):
        _run_cli(prompt, brief.duration, out_wav, model)
        _normalize_wav(out_wav, target_duration=brief.duration)
    else:
        audio_bytes = _run_api(prompt, brief.duration, model)
        with open(out_wav, "wb") as f:
            f.write(audio_bytes)
        _normalize_wav(out_wav, target_duration=brief.duration)

    return {
        "engine": "audiogen",
        "raw": str(out_wav),
        "stems": {},
        "prompt": prompt,
    }
