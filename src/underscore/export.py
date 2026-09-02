"""export: the bundle an editor actually wants.

master WAV, speech-ducked WAV, stems, MP3 preview, timeline markers (CSV and
EDL), the Sonic Pi source, a manifest with seed + brief + measurements, and
the CC0 dedication. Every track is reproducible from its own bundle.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from . import __version__
from .brief import Brief
from .master import preview_mp3

CC0 = ("This audio is dedicated to the public domain under CC0 1.0 Universal.\n"
       "Use it in anything, commercial or not, with no attribution required.\n"
       "https://creativecommons.org/publicdomain/zero/1.0/\n")


def _tc(t: float, fps: float = 30.0) -> str:
    f = int(round((t - int(t)) * fps))
    s = int(t)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}:{f:02d}"


def write_markers(brief: Brief, outdir: Path) -> list[str]:
    rows = [("Section: " + s.mood, s.start, s.end, "section") for s in brief.sections]
    rows += [("Hit: " + h.kind, h.t, h.t, "hit") for h in brief.hits]
    rows.sort(key=lambda r: r[1])
    csv = outdir / "markers.csv"
    with csv.open("w") as f:
        f.write("name,start_s,end_s,type,start_tc,end_tc\n")
        for name, a, b, kind in rows:
            f.write(f"{name},{a:.3f},{b:.3f},{kind},{_tc(a)},{_tc(b)}\n")
    edl = outdir / "markers.edl"
    with edl.open("w") as f:
        f.write(f"TITLE: {brief.title}\nFCM: NON-DROP FRAME\n\n")
        for i, (name, a, b, kind) in enumerate(rows, 1):
            f.write(f"{i:03d}  AX       V     C        {_tc(a)} {_tc(b)} {_tc(a)} {_tc(b)}\n")
            f.write(f"* FROM CLIP NAME: {name}\n* COMMENT: {kind}\n\n")
    return [str(csv), str(edl)]


def export_bundle(outdir: str | Path, brief: Brief, program: str | None,
                  render_info: dict, master_info: dict, ducked: str | None,
                  measurements: dict, passed: bool, reasons: list[str],
                  timings: dict | None = None, loop: bool = False,
                  brief_info: dict | None = None, compose_backend: str | None = None) -> dict:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    # manifest paths are basenames: every listed file sits next to the manifest
    master_wav = Path(master_info["master"])
    files["master"] = Path(shutil.copy(master_wav, out / f"{brief.title}.master.wav")).name
    if ducked:
        files["ducked"] = Path(shutil.copy(ducked, out / f"{brief.title}.ducked.wav")).name
    for name, p in (render_info.get("stems") or {}).items():
        files[f"stem_{name}"] = Path(shutil.copy(p, out / f"{brief.title}.stem-{name}.wav")).name
    mp3 = preview_mp3(master_wav, out / f"{brief.title}.preview.mp3")
    if mp3:
        files["preview"] = Path(mp3).name
    if program:
        (out / f"{brief.title}.rb").write_text(program)
        files["source"] = f"{brief.title}.rb"
    csv_p, edl_p = write_markers(brief, out)
    files["markers_csv"], files["markers_edl"] = Path(csv_p).name, Path(edl_p).name
    (out / "LICENSE-CC0.txt").write_text(CC0)
    brief.save(out / "brief.json")

    manifest = {
        "underscore_version": __version__,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine": render_info.get("engine"),
        "render_errors": render_info.get("sonicpi_errors", []),
        "seed": brief.seed,
        "loop": loop,
        "gate_passed": passed,
        "gate_reasons": reasons,
        "stage_seconds": timings or {},
        # receipts: where the brief came from and which seam composed the program. Cost in
        # dollars is not recorded because the cli and local seams do not report it; the
        # backend and model names are, and the time each model stage took is in stage_seconds.
        "brief": {"source": "file", "analyze_backend": None, "analyze_model": None, "analyze_seconds": None,
                  **(brief_info or {})},
        "compose_backend": compose_backend,
        "measurements": measurements,
        "master": {k: v for k, v in master_info.items() if k != "master"},
        "files": files,
        "license": "CC0-1.0",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=float))
    # The dedication travels inside every audio file (bext in WAVs, ID3 in the MP3), naming this manifest.
    from .dedication import tag_bundle
    tag_bundle(out, brief.title, files, __version__, measurements, manifest["generated_at"])
    # README.txt describes only the files this bundle actually contains.
    lines = [brief.title, "", f"Drop {Path(files['master']).name} under your video."]
    if "ducked" in files:
        lines.append("If your video has speech, use the .ducked.wav instead: it already sits under the voice.")
    lines.append("Import markers.csv or markers.edl for section and hit markers on your timeline.")
    if any(k.startswith("stem_") for k in files):
        lines.append("The .stem-*.wav files are separate instrument layers if you want to remix.")
    if "source" in files:
        lines.append("The .rb file is the Sonic Pi source: the code is the score.")
    lines.append("Every WAV carries the dedication in its bext chunk and the MP3 in its ID3 tags, with the bed id and the sha256 of manifest.json.")
    lines += ["", "License: CC0. Use it for anything."]
    (out / "README.txt").write_text("\n".join(lines) + "\n")
    return manifest
