# Underscore in twenty seconds

A brief in, a measured bed out, on the built-in synth engine so it runs anywhere. This document is what Rot replays and records as the demo cast (`docs/demo.cast`).

Write a starter brief for a ninety-second video:

```bash
underscore init demo --duration 90
```

Run the whole pipeline. The synth engine composes nothing, so no model is involved; the render, the mastering chain, the measurements, and the gate are the real ones:

```bash
underscore score --brief demo.brief.json --engine synth
```

Read the gate's verdict back from the manifest:

```bash
python3 -c "import json; m = json.load(open('out/demo/manifest.json')); print('gate_passed', m['gate_passed'], '|', round(m['measurements']['lufs_integrated'], 1), 'LUFS')"
```

The bundle in `out/demo/` holds the mastered WAV, four stems, an MP3 preview, timeline markers, the brief, the manifest, and the CC0 dedication.
