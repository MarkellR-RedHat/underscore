# Underscore

Code-generated, measured, CC0 background music for developer videos.

Underscore turns a short brief (or a video) into a finished music bed: it asks
your own Claude Code account to write Sonic Pi code, renders it, masters it to
broadcast loudness, measures the result, and refuses to ship anything out of
spec. Every track exports with stems, a speech-ducked mix, timeline markers,
and the source code that made it. The output is public domain (CC0).

It runs on your machine and your own accounts. Nothing is hosted.

## Two modes, one generator

- **Brief mode.** You describe what you need: duration, mood, energy curve,
  hit points. Nothing leaves your machine except the brief text you wrote.
- **Video mode.** Point it at a video. Scene cuts, transcript, and speech map
  are extracted locally, a brief is derived, and the music changes where the
  picture changes and ducks under the voice. For source material you cannot
  share, use `--llm ollama` (fully local) or write the brief yourself.

## Pipeline

```
analyze (video -> brief)   [optional, local: PySceneDetect + faster-whisper + VAD]
compose (brief -> Sonic Pi code)   [Claude Code CLI | Anthropic API | Ollama]
render  (code -> WAV 48k/24)       [Sonic Pi headless | built-in synth fallback]
master  (WAV -> -14 LUFS, fades)   [pedalboard + pyloudnorm, optional matchering]
measure (gate: loudness, peak, energy vs brief)   [librosa + pyloudnorm]
export  (bundle: master, ducked, stems, mp3, markers, source, manifest)
```

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[video]'
underscore init my-video            # writes examples/brief.json to edit
underscore score --brief brief.json # full pipeline
underscore score --video talk.mp4   # video mode
```

Step zero on a new machine: `scripts/check-render.sh` tells you whether Sonic
Pi headless rendering works. If it does not yet, the built-in synth engine
(`--engine synth`) lets you exercise the entire pipeline today.

## Status

Day one. Built in the open at Rawlslab.
