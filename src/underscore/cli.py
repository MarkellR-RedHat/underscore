"""underscore: command line."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .brief import Brief, BriefError, default_brief


def _p(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_init(a):
    b = default_brief(a.title, a.duration)
    out = Path(a.out or f"{a.title}.brief.json")
    b.save(out)
    _p(f"wrote {out}  (edit moods, energies, hits, speech; then: underscore score --brief {out})")


def default_llm(explicit: str | None) -> str | None:
    """Video mode uses the model when a backend is configured, without an explicit --llm.
    None means the brief stays heuristic, and the run says so."""
    if explicit:
        return explicit
    if os.environ.get("UNDERSCORE_CLI"):
        return "cli"
    if os.environ.get("UNDERSCORE_API_URL"):
        return "api"
    if os.environ.get("UNDERSCORE_LOCAL"):
        return "local"
    return None


def resolve_out(out: str | None, default_name: str) -> Path:
    """`-o` may be a file or a directory (score accepts a directory; master now does too).
    A directory, or a path with no audio extension, gets the default file name inside it."""
    if not out:
        return Path(default_name)
    p = Path(out)
    if p.is_dir() or out.endswith(os.sep) or p.suffix.lower() not in (".wav", ".flac", ".aiff", ".aif"):
        p.mkdir(parents=True, exist_ok=True)
        return p / default_name
    return p


def cmd_analyze(a):
    from .analyze import brief_from_video
    llm = default_llm(a.llm)
    brief, info = brief_from_video(a.video, a.title, llm, a.model, not a.no_transcript)
    out = Path(a.out or f"{brief.title}.brief.json")
    brief.save(out)
    how = f"brief by the model ({llm})" if llm else "brief by heuristic (no backend configured: set UNDERSCORE_CLI, UNDERSCORE_API_URL, or UNDERSCORE_LOCAL, or pass --llm)"
    _p(f"{len(info['cuts'])} cuts, {info['speech_spans']} speech spans ({info['speech_source']}), "
       f"{info['transcript_segments']} transcript segments, {how} -> {out}")


def cmd_compose(a):
    from .compose import compose
    brief = _load_brief(a.brief)
    try:
        code, program = compose(brief, a.llm, a.model)
    except RuntimeError as e:
        # no backend configured, or the backend failed: one line, exit 2, no traceback
        _p(f"compose: {e}")
        sys.exit(2)
    out = Path(a.out or f"{brief.title}.rb")
    out.write_text(program)
    _p(f"wrote {out}")


def cmd_render(a):
    from .render import render
    if a.sonic_pi_app:
        os.environ["UNDERSCORE_SONIC_PI_APP"] = a.sonic_pi_app
    brief = _load_brief(a.brief)
    program = Path(a.program).read_text() if a.program else None
    info = render(program, brief, a.out or f"{brief.title}.raw.wav", a.engine)
    _p(json.dumps(info, indent=2))


def cmd_master(a):
    from .master import master, duck
    brief = _load_brief(a.brief)
    out = resolve_out(a.out, f"{brief.title}.master.wav")
    info = master(a.wav, out, brief, a.reference, loop=a.loop)
    if brief.speech and not a.no_duck:
        info["ducked"] = duck(info["master"], Path(info["master"]).with_suffix(".ducked.wav"), brief.speech)
    _p(json.dumps(info, indent=2))


def cmd_measure(a):
    from .measure import measure, gate
    brief = _load_brief(a.brief)
    m = measure(a.wav, brief, loop=a.loop)
    ok, reasons = gate(m, brief, loop_trim_s=0.5 if a.loop else 0.0)
    from .export import gate_report
    report = gate_report(reasons, m)
    print(json.dumps({"passed": report.passed, "reasons": reasons, "measurements": m, "gates": report.to_dict()}, indent=2, default=float))
    sys.exit(report.exit_code)


def cmd_doctor(a):
    """Can this machine run the pipeline? Checks, one line each."""
    import shutil as _sh
    import sys as _sys
    if a.sonic_pi_app:
        os.environ["UNDERSCORE_SONIC_PI_APP"] = a.sonic_pi_app
    ok = lambda s: print(f"  ✓ {s}")          # noqa: E731
    no = lambda s: print(f"  ✗ {s}")          # noqa: E731
    print("Underscore doctor")
    v = _sys.version_info
    (ok if v >= (3, 10) else no)(f"Python {v.major}.{v.minor}.{v.micro}" + ("" if v >= (3, 10) else "  (3.10+ required)"))
    for tool, hint in (("ffmpeg", "brew install ffmpeg / apt-get install ffmpeg"),
                       ("ffprobe", "comes with ffmpeg")):
        (ok if _sh.which(tool) else no)(f"{tool}" + ("" if _sh.which(tool) else f"  ({hint})"))
    try:
        import pedalboard  # noqa: F401
        ok("pedalboard imports (mastering chain ready)")
    except Exception as e:  # noqa: BLE001
        no(f"pedalboard import failed: {e}  (Debian/Ubuntu: apt-get install libatomic1)")
    from .render import app_root, sonicpi_available, RECORDER
    root = app_root()
    if sonicpi_available():
        ver = ""
        plist = root / "Contents" / "Info.plist"
        if plist.exists():
            import re as _re
            m = _re.search(r"CFBundleShortVersionString</key>\s*<string>([^<]+)", plist.read_text(errors="ignore"))
            if m:
                ver = f" {m.group(1)}"
                if not m.group(1).startswith("5"):
                    no(f"Sonic Pi{ver} at {root}: version 5.x required for headless render")
                    ver = None
        if ver is not None:
            ok(f"Sonic Pi{ver} at {root} (headless boot library + recorder present)")
    else:
        no(f"Sonic Pi headless render unavailable at {root}  (brew install --cask sonic-pi, or set UNDERSCORE_SONIC_PI_APP; the synth engine still runs everything)")
    if RECORDER.exists():
        ok("bundled recorder present")
    else:
        no("bundled recorder missing (reinstall the package)")
    cli_cmd = os.environ.get("UNDERSCORE_CLI")
    if cli_cmd:
        import shlex as _shlex
        binname = _shlex.split(cli_cmd)[0]
        (ok if _sh.which(binname) else no)(f"cli backend: UNDERSCORE_CLI = {cli_cmd!r}" + ("" if _sh.which(binname) else f"  ({binname} not on PATH)"))
    else:
        no("cli backend unconfigured: set UNDERSCORE_CLI (see README, Backends); only --engine synth works without one")
    if os.environ.get("UNDERSCORE_API_URL"):
        ok(f"api backend: UNDERSCORE_API_URL set" + ("" if os.environ.get("UNDERSCORE_MODEL") else "  (remember UNDERSCORE_MODEL or --model)"))
    if os.environ.get("UNDERSCORE_LOCAL"):
        ok("local backend: UNDERSCORE_LOCAL set")
    free_gb = _sh.disk_usage(".").free / 1e9
    (ok if free_gb > 2 else no)(f"{free_gb:.1f} GB free on this volume" + ("" if free_gb > 2 else "  (renders need room)"))


def cmd_score(a):
    """The whole pipeline."""
    from .compose import compose
    from .render import render
    from .master import master, duck
    from .measure import measure, gate
    from .export import export_bundle

    if a.sonic_pi_app:
        os.environ["UNDERSCORE_SONIC_PI_APP"] = a.sonic_pi_app
    brief_info = {"source": "file", "analyze_backend": None, "analyze_model": None, "analyze_seconds": None}
    if a.video:
        from .analyze import brief_from_video
        import time as _t0
        _s = _t0.perf_counter()
        brief, info = brief_from_video(a.video, a.title, None if a.offline_brief else default_llm(a.llm), a.model)
        brief_info = {"source": info["brief_source"], "analyze_backend": info["analyze_backend"],
                      "analyze_model": info["analyze_model"], "analyze_seconds": round(_t0.perf_counter() - _s, 1),
                      "speech_source": info["speech_source"]}
        _p(f"analyze: {len(info['cuts'])} cuts, {info['speech_spans']} speech spans ({info['speech_source']}), brief by {info['brief_source']}")
    else:
        brief = _load_brief(a.brief)
    work = Path(a.workdir or f".underscore/{brief.title}")
    work.mkdir(parents=True, exist_ok=True)
    brief.save(work / "brief.json")

    import time as _time
    timings: dict[str, float] = {}
    _t = _time.perf_counter()
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
                _p(f"compose: {e}")
                sys.exit(2)
            _p(f"compose unavailable ({e}); falling back to synth engine")
            engine = "synth"

    timings["compose"] = round(_time.perf_counter() - _t, 1); _t = _time.perf_counter()
    from .render import RenderError
    try:
        rinfo = render(program, brief, work / f"{brief.title}.raw.wav", engine)
    except RenderError as err:
        # Sonic Pi rejected the program at runtime: hand the errors back to the
        # model once, then try again. Static validation cannot catch everything.
        _p("render: Sonic Pi reported runtime errors; recomposing with feedback")
        for e in err.errors[:4]:
            _p(f"  - {e}")
        fb = "Sonic Pi reported these runtime errors in your previous code:\n" + "\n".join(f"- {e}" for e in err.errors)
        _, program = compose(brief, a.llm, a.model, feedback=fb)
        (work / f"{brief.title}.rb").write_text(program)
        timings["recompose"] = round(_time.perf_counter() - _t, 1); _t = _time.perf_counter()
        rinfo = render(program, brief, work / f"{brief.title}.raw.wav", engine)
    timings["render"] = round(_time.perf_counter() - _t, 1); _t = _time.perf_counter()
    _p(f"render: {rinfo['engine']} -> {rinfo['raw']}" + (f"  (preroll {rinfo['preroll_s']}s)" if 'preroll_s' in rinfo else ""))
    minfo = master(rinfo["raw"], work / f"{brief.title}.master.wav", brief, a.reference, loop=a.loop)
    ducked = duck(minfo["master"], work / f"{brief.title}.ducked.wav", brief.speech) if brief.speech else None
    timings["master"] = round(_time.perf_counter() - _t, 1); _t = _time.perf_counter()
    m = measure(minfo["master"], brief, loop=a.loop)
    ok, reasons = gate(m, brief, loop_trim_s=minfo.get("loop_trim_s", 0.0))
    timings["measure"] = round(_time.perf_counter() - _t, 1)
    _p(f"measure: {m['lufs_integrated']:.1f} LUFS, peak {m['true_peak_dbtp']:.2f} dBTP, "
       f"LRA {m['loudness_range_lu']:.1f} LU -> {'PASS' if ok else 'FAIL'}")
    for r in reasons:
        _p(f"  - {r}")
    outdir = Path(a.out or f"out/{brief.title}")
    manifest = export_bundle(outdir, brief, program, rinfo, minfo, ducked, m, ok, reasons, timings, loop=a.loop,
                             brief_info=brief_info, compose_backend=None if engine == "synth" or a.program else a.llm)
    _p(f"export: {outdir}  ({len(manifest['files'])} files)")
    _p("timing: " + " ".join(f"{k}={v}s" for k, v in timings.items()))
    if not ok and not a.ship_anyway:
        _p("gate FAILED: bundle written for inspection but not marked shippable (use --ship-anyway to override)")
        sys.exit(2)


def _load_brief(path) -> Brief:
    """Load and validate; every problem is printed, then exit 1 (the shared BriefError carries them all)."""
    try:
        return Brief.load(path)
    except BriefError as err:
        _p(f"brief invalid: {err.path}")
        for e in err.errors:
            _p(f"  - {e}")
        sys.exit(1)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="underscore", description="Code-generated, measured, CC0 music beds for developer videos.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="write a starter brief"); s.add_argument("title"); s.add_argument("--duration", type=float, default=60.0); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_init)
    s = sub.add_parser("analyze", help="video -> brief (local)"); s.add_argument("video"); s.add_argument("--title"); s.add_argument("--llm", default=None, choices=[None, "cli", "api", "local"]); s.add_argument("--model"); s.add_argument("--no-transcript", action="store_true"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_analyze)
    s = sub.add_parser("compose", help="brief -> Sonic Pi program"); s.add_argument("brief"); s.add_argument("--llm", default="cli", choices=["cli", "api", "local"]); s.add_argument("--model"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_compose)
    s = sub.add_parser("render", help="program -> raw WAV"); s.add_argument("--brief", required=True); s.add_argument("--program"); s.add_argument("--engine", default="auto", choices=["auto", "sonicpi", "synth"]); s.add_argument("--sonic-pi-app", help="Sonic Pi application path (default /Applications/Sonic Pi.app)"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("master", help="raw WAV -> mastered bed"); s.add_argument("wav"); s.add_argument("--brief", required=True); s.add_argument("--reference"); s.add_argument("--no-duck", action="store_true"); s.add_argument("--loop", action="store_true", help="loop-safe: no fades, seam crossfaded for tiling"); s.add_argument("-o", "--out"); s.set_defaults(fn=cmd_master)
    s = sub.add_parser("doctor", help="check this machine: renderer, tools, backends"); s.add_argument("--sonic-pi-app"); s.set_defaults(fn=cmd_doctor)
    s = sub.add_parser("measure", help="measure + gate"); s.add_argument("wav"); s.add_argument("--brief", required=True); s.add_argument("--loop", action="store_true", help="the WAV is a loop-safe bed (seam check, trimmed duration)"); s.set_defaults(fn=cmd_measure)
    s = sub.add_parser("score", help="full pipeline: brief or video -> bundle")
    g = s.add_mutually_exclusive_group(required=True); g.add_argument("--brief"); g.add_argument("--video")
    s.add_argument("--title"); s.add_argument("--llm", default="cli", choices=["cli", "api", "local"]); s.add_argument("--model")
    s.add_argument("--offline-brief", action="store_true", help="video mode: derive the brief heuristically, no model call")
    s.add_argument("--engine", default="auto", choices=["auto", "sonicpi", "synth"]); s.add_argument("--reference")
    s.add_argument("--program", help="reuse an existing Sonic Pi program (skip compose)")
    s.add_argument("--loop", action="store_true", help="loop-safe bed: no fades, seam crossfaded so the track tiles")
    s.add_argument("--sonic-pi-app", help="Sonic Pi application path (default /Applications/Sonic Pi.app)")
    s.add_argument("--workdir"); s.add_argument("-o", "--out"); s.add_argument("--ship-anyway", action="store_true")
    s.set_defaults(fn=cmd_score)

    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
