#!/usr/bin/env python3
"""Build catalog.json: a machine-readable index of every shipped bed.

    .venv/bin/python scripts/build_catalog_index.py --catalog catalog

One entry per bed that passed the gate: id, collection, profile, key, mode,
bpm, duration, seed, measurements, file names, license. File entries are
basenames relative to the bed's own folder. The index goes at the catalog
root and is published with each release.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def bed_entry(manifest_path: Path) -> dict | None:
    bed_dir = manifest_path.parent
    man = json.loads(manifest_path.read_text())
    if not man.get("gate_passed"):
        return None
    brief = json.loads((bed_dir / "brief.json").read_text())
    title = brief["title"]
    profile = "-".join(title.split("-")[:-3]) or title
    meas = man.get("measurements", {})
    files = {k: Path(v).name for k, v in man.get("files", {}).items()}
    return {
        "id": title,
        "collection": brief.get("collection") or bed_dir.parent.name,
        "profile": profile,
        "key": brief.get("key"),
        "mode": brief.get("mode"),
        "bpm": brief.get("bpm"),
        "duration_s": brief.get("duration"),
        "seed": brief.get("seed"),
        "lufs_integrated": meas.get("lufs_integrated"),
        "true_peak_dbtp": meas.get("true_peak_dbtp"),
        "loudness_range_lu": meas.get("loudness_range_lu"),
        "engine": man.get("engine"),
        "files": files,
        "license": man.get("license", "CC0-1.0"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog")
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    root = Path(a.catalog)
    beds = []
    for mp in sorted(root.glob("*/*/manifest.json")):
        e = bed_entry(mp)
        if e:
            beds.append(e)
    beds.sort(key=lambda e: (e["collection"], e["id"]))
    index = {"beds": beds, "count": len(beds), "license": "CC0-1.0",
             "note": "Every bed is dedicated to the public domain under CC0 1.0."}
    out = Path(a.out or root / "catalog.json")
    out.write_text(json.dumps(index, indent=2) + "\n")
    print(f"{len(beds)} beds -> {out}")


if __name__ == "__main__":
    main()
