# Changelog

## 0.1.0 (not yet released)

First release. The pipeline: brief or video in; composed, rendered, mastered, measured, and gated music bed out, dedicated to the public domain under CC0.

- Six stages (`analyze`, `compose`, `render`, `master`, `measure`, export), chained by `underscore score`.
- Two render engines: Sonic Pi 5 headless (macOS) and a built-in synth engine that runs anywhere.
- Neutral composing seam: backends `cli | api | local`, configured with `UNDERSCORE_CLI`, `UNDERSCORE_API_URL` and `UNDERSCORE_API_KEY`, `UNDERSCORE_LOCAL`, and `UNDERSCORE_MODEL`. Nothing bundled, no default model.
- Six collections (analog, glass, pulse, ember, drift, orbit) with deterministic per-seed instrument assignment.
- A loudness, true-peak, duration, silence, and energy-curve gate; beds that fail are written for inspection but marked not shippable.
- Catalog tooling: `scripts/catalog.py` (exits non-zero when every bed fails, logs gate reasons), `scripts/build_catalog_page.py`, `scripts/build_catalog_index.py` (machine-readable `catalog.json`).
- Bundles are reproducible: brief, seed, program, measurements, and license travel with every track; manifest file entries are basenames.
- The CC0 dedication is inside every audio file: a Broadcast Wave `bext` chunk in each WAV and ID3 tags in the MP3, naming the bed, the license URL, and the sha256 of `manifest.json`.
- The brief schema and the gate report are the family's shared ones, vendored from rawlslab-core; a bad brief reports every problem at once, and each bundle carries `gates.json`.
- `underscore compose` without a configured backend, and `score --engine sonicpi` without one, print one line and exit 2.
- `rot.yaml` and a Rot workflow: the README and `docs/DEMO.md` replay in a clean container on every push; `docs/demo.cast` is the recorded twenty-second demo.
