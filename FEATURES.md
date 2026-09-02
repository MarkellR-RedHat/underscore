# Underscore feature audit

Every feature named in the README, docs/POLICY.md, CHANGELOG.md, the roadmap, the launch task list and gap register, the program decisions, and the owner handoffs, with its status and the command that proves it. Audited September 2, 2026 at master 4b996a3 (plus the catalog index change at caf0509); proof runs used the synth engine and this Mac's Sonic Pi 5, no model calls, no spend. Paths under `proof/` are the audit's scratch outputs; the durable evidence is the release, the test suite, and the catalog.

Status words: **shipped** (works, proven by the command), **partial** (exists but with a stated hole), **missing** (named somewhere, not built).

## Pipeline

| Feature | Status | Proves it | Produces |
|---|---|---|---|
| Starter brief (`underscore init`) | shipped | `underscore init my-video --duration 90` | `my-video.brief.json` |
| Full pipeline from a brief (`underscore score --brief`) | shipped | `underscore score --brief examples/brief.example.json --engine synth -o out/demo` | `out/demo/` bundle, 9 files, gate PASS at -14.0 LUFS |
| Built-in synth engine (no model, no Sonic Pi) | shipped | same command, `--engine synth`; `python -m pytest -q tests/test_pipeline_synth.py` | `<title>.master.wav` plus four stems |
| Sonic Pi 5 headless render | shipped | `underscore score --brief examples/reproduce/brief.json --program examples/reproduce/deep-dive-amin-60s-1109.rb --engine sonicpi` (this Mac, about 90 s) | `out/deep-dive-amin-60s-1109/` with `engine: sonicpi` in manifest.json; the 108 catalog beds are all `engine: sonicpi` |
| Compose with a language model through the `cli` seam | shipped | `export UNDERSCORE_CLI="<agent command>"; underscore score --brief my-video.brief.json` (needs a backend; not run in this audit) | the 108 released beds were composed this way; each ships its `.rb` |
| `api` seam (chat-completions endpoint) | partial | `UNDERSCORE_API_URL=... underscore compose brief.json --llm api`; selection is tested by `pytest -k test_14` | code path in `compose.py`; no recorded run against a real endpoint |
| `local` seam (local model runner) | shipped | `UNDERSCORE_LOCAL="<agent command>" underscore score --brief examples/brief.example.json --llm local --engine sonicpi` (recorded September 2 against the command-line agent on this Mac: compose 85.1 s, render 112.9 s, gate PASS) | `~/launch/underscore-release-prep/local-seam-2026-09-02/` (manifest with `compose_backend: local`, brief, program, README, preview) |
| Program validation and the fixed outer program (tempo, seed, section sequencing, hit threads) | shipped | `python -m pytest -q tests/test_compose.py` | 4 tests |
| One recompose after a Sonic Pi runtime error | shipped | catalog run record: `catalog/*/catalog-log.jsonl` (one recompose logged in the September 1 run) | log line |
| Compose without a configured backend refuses | shipped | `underscore compose brief.json` with no `UNDERSCORE_CLI`; `python -m pytest -q tests/test_cli_exits.py` | one line on stderr (`compose: set UNDERSCORE_CLI ...`), exit 2; same for `score --engine sonicpi` |
| Mastering chain, two-pass loudness normalize, true-peak limiter, fades | shipped | any `score` run: the `measure:` line reports LUFS, dBTP, LRA | `<title>.master.wav` at target LUFS, peak at or below -1 dBTP |
| Reference-matched mastering (matchering) | shipped | `underscore score --brief examples/brief.example.json --engine synth --reference <some.wav> -o out/ref` | manifest.json `master.reference_matched: true`; temp cleanup tested by `pytest -k reference_match` |
| Speech ducking when the brief has speech spans | shipped | add `"speech": [{"start": 5, "end": 20}]` to a brief, then `score --engine synth` | `<title>.ducked.wav`, README.txt names it; `pytest -k ducked` |
| Gate: loudness, true peak, duration, silent sections, energy curve | shipped | any `score` run (`-> PASS`); `python -m pytest -q tests/test_gate_edges.py` | manifest.json `gate_passed`, `gate_reasons` |
| Measurements: LUFS, true peak, LRA, spectral centroid, per-section RMS, energy correlation | shipped | `underscore measure out/demo/<title>.master.wav --brief out/demo/brief.json` | JSON on stdout; the same block in manifest.json |
| Export bundle: master, preview MP3, `.rb`, markers CSV and EDL, brief, manifest, CC0 text, README.txt | shipped | `ls out/demo` | 9 files (11 with stems, 10 with a ducked file) |
| Stems from the synth engine | shipped | `score --engine synth` | `<title>.stem-{pads,bass,drums,motif}.wav` |
| Stems from the Sonic Pi engine (one solo pass per layer) | in progress on `next` | `src/underscore/stems.py` (layers from the seed's picks, a prepended filter on Sonic Pi's sound module, alignment to the mix by cross-correlation); `python -m pytest -q tests/test_stems.py` | a fully muted pass renders to silence (proven September 2); solo passes under test; the first collection with stems is the milestone |
| Loop-safe export (`--loop`: decay trim, seam crossfade, seam check in the gate) | shipped | `underscore score --brief examples/brief.example.json --engine synth --loop -o out/loop`; `python -m pytest -q tests/test_loop.py` | manifest.json `loop: true`, bed half a second shorter than the brief |
| Loop-safe variants of the 108 catalog beds | missing | decision 4: nice-to-have; a re-render is about 7 hours of Sonic Pi wall time plus compose spend | none; default is no re-render before freeze |
| `--ship-anyway` (write a failed bed as shippable) | shipped | `python -m pytest -q tests/test_cli_exits.py -k ship` | without it a failed gate exits 2 with the bundle written; with it the bundle stays and exit is 0, `gate_passed: false` recorded |
| Individual stage commands: `analyze`, `compose`, `render`, `master`, `measure` | shipped | `underscore render --brief b.json --engine synth -o raw.wav`; `underscore master raw.wav --brief b.json -o outdir/`; `underscore measure master.wav --brief b.json` | raw WAV; mastered plus ducked WAV in the directory (`pytest -k test_13`); measurement JSON |
| Reuse a program (`--program`, skip compose) | shipped | the reproduce command above | the same bed again |

## Video mode

| Feature | Status | Proves it | Produces |
|---|---|---|---|
| Video to brief: scene cuts, speech map, tempo fit, sections | shipped | `underscore score --video talk.mp4 --offline-brief --engine synth -o out/video` (the audit used a generated 24 s clip with two cuts) | `analyze: 2 cuts, 0 speech spans (vad), brief by heuristic`; `out/video/brief.json` |
| Speech map from the transcript with VAD-kept pauses; VAD fallback | shipped | `python -m pytest -q tests/test_e2e_gaps.py -k test_12` | 3 tests; manifest `brief.speech_source` |
| `--offline-brief` (nothing leaves the machine) | shipped | the command above | manifest.json `brief.source: heuristic` |
| Model-derived brief from a video (`--llm`) | shipped | `underscore score --video talk.mp4 --llm cli` with `UNDERSCORE_CLI` set; backend selection tested by `test_14`; the September 1 end-to-end rehearsal ran it for real (`~/launch/e2e/REPORT.md`, gaps 12 to 15) | brief with model-assigned moods and hits |
| Manifest provenance: brief source, analyze backend and model, analyze seconds, compose backend | shipped | `python -m pytest -q tests/test_e2e_gaps.py -k test_15`; any video run's manifest.json | `brief` and `compose_backend` keys |
| Transcript model download on first run is documented | shipped | README Requirements: "Video mode downloads the faster-whisper base transcription model (about 75 MB) ... on its first run" | the audit's first pass missed the line |

## Machine, configuration, platform

| Feature | Status | Proves it | Produces |
|---|---|---|---|
| `underscore doctor` (Python, ffmpeg, ffprobe, pedalboard, Sonic Pi, recorder, backends, disk) | shipped | `underscore doctor` | check list; on this Mac everything but the unconfigured cli backend is a tick |
| Configurable Sonic Pi path (`UNDERSCORE_SONIC_PI_APP`, `--sonic-pi-app`) | shipped | `UNDERSCORE_SONIC_PI_APP=/nonexistent underscore doctor` | the Sonic Pi line turns to a cross naming that path |
| Linux headless Sonic Pi render | partial | README states it as unverified; the override exists, the Sonic Pi 5 Linux layout is unchecked | none |
| Linux install path for the synth engine (`libatomic1`, `ffmpeg`) | shipped | `docker run --rm python:3.12-slim` install of `rawlslab-underscore==0.1.0rc1` from TestPyPI, then `underscore score --engine synth` (September 2, gate PASS) | bundle in the container |
| Neutral backend configuration (`UNDERSCORE_CLI`, `UNDERSCORE_API_URL`, `UNDERSCORE_API_KEY`, `UNDERSCORE_LOCAL`, `UNDERSCORE_MODEL`, `{model}` substitution) | shipped | README Backends table; `pytest -k test_14` | no vendor or model name anywhere in the tree (flip check, September 2) |

## Catalog and release

| Feature | Status | Proves it | Produces |
|---|---|---|---|
| Six collections with deterministic per-seed instrument assignment | shipped | `python -m pytest -q tests/test_collections.py` | 3 tests; 18 beds per collection in the release |
| Catalog batch (`scripts/catalog.py`): profile by duration matrix, fixed seeds, resumable, per-collection log, non-zero exit when every bed fails | shipped | `.venv/bin/python scripts/catalog.py --out catalog-demo --collection glass --limit 2 --engine synth`; with `UNDERSCORE_SONIC_PI_APP=/nonexistent --engine sonicpi` it reports "every bed failed" | `catalog-demo/glass/<bed>/` bundles, `catalog-log.jsonl` |
| Catalog page (`scripts/build_catalog_page.py`) | shipped | `.venv/bin/python scripts/build_catalog_page.py --catalog catalog-demo` | `catalog-demo/index.html` |
| Catalog index in the family bed catalog contract (`version`, `file`, `mood`, `energy`, `loop_safe`, `license`, `sha256`, plus the full record and `recommended_for` per decision 23; `--flat` for releases) | shipped | `.venv/bin/python scripts/build_catalog_index.py --catalog catalog-demo`; `python -m pytest -q tests/test_catalog_index.py`; Backdrop's `--bed auto` check passed against the release (September 2) | `catalog.json` |
| The 108-bed catalog, all gate-passing, all Sonic Pi | shipped | `gh release view catalog-2026.09` | https://github.com/MarkellRawls/underscore/releases/tag/catalog-2026.09 |
| Release layout: six collection zips, previews zip, catalog.json, checksums, every WAV, `.rb`, and preview MP3 as an individual asset | shipped | `gh release view catalog-2026.09 --json assets --jq '.assets|length'` (334) | `release-SHA256SUMS.txt` (332 lines) covers every file; all audio re-uploaded tagged on September 2 |
| CC0 dedication in every bundle and at the catalog root | shipped | `cat out/demo/LICENSE-CC0.txt`; `CATALOG-LICENSE.md`; `docs/POLICY.md` records that the 24 Sonic Pi samples used are CC0 | text files |
| CC0 dedication embedded in the audio file itself (bext in every WAV, ID3 in the MP3; bed id, license URL, sha256 of manifest.json, measured loudness) | shipped | any `score` run, then `python -c "from underscore.dedication import read_bext; print(read_bext('out/demo/<title>.master.wav'))"`; `python -m pytest -q tests/test_dedication.py`; `ffprobe -show_entries format_tags out/demo/<title>.preview.mp3` | tags inside the files; all 108 release files re-tagged September 2 (`scripts/tag_catalog.py`) |
| Reproducibility example checked in (`examples/reproduce/`) | partial | `underscore score --brief examples/reproduce/brief.json --program examples/reproduce/deep-dive-amin-60s-1109.rb --engine sonicpi` (run on this Mac, September 2, about 90 s) | the same music, gate PASS, measurements within tolerance of the released bed (LUFS -14.033 vs -14.034, LRA 1.98 vs 2.06 LU, energy correlation 0.878 vs 0.877, centroid 832 vs 830 Hz) but not the same bytes (true peak -1.50 vs -1.77 dBTP; the render is a realtime recording). The README said "regenerates it exactly"; reworded to what is true |
| Site page: players, energy curves, filters, per-bed WAV and source links to the release, catalog CSV | shipped | https://rawlslab.ai/underscore (behind Access until October 5); `~/rawlslab-site/scripts/sync-underscore.py --release-tag catalog-2026.09` | `underscore/beds-data.js` with `release_tag: catalog-2026.09` (site master 4cd602e) |
| Site preview MP3s served from the release, zip buttons pointing at the release zips | shipped on the launch-day branch | site `launch-day` branch (coordinator) | goes live with the branch |

## Packaging, CI, checks

| Feature | Status | Proves it | Produces |
|---|---|---|---|
| Package `rawlslab-underscore`, console script `underscore`, assets inside the package | shipped | `python -m build`; wheel-smoke job in ci.yml | wheel that runs `underscore init` and `score --engine synth` from `/tmp` |
| CI: tests on ubuntu 3.10 and 3.12 on every push, macOS on `0.*` tags, manual, and weekly (decision 14); synth pipeline; wheel smoke | shipped | `gh run list --workflow ci` (run 33575424830 on tag 0.1.0-rc.1 includes the macOS job) | green runs |
| Trusted publishing: rc tags to TestPyPI, finals to PyPI | shipped | `gh run view 33575424825` (tag 0.1.0-rc.1, testpypi job success) | https://test.pypi.org/project/rawlslab-underscore/0.1.0rc1/ |
| Clean-venv install from TestPyPI on macOS and Linux | shipped | `pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rawlslab-underscore==0.1.0rc1` then `underscore score --engine synth` | gate PASS, manifest `underscore_version: 0.1.0rc1` |
| Test suite | shipped | `.venv/bin/python -m pytest -q tests` | 27 passed |
| README runs under Rot in a clean container | shipped | Rot referee run by the Rot lane on 4b996a3 (September 2): FRESH, 4 blocks work, 5 skipped by directive | `.rot/reports` on the Rot side |
| Rot self-check configured in this repo (`rot.yaml`, workflow on push, PR, weekly) | shipped | `rot run --strict` from the repo root (Docker); `.github/workflows/rot.yml` | `.rot/reports/*.md` (README and docs/DEMO.md FRESH), badges, expectations committed |
| README demo capture | shipped | `assets/demo.png` (700 by 193, from a real synth run at cb27cf7; the CLI output format is unchanged since) | image at the top of the README |
| 20-second demo cast | shipped | `rot run --strict --record casts/` (Rot replays `docs/DEMO.md` and records the run) | `docs/demo.cast`, asciicast v2, 16 s, 5 KB, deterministic |
| Repo metadata (description, homepage, topics), issue and PR templates, SECURITY.md, CHANGELOG.md | shipped | `gh repo view MarkellRawls/underscore`; flip check hygiene rules pass | repo |
| Vendor-free tree and history | partial | flip check September 2: tree clean; history carries pre-4363535 vendor names and INTERNAL.md | orphan rebuild in RC week (October 26 to 30) |
| Shared core adoption (`brief`, `gates` from rawlslab-core) | shipped | `python3 ~/core/scripts/vendor.py ~/underscore --dest src/underscore/_vendor --modules brief gates --check`; `python -m pytest -q tests/test_core_adoption.py` | `Brief` subclasses the vendored `MusicBrief`; every bundle carries `gates.json`; a bad brief reports every problem at once |
| Backdrop `--bed auto` integration through the catalog contract | shipped | Backdrop lane's check against the release: PASS, hash verifies | `compose/manifest.json` on the Backdrop side names the bed |

## Docs behind code

- INTERNAL.md still lists Rot as "planned, after Backdrop" (gap register item 6). The file is deleted in RC week; not corrected in place.

## Audit note: the reproduce example

Reproduction is program-exact and measurement-exact, not byte-exact: Sonic Pi records in realtime, so two renders of the same program differ at the sample level and the limiter lands at a slightly different peak. Every gate measurement matches to the rounding shown in the table. Byte-exact regeneration would need offline (non-realtime) rendering, which Sonic Pi 5 does not offer; it is not on the roadmap.
