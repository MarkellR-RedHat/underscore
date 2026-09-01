"""analyze: video -> brief, entirely on your machine.

Scene cuts (PySceneDetect), speech spans (energy VAD, always available), and
an optional transcript (faster-whisper) feed a brief. With --llm, the model
assigns moods and hit points from the transcript; without it, a heuristic does.
Nothing about the video leaves the machine unless you choose --llm claude or
anthropic, and even then only the transcript text and cut list are sent.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .brief import Brief, Hit, Section, Span, bpm_for_cuts, sections_from_cuts, MOODS, HIT_KINDS


def _ffmpeg() -> str:
    f = shutil.which("ffmpeg")
    if not f:
        raise RuntimeError("ffmpeg required for video mode (brew install ffmpeg)")
    return f


def video_duration(video: str | Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(video)], capture_output=True, text=True)
    return float(out.stdout.strip())


def extract_audio(video: str | Path, wav: str | Path, sr: int = 16000) -> Path:
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-i", str(video), "-vn",
                    "-ac", "1", "-ar", str(sr), str(wav)], check=True)
    return Path(wav)


def scene_cuts(video: str | Path, threshold: float = 27.0) -> list[float]:
    try:
        from scenedetect import detect, ContentDetector
    except ImportError as e:
        raise RuntimeError("pip install 'underscore-audio[video]' for scene detection") from e
    scenes = detect(str(video), ContentDetector(threshold=threshold))
    return [s[0].get_seconds() for s in scenes[1:]]


def _merge(spans: list[Span], gap: float, min_len: float) -> list[Span]:
    merged: list[Span] = []
    for sp in spans:
        if merged and sp.start - merged[-1].end < gap:
            merged[-1].end = sp.end
        else:
            merged.append(Span(sp.start, sp.end))
    return [Span(round(x.start, 2), round(x.end, 2)) for x in merged if x.end - x.start >= min_len]


def _webrtc_vad(wav: str | Path, aggressiveness: int = 3, min_len: float = 0.3, gap: float = 0.4) -> list[Span]:
    """Real voice activity detection (Google's WebRTC VAD): tells speech from
    room noise, music, and wind, which an energy threshold cannot."""
    import webrtcvad
    import librosa
    y, sr = librosa.load(str(wav), sr=16000, mono=True)
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    vad = webrtcvad.Vad(aggressiveness)
    frame_ms = 30
    n = int(sr * frame_ms / 1000) * 2          # bytes per frame (int16)
    flags = []
    for i in range(0, len(pcm) - n + 1, n):
        flags.append(vad.is_speech(pcm[i:i + n], sr))
    # smooth: a frame is speech if most of its 300 ms neighbourhood is
    win = 10
    sm = np.convolve(np.array(flags, dtype=float), np.ones(win) / win, mode="same") >= 0.7
    spans, start = [], None
    for i, f in enumerate(sm):
        t = i * frame_ms / 1000
        if f and start is None:
            start = t
        elif not f and start is not None:
            spans.append(Span(start, t)); start = None
    if start is not None:
        spans.append(Span(start, len(sm) * frame_ms / 1000))
    return _merge(spans, gap, min_len)


def _energy_vad(wav: str | Path, min_len: float = 0.3, gap: float = 0.4) -> list[Span]:
    """Fallback when webrtcvad is unavailable: loud-enough frames count as speech."""
    import librosa
    y, sr = librosa.load(str(wav), sr=16000, mono=True)
    hop = 160
    rms = librosa.feature.rms(y=y, frame_length=400, hop_length=hop)[0]
    db = librosa.amplitude_to_db(rms + 1e-9, ref=np.max)
    active = db > -32
    spans, start = [], None
    for i, on in enumerate(active):
        t = i * hop / sr
        if on and start is None:
            start = t
        elif not on and start is not None:
            spans.append(Span(start, t)); start = None
    if start is not None:
        spans.append(Span(start, len(y) / sr))
    return _merge(spans, gap, min_len)


def speech_spans(wav: str | Path, min_len: float = 0.3, gap: float = 0.4) -> list[Span]:
    try:
        return _webrtc_vad(wav, min_len=min_len, gap=gap)
    except ImportError:
        return _energy_vad(wav, min_len=min_len, gap=gap)


def transcribe(wav: str | Path, model_size: str = "base") -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return []
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(wav), vad_filter=True)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]


def _llm_brief(brief: Brief, transcript: list[dict], backend: str, model: str | None) -> Brief:
    from .compose import run_llm
    prompt = (
        "You score background music for a developer video. Given the transcript and the "
        "provisional sections below, return ONLY a JSON object with keys 'sections' (list of "
        "{index, mood, energy, notes}) and 'hits' (list of {t, kind}). "
        f"Moods must be from {MOODS}. energy is 0..1. Hit kinds from {HIT_KINDS}. "
        "Place at most 3 hits, only on real moments (a reveal, a result, a turn). "
        "Sections under speech should have energy <= 0.55.\n\n"
        f"duration: {brief.duration}\nsections: {json.dumps([s.__dict__ for s in brief.sections])}\n"
        f"transcript: {json.dumps(transcript)[:12000]}"
    )
    raw = run_llm(prompt, backend, model)
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return brief
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return brief
    for item in data.get("sections", []):
        i = int(item.get("index", -1))
        if 0 <= i < len(brief.sections):
            s = brief.sections[i]
            if item.get("mood") in MOODS:
                s.mood = item["mood"]
            if isinstance(item.get("energy"), (int, float)):
                s.energy = float(min(1.0, max(0.0, item["energy"])))
            s.notes = str(item.get("notes", s.notes))[:120]
    hits = [Hit(float(h["t"]), h["kind"]) for h in data.get("hits", [])
            if h.get("kind") in HIT_KINDS and 0 <= float(h.get("t", -1)) <= brief.duration]
    brief.hits = hits[:3]
    return brief


def brief_from_video(video: str | Path, title: str | None = None,
                     llm: str | None = None, model: str | None = None,
                     with_transcript: bool = True) -> tuple[Brief, dict]:
    video = Path(video)
    title = title or re.sub(r"[^a-z0-9]+", "-", video.stem.lower()).strip("-")
    dur = video_duration(video)
    cuts = scene_cuts(video)
    with tempfile.TemporaryDirectory() as td:
        wav = extract_audio(video, Path(td) / "audio.wav")
        transcript = transcribe(wav) if with_transcript else []
        if transcript:
            # Whisper's segment timestamps are the most reliable speech map we
            # have (it already runs a VAD and ignores room noise). Merge them.
            speech = _merge([Span(t["start"], t["end"]) for t in transcript], gap=0.6, min_len=0.3)
        else:
            speech = speech_spans(wav)
    brief = Brief(title=title, duration=round(dur, 2), bpm=bpm_for_cuts(cuts),
                  sections=sections_from_cuts(cuts, dur), speech=speech)
    brief.quantize_to_bars()
    if llm:
        brief = _llm_brief(brief, transcript, llm, model)
    analysis = {"cuts": cuts, "speech_spans": len(speech), "transcript_segments": len(transcript)}
    return brief, analysis
