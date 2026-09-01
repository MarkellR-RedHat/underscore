"""underscore: command line."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .brief import Brief, default_brief


def _p(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_init(a):
    b = default_brief(a.title, a.duration)
    out = Path(a.out or f"{a.title}.brief.json")
    b.save(out)
    _p(f"wrote {out}  (edit moods, energies, hits, speech; then: underscore score --brief {out})")


def cmd_analyze(a):
    from .analyze import brief_from_video
    brief, info = brief_from_video(a.video, a.title, a.llm, a.model, not a.no_transcript)
    out = Path(a.out or f"{brief.title}.brief.json")
    brief.save(out)
    _p(f"{len(info['cuts'])} cuts, {info['speech_spans']} speech spans, "
       f"{info['transcript_segments']} transcript segments -> {out}")


def cmd_compose(a):
    from .compose import compose
    brief = Brief.load(a.brief)
    _die_if_invalid(brief)
    code, program = compose(brief, a.llm, a.model)
    out = Path(a.out or f"{brief.title}.rb")
    out.write_text(program)
    _p(f"wrote {out}")


def cmd_render(a):
    from .render import render
    brief = Brief.load(a.brief)
    program = Path(a.program).read_text() if a.program else None
    info = render(program, brief, a.out or f"{brief.title}.raw.wav", a.engine)
    _p(json.dumps(info, indent=2))


def cmd_master(a):
    from .master import master, duck
    brief = Brief.load(a.brief)
    info = master(a.wav, a.out or f"{brief.title}.master.wav", brief, a.reference)
    if brief.speech and not a.no_duck:
        info["ducked"] = duck(info["master"], Path(info["master"]).with_suffix(".ducked.wav"), brief.speech)
    _p(json.dumps(info, indent=2))


def cmd_measure(a):
    from .measure import measure, gate
    brief = Brief.load(a.brief)
    m = measure(a.wav, brief)
    ok, reasons = gate(m, brief)
    print(json.dumps({"passed": ok, "reasons": reasons, "measurements": m}, indent=2, default=float))
    sys.exit(0 if ok else 2)


def cmd_score(a):
    """The whole pipeline."""
    from .compose import compose
    from .render import render
    from .master import master, duck
    from .measure import measure, gate
    from .export import export_bundle

    if a.video:
        from .analyze import brief_from_video
        brief, info = brief_from_video(a.video, a.title, a.llm if not a.offline_brief else None, a.model)
        _p(f"analyze: {len(info['cuts'])} cuts, {info['speech_spans']} speech spans")
    else:
        brief = Brief.load(a.brief)
    _die_if_invalid(brief)
    work = Path(a.workdir or f".underscore/{brief.title}")
    work.mkdir(parents=True, exist_ok=True)
    brief.save(work / "brief.json")

    program = None
    engine = a.engine
    if a.program:
        program = Path(a.program).read_text()
        _p(f"compose: reusing {a.program}")
    elif engine != "synth":
        try:
            _p(f"compose: asking {a.llm} for Sonic Pi code")
            _, program = compose(brief, a.llm, a.model)
            (work / f"{brief.title}.rb").write_text(program)
        except Exception as e:  # noqa: BLE001
            if engine == "sonicpi":
                raise
            _p(f"compose unavailable ({e}); falling back to synth engine")
            engine = "synth"

    rinfo = render(program, brief, work / f"{brief.title}.raw.wav", engine)
    _p(f"render: {rinfo['engine']} -> {rinfo['raw']}")
    minfo = master(rinfo["raw"], work / f"{brief.title}.master.wav", brief, a.reference)
    ducked = duck(minfo["master"], work / f"{brief.title}.ducked.wav", brief.speech) if brief.speech else None
    m = measure(minfo["master"], brief)
    ok, reasons = gate(m, brief)
    _p(f"measure: {m['lufs_integrated']:.1f} LUFS, peak {m['true_peak_dbtp']:.2f} dBTP, "
       f"LRA {m['loudness_range_lu']:.1f} LU -> {'PASS' if ok else 'FAIL'}")
    for r in reasons:
        _p(f"  - {r}")
    outdir = Path(a.out or f"out/{brief.title}")
    manifest = export_bundle(outdir, brief, program, rinfo, minfo, ducked, m, ok, reasons)
    _p(f"export: {outdir}  ({len(manifest['files'])} files)")
    if not ok and not a.ship_anyway:
        _p("gate FAILED: bundle written for inspection but not marked shippable (use --ship-anyway to override)")
        sys.exit(2)


def _die_if_invalid(brief: Brief) -> None:
    errs = brief.validate()
    if errs:
        _p("brief invalid:")
        for e in errs:
            _p(f"  - {e}")
        sys.exit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="underscore", description="Code-generated, measured, CC0 music beds for developer videos.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write a starter brief"); s.add_argument("title"); s.add_argument("--duration", type=float, default=60.0); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("analyze", help="video -> brief (local)"); s.add_argument("video"); s.add_argument("--title"); s.add_argument("--llm", default=None, choices=[None, "claude", "anthropic", "ollama"]); s.add_argument("--model"); s.add_argument("--no-transcript", action="store_true"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_analyze)
    s = sub.add_parser("compose", help="brief -> Sonic Pi program"); s.add_argument("brief"); s.add_argument("--llm", default="claude", choices=["claude", "anthropic", "ollama"]); s.add_argument("--model"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_compose)
    s = sub.add_parser("render", help="program -> raw WAV"); s.add_argument("--brief", required=True); s.add_argument("--program"); s.add_argument("--engine", default="auto", choices=["auto", "sonicpi", "synth"]); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("master", help="raw WAV -> mastered bed"); s.add_argument("wav"); s.add_argument("--brief", required=True); s.add_argument("--reference"); s.add_argument("--no-duck", action="store_true"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_master)
    s = sub.add_parser("measure", help="measure + gate"); s.add_argument("wav"); s.add_argument("--brief", required=True); s.set_defaults(fn=cmd_measure)
    s = sub.add_parser("score", help="full pipeline: brief or video -> bundle")
    g = s.add_mutually_exclusive_group(required=True); g.add_argument("--brief"); g.add_argument("--video")
    s.add_argument("--title"); s.add_argument("--llm", default="claude", choices=["claude", "anthropic", "ollama"]); s.add_argument("--model")
    s.add_argument("--offline-brief", action="store_true", help="video mode: derive the brief heuristically, no model call")
    s.add_argument("--engine", default="auto", choices=["auto", "sonicpi", "synth"]); s.add_argument("--reference")
    s.add_argument("--program", help="reuse an existing Sonic Pi program (skip compose)")
    s.add_argument("--workdir"); s.add_argument("-o", "--out"); s.add_argument("--ship-anyway", action="store_true")
    s.set_defaults(fn=cmd_score)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
