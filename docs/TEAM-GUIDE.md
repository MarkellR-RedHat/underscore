# Making music for your videos

This guide gets you from zero to a usable music bed in under 10 minutes.

## Listen first

Before you generate anything, play the showcase track in `examples/showcase-drift-cmaj-240s.mp3`. That was made with the drift collection. There are six collections, each with a different sound:

| Collection | Sound |
|---|---|
| analog | Warm analog pads and soft percussion |
| glass | Bright and clean, bells and piano |
| pulse | Driving electronic, pulsing bass |
| ember | Lo-fi warmth with a gentle swing |
| drift | Cinematic ambient, long pads, sparse pings |
| orbit | Organic and friendly, kalimba, brushed percussion |

## Easiest path (AI audio generation, no Sonic Pi)

This sends your brief to a text-to-music model and gets audio back directly. No Sonic Pi install, no code generation step. The audio goes through the same mastering and quality gate as every other engine.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[video]'

export UNDERSCORE_AUDIOGEN_URL="https://your-audio-endpoint/v1/audio"
export UNDERSCORE_AUDIOGEN_KEY="your-key"

underscore init my-track --duration 60
underscore score --brief my-track.brief.json --engine audiogen --collection glass
```

Your music lands in `out/my-track/`. Grab `my-track.master.wav` and drop it under your video timeline.

For commercial use in Red Hat videos, make sure whatever model you point it at has a license that allows commercial output. Self-hosting a permissively licensed model on OpenShift AI is the cleanest path.

## Quick path (no Sonic Pi, no LLM, no model)

This uses the built-in synth engine. No external dependencies at all. The music is simpler than a full render but perfectly usable for background.

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[video]'

underscore init my-track --duration 60
underscore score --brief my-track.brief.json --engine synth --collection glass
```

Your music lands in `out/my-track/`. Grab `my-track.master.wav` and drop it under your video timeline.

## Full path (real music with Sonic Pi + LLM)

### 1. Install Sonic Pi

Download Sonic Pi 5 from https://sonic-pi.net and install it to `/Applications/`.

### 2. Install ffmpeg

```bash
brew install ffmpeg
```

### 3. Set up your composing backend

Point Underscore at whatever LLM you already use. Pick one:

**Claude Code or any CLI agent:**
```bash
export UNDERSCORE_CLI="your-agent --print --plain"
```

**An API endpoint (vLLM, MaaS, etc):**
```bash
export UNDERSCORE_API_URL="https://your-endpoint/v1"
export UNDERSCORE_API_KEY="your-key"
export UNDERSCORE_MODEL="your-model"
```

**A local model (nothing leaves your machine):**
```bash
export UNDERSCORE_LOCAL="ollama run llama3.1:8b"
```

### 4. Generate

```bash
pip install -e '.[video]'
underscore init my-track --duration 90
underscore score --brief my-track.brief.json --collection drift
```

Full render takes about 90 seconds (real-time playback through Sonic Pi) plus composing time.

## Customizing your brief

After `underscore init`, edit the generated `.brief.json` file. The key fields:

| Field | What it controls |
|---|---|
| `duration` | Length in seconds |
| `tempo` | BPM (leave blank to auto-pick) |
| `key` | Musical key, e.g. "C major", "A minor" |
| `collection` | One of the six collections above |
| `sections` | List of sections with mood and energy level |

### Example: a 60-second explainer video

```json
{
  "duration": 60,
  "tempo": 110,
  "key": "D minor",
  "collection": "glass",
  "sections": [
    {"label": "intro", "bars": 4, "mood": "curious", "energy": 0.3},
    {"label": "main", "bars": 12, "mood": "focused", "energy": 0.6},
    {"label": "outro", "bars": 4, "mood": "resolved", "energy": 0.3}
  ]
}
```

### Example: from a video file

```bash
underscore score --video my-talk.mp4
```

This analyzes the video cuts and speech, builds a brief automatically, and generates music that changes where the picture changes and ducks under the voice.

## What you get

Each run produces a folder with:

- `*.master.wav` — the finished track, broadcast-ready
- `*.ducked.wav` — same track with volume ducked under speech spans (if your brief has them)
- `*.preview.mp3` — small file for quick auditioning
- `*.rb` — the Sonic Pi source code (the code IS the score)
- `markers.csv` — section markers for your timeline
- `manifest.json` — seed, measurements, gate result
- `LICENSE-CC0.txt` — public domain dedication

## Licensing

All music output is CC0 (public domain). No license review needed, no attribution required. Use it in any video, for any purpose.

## Check your setup

```bash
underscore doctor
```

This reports whether Sonic Pi is found, which backends are configured, and what is missing.
