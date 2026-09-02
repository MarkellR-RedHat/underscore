#!/usr/bin/env python3
"""Write the CC0 dedication into every catalog bed's audio files (bext in WAVs, ID3 in MP3s), naming each
bed's manifest.json. Idempotent: an existing tag is replaced, never stacked. Manifests are not touched.

    .venv/bin/python scripts/tag_catalog.py --catalog catalog
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from underscore import __version__  # noqa: E402
from underscore.dedication import tag_bundle  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog")
    a = ap.parse_args()
    n = 0
    for mp in sorted(Path(a.catalog).glob("*/*/manifest.json")):
        man = json.loads(mp.read_text())
        tag_bundle(mp.parent, mp.parent.name, man["files"], man.get("underscore_version") or __version__,
                   man.get("measurements"), man.get("generated_at", ""))
        n += 1
    print(f"tagged {n} beds under {a.catalog}")


if __name__ == "__main__":
    main()
