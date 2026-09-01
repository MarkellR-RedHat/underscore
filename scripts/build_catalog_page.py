#!/usr/bin/env python3
"""Build catalog/index.html: a browsable, playable index of every shipped bed.

    .venv/bin/python scripts/build_catalog_page.py --catalog catalog

Only beds whose gate passed are listed. Each card: profile, key, tempo,
duration, measured loudness and peak, an inline player, and download links
for the master, the ducked mix, the stems, and the Sonic Pi source.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

CSS = """
:root{--sans:'Inter',-apple-system,sans-serif;--display:'Fraunces',Georgia,serif;--ink:#0a0f1e;--soft:#48546a;--faint:#8892a5;
--grad:linear-gradient(135deg,#1f5fe6 0%,#4b2fe0 35%,#8f2bd0 65%,#ff3b6b 100%);--line:rgba(10,15,30,.08)}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:var(--sans);color:var(--ink);background:#fbfcfe;padding:2.5rem 2rem;max-width:1100px;margin:0 auto}
h1{font-family:var(--display);font-weight:900;font-size:2.4rem;letter-spacing:-.02em}
h1 span{background:var(--grad);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
.sub{color:var(--soft);margin:.6rem 0 2rem;max-width:640px;line-height:1.6}
.coll{margin-bottom:2.6rem}.coll h2{font-family:var(--display);font-weight:900;font-size:1.7rem;text-transform:capitalize;margin-bottom:.2rem}.tag-line{color:var(--soft);margin-bottom:1rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:1.2rem}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:1.2rem;position:relative;overflow:hidden}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--grad)}
.card h3{font-family:var(--display);font-weight:900;font-size:1.15rem;margin-bottom:.25rem}
.meta{font-size:.82rem;color:var(--soft);margin-bottom:.7rem}.meta b{color:var(--ink)}
.tags{display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:.8rem}
.tag{font-size:.7rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:.25rem .55rem;border-radius:999px;background:rgba(31,95,230,.09);color:#1f5fe6}
audio{width:100%;margin:.4rem 0 .7rem}
.dl{display:flex;gap:.5rem;flex-wrap:wrap}.dl a{font-size:.8rem;font-weight:600;color:var(--ink);text-decoration:none;border:1.5px solid var(--line);border-radius:10px;padding:.35rem .7rem}
.dl a:hover{border-color:#1f5fe6}
footer{margin-top:3rem;color:var(--faint);font-size:.85rem;text-align:center;line-height:1.6}
"""


def card(d: Path, man: dict, brief: dict, prefix: str = "") -> str:
    m = man["measurements"]
    files = man["files"]
    rel = lambda p: html.escape(f"{prefix}/{d.name}/{Path(p).name}" if prefix else f"{d.name}/{Path(p).name}")
    profile = brief["title"].split("-")[0]
    links = [("master WAV", files.get("master")), ("ducked WAV", files.get("ducked")),
             ("source .rb", files.get("source")), ("markers", files.get("markers_csv"))]
    stems = [(f"stem {k[5:]}", v) for k, v in files.items() if k.startswith("stem_")]
    dl = "".join(f'<a href="{rel(p)}" download>{html.escape(n)}</a>' for n, p in links + stems if p)
    return f"""
<div class="card">
  <h3>{html.escape(brief["title"])}</h3>
  <div class="meta"><b>{html.escape(profile)}</b> · {html.escape(brief["key"])} {html.escape(brief["mode"])} · {brief["bpm"]} BPM · {int(brief["duration"])} s · seed {brief["seed"]}</div>
  <div class="tags"><span class="tag">{m["lufs_integrated"]:.1f} LUFS</span><span class="tag">{m["true_peak_dbtp"]:.1f} dBTP</span><span class="tag">CC0</span></div>
  <audio controls preload="none" src="{rel(files["preview"]) if files.get("preview") else rel(files["master"])}"></audio>
  <div class="dl">{dl}</div>
</div>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--catalog", default="catalog")
    a = ap.parse_args()
    root = Path(a.catalog)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from underscore.collections import COLLECTIONS
    sections, total, skipped = [], 0, 0
    for cname, coll in COLLECTIONS.items():
        cdir = root / cname
        if not cdir.is_dir():
            continue
        cards = []
        for d in sorted(p for p in cdir.iterdir() if p.is_dir() and (p / "manifest.json").exists()):
            man = json.loads((d / "manifest.json").read_text())
            if not man.get("gate_passed"):
                skipped += 1; continue
            brief = json.loads((d / "brief.json").read_text())
            cards.append(card(d, man, brief, prefix=cname))
        if cards:
            total += len(cards)
            sections.append(f'<section class="coll"><h2>{html.escape(cname)}</h2><p class="tag-line">{html.escape(coll.tagline)}. {html.escape(coll.sound.split(".")[0])}.</p><div class="grid">{"".join(cards)}</div></section>')
    cards = sections
    page = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Underscore catalog</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fraunces:opsz,wght@9..144,900&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<h1>Underscore <span>catalog</span></h1>
<p class="sub">Code-generated background music for developer videos. Every bed here passed a measurement gate
(loudness, true peak, energy curve), ships with its Sonic Pi source and seed, and is dedicated to the public domain under CC0.
Use any of it in anything, no attribution needed.</p>
{''.join(cards)}
<footer>{total} beds shipped · {skipped} withheld by the gate · a <a href="https://rawlslab.ai">RawlsLab</a> project · code MIT, music CC0</footer>
</body></html>"""
    (root / "index.html").write_text(page)
    print(f"wrote {root/'index.html'}: {total} beds listed, {skipped} withheld")


if __name__ == "__main__":
    main()
