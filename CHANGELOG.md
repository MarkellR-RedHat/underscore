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
