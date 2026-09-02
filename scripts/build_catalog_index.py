#!/usr/bin/env python3
"""Build catalog.json: a machine-readable index of every shipped bed.

    .venv/bin/python scripts/build_catalog_index.py --catalog catalog
    .venv/bin/python scripts/build_catalog_index.py --catalog catalog --flat -o release/catalog.json

One entry per bed that passed the gate. The index follows the family's bed
catalog contract (Backdrop's docs/BED-CATALOG.md): top-level `version: 1` and,
per bed, `id`, `file`, `duration_s`, `bpm`, `energy`, `mood`, `loop_safe`,
`license`, `sha256`. Alongside those it keeps the fuller Underscore record:
collection, profile, key, mode, seed, the loudness and true-peak measurements,
energy correlation, spectral centroid, engine, and the bundle file names
(basenames relative to the bed's own folder).

`file` is relative to the folder holding catalog.json: `<collection>/<id>/<id>.master.wav`
in the catalog tree, or the bare `<id>.master.wav` with `--flat` for a GitHub
release, where every file sits at the root. `energy` is the duration-weighted
mean of the brief's requested section energies (0 to 1; the under-speech rule
is 0.55 or below). `mood` is the profile. `loop_safe` is the manifest's `loop`
flag. `sha256` is the master WAV's hash, so a consumer can verify the file it
downloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _energy(brief: dict) -> float | None:
    sections = brief.get("sections") or []
    total = sum(max(0.0, float(s.get("end", 0)) - float(s.get("start", 0))) for s in sections)
    if not sections:
        return None
    if total <= 0:
        return round(sum(float(s["energy"]) for s in sections) / len(sections), 3)
    weighted = sum(float(s["energy"]) * max(0.0, float(s["end"]) - float(s["start"])) for s in sections)
    return round(weighted / total, 3)


def bed_entry(manifest_path: Path, flat: bool) -> dict | None:
    bed_dir = manifest_path.parent
    man = json.loads(manifest_path.read_text())
    if not man.get("gate_passed"):
        return None
    brief = json.loads((bed_dir / "brief.json").read_text())
    title = brief["title"]
    profile = "-".join(title.split("-")[:-3]) or title
    meas = man.get("measurements", {})
    files = {k: Path(v).name for k, v in man.get("files", {}).items()}
    collection = brief.get("collection") or bed_dir.parent.name
    master = files["master"]
    master_path = bed_dir / master
    return {
        "id": title,
        "file": master if flat else f"{collection}/{title}/{master}",
        "duration_s": brief.get("duration"),
        "bpm": brief.get("bpm"),
        "energy": _energy(brief),
        "mood": profile,
        "loop_safe": bool(man.get("loop", False)),
        "license": man.get("license", "CC0-1.0"),
        "sha256": _sha256(master_path),
        "collection": collection,
        "profile": profile,
        "key": brief.get("key"),
        "mode": brief.get("mode"),
        "seed": brief.get("seed"),
        "lufs_integrated": meas.get("lufs_integrated"),
        "true_peak_dbtp": meas.get("true_peak_dbtp"),
        "loudness_range_lu": meas.get("loudness_range_lu"),
        "energy_correlation": (round(meas["energy_correlation"], 4)
                               if meas.get("energy_correlation") is not None else None),
        "spectral_centroid_hz": (round(meas["spectral_centroid_hz"], 1)
                                 if meas.get("spectral_centroid_hz") is not None else None),
        "engine": man.get("engine"),
        "files": files,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--flat", action="store_true",
                    help="file paths are bare names (a release where every file sits at the root)")
    a = ap.parse_args()
    root = Path(a.catalog)
    beds = []
    for mp in sorted(root.glob("*/*/manifest.json")):
        e = bed_entry(mp, a.flat)
        if e:
            beds.append(e)
    beds.sort(key=lambda e: (e["collection"], e["id"]))
    index = {"version": 1, "beds": beds, "count": len(beds), "license": "CC0-1.0",
             "note": "Every bed is dedicated to the public domain under CC0 1.0."}
    out = Path(a.out or root / "catalog.json")
    out.write_text(json.dumps(index, indent=2) + "\n")
    print(f"{len(beds)} beds -> {out}")


if __name__ == "__main__":
    main()
