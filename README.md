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
- **Video mode.** Point it at a video. Scene cuts, transcript (faster-whisper),
  and speech map (Whisper timestamps, WebRTC VAD as fallback) are extracted locally, a brief is derived, and the music changes where the
  picture changes and ducks under the voice. For source material you cannot
  share, use `--llm ollama` (fully local) or write the brief yourself.

## Pipeline

```
analyze (video -> brief)   [optional, local: PySceneDetect + faster-whisper + VAD]
compose (brief -> Sonic Pi code)   [Claude Code CLI | Anthropic API | Ollama]
render  (code -> WAV 48k/24)       [Sonic Pi 5 headless recorder | built-in synth fallback]
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

## How the Sonic Pi render works (no GUI)

Sonic Pi 5 ships a headless boot library. `vendor/underscore-record.rb` builds
on it: boot the daemon and engine, start recording through the spider (the
same path as the GUI's record button), run the program for the brief's
duration, save the WAV, shut down. Rendering is realtime: a 90 s bed takes
about 90 s plus a few seconds of boot. The harness holds the run open past the
recording window because the engine pauses itself once every run completes.

Re-render a take you like without asking the model again:

```bash
underscore score --brief brief.json --program out/track/track.rb --engine sonicpi
```

## Status

Day one. Built in the open at Rawlslab.

## The catalog

`scripts/catalog.py` renders a matrix of beds: six profiles (explainer, launch,
demo, deep-dive, playful, keynote) at 60, 90, and 120 seconds, rotating keys,
deterministic seeds. Every bed ships as a full bundle. Failures are logged to
`catalog/catalog-log.jsonl` and skipped; rerunning resumes.

```bash
.venv/bin/python scripts/catalog.py --out catalog --limit 18
```

Renders are audible while they run (the record tap is pre-device, so system
volume does not change what gets written).

## Tests

```bash
.venv/bin/python -m pytest -q tests
```

The synth engine makes the whole pipeline testable without Sonic Pi.

## Catalog page

```bash
.venv/bin/python scripts/build_catalog_page.py --catalog catalog   # -> catalog/index.html
```

A playable index of every bed that passed the gate, with measurements and
downloads. Beds the gate withheld are counted but not listed.
