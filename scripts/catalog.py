#!/usr/bin/env python3
"""Generate the Underscore catalog: a matrix of briefs -> finished CC0 beds.

    .venv/bin/python scripts/catalog.py --out catalog --limit 24
    .venv/bin/python scripts/catalog.py --dry-run          # just write the briefs

Each bed gets a deterministic seed, so any track can be regenerated exactly.
Failures (gate or render) are logged and skipped; the batch keeps going. If
every bed in a run fails, the script exits non-zero so a broken environment
(no Sonic Pi, no backend) cannot look like a successful run.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from underscore.brief import Brief, Section, Hit  # noqa: E402
from underscore.collections import COLLECTIONS, get as get_collection  # noqa: E402

# The matrix: what a developer-video editor actually reaches for.
PROFILES = {
    # name: (style, mode, bpm, arc as [(mood, energy, share), ...])
    "explainer":   ("warm electronic, analog pads, soft percussion", "minor", 92,
                    [("curious", 0.5, .12), ("focused", 0.55, .58), ("lift", 0.75, .2), ("resolve", 0.3, .1)]),
    "launch":      ("bright electronic, driving, clean synths", "major", 112,
                    [("focused", 0.6, .15), ("lift", 0.8, .55), ("triumphant", 0.9, .2), ("resolve", 0.4, .1)]),
    "demo":        ("steady lo-fi electronic, rounded bass, minimal", "minor", 88,
                    [("focused", 0.5, .2), ("focused", 0.55, .6), ("lift", 0.65, .1), ("resolve", 0.3, .1)]),
    "deep-dive":   ("cinematic ambient electronic, slow build, wide pads", "minor", 78,
                    [("calm", 0.4, .2), ("serious", 0.5, .5), ("lift", 0.7, .2), ("resolve", 0.3, .1)]),
    "playful":     ("plucky electronic, syncopated, light and upbeat", "major", 118,
                    [("playful", 0.6, .2), ("playful", 0.7, .55), ("lift", 0.8, .15), ("resolve", 0.4, .1)]),
    "keynote":     ("wide cinematic synths, big chords, confident", "major", 100,
                    [("warm", 0.5, .15), ("lift", 0.7, .45), ("triumphant", 0.9, .3), ("resolve", 0.4, .1)]),
}
KEYS = {"minor": ["D", "A", "E", "G"], "major": ["C", "G", "F", "D"]}
DURATIONS = [60.0, 90.0, 120.0]


def make_brief(profile: str, duration: float, key: str, seed: int, collection: str = "analog") -> Brief:
    style, mode, bpm, arc = PROFILES[profile]
    coll = get_collection(collection)
    bpm = bpm + coll.tempo_shift
    style = f"{coll.tagline}; {style}"
    sections, t = [], 0.0
    for mood, energy, share in arc:
        end = round(t + duration * share, 3)
        sections.append(Section(round(t, 3), end, mood, energy))
        t = end
    sections[-1].end = duration
    hits = [Hit(round(sections[2].start, 3), "riser"), Hit(round(sections[-1].start, 3), "soft-hit")]
    b = Brief(title=f"{profile}-{key.lower()}{mode[:3]}-{int(duration)}s-{seed}", duration=duration,
              bpm=bpm, key=key, mode=mode, style=style, seed=seed, sections=sections, hits=hits,
              collection=collection)
    return b.quantize_to_bars()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="catalog")
    ap.add_argument("--limit", type=int, default=24)
    ap.add_argument("--engine", default="sonicpi")
    ap.add_argument("--llm", default="cli")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collection", default="analog", choices=list(COLLECTIONS))
    a = ap.parse_args()

    # each collection lives in its own folder and its own seed range
    seed_base = 100 + 1000 * list(COLLECTIONS).index(a.collection)
    out = Path(a.out) / a.collection; (out / "briefs").mkdir(parents=True, exist_ok=True)
    combos = list(product(PROFILES.keys(), DURATIONS))
    plan = []
    for i, (profile, dur) in enumerate(combos):
        mode = PROFILES[profile][1]
        key = KEYS[mode][i % len(KEYS[mode])]
        plan.append(make_brief(profile, dur, key, seed=seed_base + i, collection=a.collection))
    plan = plan[: a.limit]
    log = out / "catalog-log.jsonl"
    print(f"{len(plan)} beds planned -> {out}  [collection {a.collection}]", file=sys.stderr)
    shipped = failed = 0
    for b in plan:
        bp = out / "briefs" / f"{b.title}.json"
        b.save(bp)
        if a.dry_run:
            continue
        dest = out / b.title
        mf = dest / "manifest.json"
        if mf.exists() and json.loads(mf.read_text()).get("gate_passed"):
            print(f"skip {b.title} (shipped)", file=sys.stderr); shipped += 1; continue
        t0 = time.time()
        r = subprocess.run([sys.executable, "-m", "underscore.cli", "score", "--brief", str(bp),
                            "--engine", a.engine, "--llm", a.llm, "-o", str(dest)],
                           capture_output=True, text=True)
        ok = r.returncode == 0
        stages, gate_reasons = {}, []
        mfp = dest / "manifest.json"
        if mfp.exists():
            try:
                m = json.loads(mfp.read_text())
                stages = m.get("stage_seconds", {})
                gate_reasons = m.get("gate_reasons", [])
            except json.JSONDecodeError:
                pass
        rec = {"title": b.title, "ok": ok, "seconds": round(time.time() - t0, 1), "stages": stages,
               "gate_reasons": gate_reasons, "tail": r.stderr.strip().splitlines()[-3:]}
        with log.open("a") as f:
            f.write(json.dumps(rec) + "\n")
        shipped += ok; failed += not ok
        detail = ", ".join(f"{k} {v}s" for k, v in stages.items() if k in ("compose", "recompose", "render"))
        why = f"  [{'; '.join(gate_reasons)}]" if (not ok and gate_reasons) else ""
        print(f"{'ok  ' if ok else 'FAIL'} {b.title}  ({rec['seconds']}s; {detail}){why}", file=sys.stderr)
    if not a.dry_run and plan and shipped == 0:
        print(f"every bed failed ({failed} of {len(plan)}); see {log}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
