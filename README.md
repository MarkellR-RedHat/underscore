# Underscore

Underscore makes background music for developer videos. You give it a short brief, or a video, and it returns a finished music bed: mastered to broadcast loudness, measured against what you asked for, and dedicated to the public domain. Every track ships with the source code that produced it, so anyone can regenerate or change it.

It runs on your own machine with your own accounts. Nothing is hosted. The audio never leaves your computer, and in brief mode nothing else does either.

## Why it exists

Developer relations and content teams publish a steady stream of videos, and most of them need music under the voice. Commercial stock libraries come with license terms that many companies will not accept for published material, and reviewing each track's terms takes time nobody has. The usual result is silence, or the same three approved tracks in every video.

Underscore takes a different route. The music is written as code by a language model working from your brief, rendered on your hardware by Sonic Pi, mastered and checked by the pipeline, and released under CC0. A track made this way has no license terms for anyone to review. You can use it, your employer can use it, and so can anyone else.

## What you get

Each bed is one folder:

| File | Purpose |
|---|---|
| `title.master.wav` | The finished bed, 48 kHz, 24-bit, -14 LUFS, with fades. |
| `title.ducked.wav` | The same bed with volume automation baked in under the speech spans from the brief. Drop it under a voice track and it already sits in the right place. |
| `title.stem-*.wav` | Separate instrument layers, when the engine produces them. |
| `title.preview.mp3` | A small file for auditioning. |
| `title.rb` | The Sonic Pi program. The code is the score. |
| `markers.csv`, `markers.edl` | Section and hit markers for the editing timeline. |
| `brief.json` | Exactly what the generator was asked for. |
| `manifest.json` | Seed, engine, every measurement, and the gate result. |
| `LICENSE-CC0.txt` | The public domain dedication. |

## How it works

The pipeline has six stages. Each one is a command, and `underscore score` runs them all.

1. **Analyze** (video mode only). Scene cuts are detected with PySceneDetect. Speech is located with faster-whisper, and its timestamps become the speech map; WebRTC VAD is the fallback when there is no transcript. A tempo is chosen so that bar lines land near the scene cuts. The result is a brief. This stage runs entirely on your machine.
2. **Compose.** The brief is turned into a prompt, and a language model writes Sonic Pi code: one function per section, one per hit, all in key, built from an allowed set of synths and samples. The default backend is the Claude Code command line tool, so it uses a subscription you already have. The Anthropic API and Ollama are also supported. The code is validated (required functions present, no forbidden constructs, no helper names that collide with Sonic Pi's own API) and wrapped in a harness that sets tempo and seed and sequences the sections to an exact number of bars.
3. **Render.** Sonic Pi 5 plays the program headlessly and records it. Rendering happens in real time: a 90 second bed takes about 90 seconds plus boot. A built-in synth engine can stand in when Sonic Pi is not available, so the rest of the pipeline stays testable. If Sonic Pi reports a runtime error, the errors are handed back to the model and the program is composed again once before the run is declared a failure.
4. **Master.** A gentle chain (high-pass, compression, two shelves, light reverb), loudness normalization to the brief's target, a transparent peak limiter with true-peak headroom, and fades. With a reference track and `matchering` installed, the tonal balance is matched to the reference.
5. **Measure.** Integrated loudness, true peak, loudness range, spectral centroid, and per-section onset density are computed. The gate refuses a bed whose loudness misses the target by more than 1 LU, whose true peak exceeds -1 dBTP, whose length is wrong, whose sections are silent, or whose energy curve does not follow the brief.
6. **Export.** The bundle above is written. Beds that fail the gate are still written for inspection, but the manifest marks them as not shippable and the catalog page leaves them out.

## Two ways to start

**Brief mode.** You describe the music: duration, tempo, key, sections with a mood and an energy level, optional hit points, optional speech spans. `underscore init` writes a starter brief to edit. Nothing about your video is involved.

**Video mode.** You point Underscore at a video. It derives the brief from the cuts and the speech, so the music changes where the picture changes and gets out of the way when someone is talking. With a language model backend, the transcript is used to assign moods and place hits. With `--offline-brief`, a heuristic does that instead and no model is called.

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[video]'

underscore init my-video --duration 90        # writes my-video.brief.json
underscore score --brief my-video.brief.json  # full pipeline, bundle in out/my-video
underscore score --video talk.mp4             # video mode
underscore score --video talk.mp4 --offline-brief --llm ollama   # nothing leaves the machine
```

Individual stages are available as `analyze`, `compose`, `render`, `master`, and `measure`. `scripts/check-render.sh` reports whether this machine can render with Sonic Pi.

## Requirements

- macOS with Sonic Pi 5 installed (`brew install --cask sonic-pi`). Linux should work with the paths in `render.py` adjusted; this has not been tested yet.
- Python 3.10 or newer.
- `ffmpeg` for MP3 previews and video mode (`brew install ffmpeg`).
- A composing backend: the Claude Code command line tool, an Anthropic API key, or Ollama with a local model.

## The Sonic Pi render, in detail

Sonic Pi 5 ships a headless boot library. `vendor/underscore-record.rb` builds on it: it starts the daemon and audio engine, begins recording through the spider (the same path the application's record button uses), runs the program for the brief's duration, saves the WAV, and shuts down. Two details matter. The engine pauses itself as soon as every run has completed, so the harness keeps the run alive for several seconds past the end of the music. The first note can arrive a few seconds after recording starts on a fresh boot, so the recording window is longer than the brief and the pre-roll is trimmed afterwards.

Renders are audible while they run. The record tap sits before the output device, so the system volume does not change what is written.

## Reproducibility

Every bed records its seed, its brief, and its program. Re-rendering a program gives the same music:

```bash
underscore score --brief brief.json --program out/track/track.rb --engine sonicpi
```

Composing again from the same brief will produce different code, because the model is not deterministic. Keep the `.rb` file if you want the track back exactly.

## Data flow

| Stage | Brief mode | Video mode, cloud model | Video mode, `--offline-brief` or Ollama |
|---|---|---|---|
| Analyze | not used | cuts, transcript, speech map computed locally | same |
| Compose | brief text is sent to the model | brief plus transcript text and cut times are sent | nothing is sent |
| Render, master, measure, export | local | local | local |

Audio, video frames, and finished tracks never leave the machine in any mode. If the source footage is confidential, use the third column.

## Using it at work

Most people who want this tool want it for company videos. `docs/POLICY.md` walks through the questions that come up: who owns the music, why the output is CC0, what a company actually receives, how the data is handled, and the practical rules that keep personal and company work separate. The short version: compose on your own time and hardware if you want to own the catalog, release it under CC0, and your employer uses it the way it would use any public domain library. Read your own company's policy; this project is not legal advice.

## Collections

A collection is a sonic world: its instruments, drum kit, effects, harmonic flavor, and arrangement signature. The same brief rendered in two collections sounds like two different libraries. Six ship today:

| Collection | Sound |
|---|---|
| analog | Warm analog pads and soft percussion. |
| glass | Bright, clean, and spacious; bells and piano with air between notes. |
| pulse | Driving electronic; pulsing bass, four on the floor when the energy allows. |
| ember | Lo-fi warmth with a gentle swing and a little vinyl texture. |
| drift | Cinematic ambient; long pads, sub bass, sparse pings. |
| orbit | Organic and friendly; kalimba, tonewheel organ, brushed percussion. |

Within a collection, each bed receives a deterministic instrument assignment from its seed, so eighteen beds in one world still differ from one another. Set `"collection"` in the brief, or pass `--collection` to the catalog script. Collections are defined in `src/underscore/collections.py`; adding one is a matter of listing its instruments and writing its sound in a paragraph.

## The catalog

`scripts/catalog.py` renders a matrix of beds (six profiles at 60, 90, and 120 seconds, rotating keys, fixed seeds) and `scripts/build_catalog_page.py` turns the results into a browsable page with players, measurements, and downloads. Failed beds are logged and retried on the next run.

```bash
.venv/bin/python scripts/catalog.py --out catalog --collection glass --limit 18
.venv/bin/python scripts/build_catalog_page.py --catalog catalog   # groups by collection
```

## Project layout

```
src/underscore/
  brief.py     the brief schema, validation, bar quantization, derivation helpers
  analyze.py   video -> brief (cuts, transcript, speech map)
  compose.py   brief -> Sonic Pi program (prompt, backends, validator, harness)
  render.py    program -> WAV (Sonic Pi 5 headless, synth fallback)
  master.py    mastering chain, loudness, limiter, fades, ducking
  measure.py   measurements and the gate
  export.py    the bundle
  cli.py       the command line
prompts/compose.md          the composing spec the model follows
vendor/underscore-record.rb the headless recorder
scripts/                    catalog batch, catalog page, render check
tests/                      unit tests; the synth engine keeps them independent of Sonic Pi
```

## Tests

```bash
.venv/bin/python -m pytest -q tests
```

## Roadmap

- Stems from the Sonic Pi engine (one solo pass per layer).
- Linux paths for the Sonic Pi render.
- A published catalog page.

## License

Code: MIT. Music produced by the pipeline: CC0 1.0 (see `CATALOG-LICENSE.md`).
