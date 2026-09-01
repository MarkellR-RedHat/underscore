"""compose: brief -> Sonic Pi code, written by the user's own model.

Backends (all bring-your-own; nothing is bundled or defaulted):
  cli   : a command-line agent already on this machine. UNDERSCORE_CLI holds
          the command, flags included; the prompt goes to stdin and the code
          comes back on stdout. A literal {model} in the command is replaced
          by --model / UNDERSCORE_MODEL.
  api   : a chat-completions style HTTP endpoint. UNDERSCORE_API_URL and a
          model (--model or UNDERSCORE_MODEL) are required; UNDERSCORE_API_KEY
          is sent as a bearer token when set.
  local : the same command seam as cli, read from UNDERSCORE_LOCAL (falling
          back to UNDERSCORE_CLI), for source material that must not leave
          the machine.
"""
from __future__ import annotations

import importlib.resources
import json
import os
import re
import shlex
import subprocess
import urllib.request

from .brief import Brief
from . import collections as _collections

KEY_OCTAVE = 3


def _spec() -> str:
    ref = importlib.resources.files("underscore").joinpath("prompts/compose.md")
    if ref.is_file():
        return ref.read_text()
    raise FileNotFoundError("prompt spec missing: underscore/prompts/compose.md")


def build_prompt(brief: Brief, feedback: str | None = None) -> str:
    bars = brief.section_bars()
    coll = _collections.get(getattr(brief, "collection", "analog") or "analog")
    lines = [
        _spec(),
        "",
        coll.prompt_block(brief.seed),
        "",
        "## This brief",
        f"key: {brief.key}{KEY_OCTAVE}  mode: {brief.mode}  bpm: {brief.bpm}  style: {brief.style}",
        f"total duration: {brief.duration:.1f}s  ({sum(bars)} bars of 4 beats)",
        "",
        "sections (define one :sec_i for each):",
    ]
    for i, (s, b) in enumerate(zip(brief.sections, bars)):
        under = any(sp.start < s.end and sp.end > s.start for sp in brief.speech)
        lines.append(f"  sec_{i}: {b} bars, mood={s.mood}, energy={s.energy:.2f}, "
                     f"under_speech={'yes' if under else 'no'}, notes={s.notes or '-'}")
    kinds = sorted({h.kind for h in brief.hits})
    if kinds:
        lines.append("")
        lines.append("hit kinds to define: " + ", ".join(f"hit_{k.replace('-', '_')}" for k in kinds))
    if feedback:
        lines += ["", "## Your previous attempt was rejected. Fix these and return the full code:", feedback]
    return "\n".join(lines)


# ---- backends ---------------------------------------------------------------

def _env_model(model: str | None) -> str | None:
    return model or os.environ.get("UNDERSCORE_MODEL") or None


def _run_command(prompt: str, model: str | None, env_vars: tuple[str, ...]) -> str:
    tmpl = next((os.environ.get(v) for v in env_vars if os.environ.get(v)), None)
    if not tmpl:
        raise RuntimeError(f"set {env_vars[0]} to the command that runs your model "
                           "(prompt on stdin, code on stdout; see README, Backends)")
    cmd = shlex.split(tmpl)
    if any("{model}" in c for c in cmd):
        m = _env_model(model)
        if not m:
            raise RuntimeError(f"the {env_vars[0]} command has a {{model}} slot; "
                               "pass --model or set UNDERSCORE_MODEL")
        cmd = [c.replace("{model}", m) for c in cmd]
    out = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=900)
    if out.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {out.stderr.strip()[:400]}")
    return out.stdout


def _run_cli(prompt: str, model: str | None) -> str:
    return _run_command(prompt, model, ("UNDERSCORE_CLI",))


def _run_local(prompt: str, model: str | None) -> str:
    return _run_command(prompt, model, ("UNDERSCORE_LOCAL", "UNDERSCORE_CLI"))


def _run_api(prompt: str, model: str | None) -> str:
    url = os.environ.get("UNDERSCORE_API_URL")
    if not url:
        raise RuntimeError("set UNDERSCORE_API_URL to a chat-completions style endpoint")
    m = _env_model(model)
    if not m:
        raise RuntimeError("the api backend needs a model: pass --model or set UNDERSCORE_MODEL")
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("UNDERSCORE_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = json.dumps({"model": m, "max_tokens": 4000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode())
    # two common response shapes: choices[].message.content, or content[].text
    if isinstance(data.get("choices"), list) and data["choices"]:
        return data["choices"][0].get("message", {}).get("content", "") or ""
    if isinstance(data.get("content"), list):
        return "".join(b.get("text", "") for b in data["content"] if isinstance(b, dict))
    raise RuntimeError("unrecognized response shape from UNDERSCORE_API_URL")


BACKENDS = {"cli": _run_cli, "api": _run_api, "local": _run_local}


def run_llm(prompt: str, backend: str = "cli", model: str | None = None) -> str:
    if backend not in BACKENDS:
        raise ValueError(f"unknown backend {backend}; choose from {list(BACKENDS)}")
    return BACKENDS[backend](prompt, model)


# ---- extraction + validation -----------------------------------------------

def extract_code(text: str) -> str:
    m = re.search(r"```(?:ruby)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip() + "\n"


FORBIDDEN = ["live_loop", "use_bpm", "use_random_seed", "sync ", "cue ", "\nloop do", "loop do\n"]

# Sonic Pi core API names that must never be redefined (the run aborts).
CORE_NAMES = {
    "tick", "look", "tick_set", "tick_reset", "play", "play_pattern", "play_chord", "sample", "synth",
    "sleep", "beat", "bar", "note", "chord", "scale", "ring", "range", "rrand", "rrand_i", "rand",
    "rand_i", "choose", "pick", "knit", "bools", "spread", "line", "dice", "one_in", "with_fx",
    "with_synth", "use_synth", "with_bpm", "use_bpm", "density", "at", "time_warp", "stop", "cue",
    "sync", "control", "kill", "vt", "rt", "bt", "set", "get", "define", "defonce", "ndefine",
    "in_thread", "live_loop", "loop", "puts", "print", "assert", "octs", "degree", "midi", "hz",
    "amp", "pan", "release", "attack", "sustain", "decay", "current_bpm", "use_debug",
}


def _define_names(code: str) -> list[str]:
    return re.findall(r"define\s+:([A-Za-z_][A-Za-z0-9_]*)", code)


def validate_code(code: str, brief: Brief) -> list[str]:
    errs: list[str] = []
    for i in range(len(brief.sections)):
        if not re.search(rf"define\s+:sec_{i}\s+do\s*\|\s*bars\s*\|", code):
            errs.append(f"missing `define :sec_{i} do |bars|`")
    for k in sorted({h.kind for h in brief.hits}):
        name = f"hit_{k.replace('-', '_')}"
        if not re.search(rf"define\s+:{name}\s+do", code):
            errs.append(f"missing `define :{name} do`")
    for bad in FORBIDDEN:
        if bad in code:
            errs.append(f"forbidden construct: {bad.strip()!r}")
    if "sleep" not in code:
        errs.append("no sleep calls found; sections would not advance time")
    for name in _define_names(code):
        if re.fullmatch(r"sec_\d+", name) or name.startswith("hit_"):
            continue
        if name in CORE_NAMES:
            errs.append(f"`define :{name}` redefines a Sonic Pi core function and would abort the run; rename it :us_{name}")
        elif not name.startswith("us_"):
            errs.append(f"helper `define :{name}` must be prefixed us_ (rename to :us_{name})")
    return errs


# ---- harness ---------------------------------------------------------------

def harness(brief: Brief, generated: str) -> str:
    bars = brief.section_bars()
    out = [
        f"# Underscore render: {brief.title}",
        f"use_bpm {brief.bpm}",
        f"use_random_seed {brief.seed}",
        "use_debug false",
        "",
        "# ---------------- generated palette + sections ----------------",
        generated.rstrip(),
        "",
        "# ---------------- harness (sequencing, do not edit) ----------------",
    ]
    for h in brief.hits:
        name = f"hit_{h.kind.replace('-', '_')}"
        out += ["in_thread do", f"  sleep {brief.seconds_to_beats(h.t):.4f}", f"  {name}", "end"]
    for i, b in enumerate(bars):
        out.append(f"sec_{i} {b}")
    # Hold the run open past the recording window: Sonic Pi 5 pauses its audio
    # engine the moment all runs complete, which would cut the record tap early.
    hold_beats = brief.seconds_to_beats(14.0)
    out.append(f"sleep {hold_beats:.4f}  # hold for the recorder tail")
    out.append("")
    return "\n".join(out)


def compose(brief: Brief, backend: str = "cli", model: str | None = None,
            retries: int = 1, feedback: str | None = None) -> tuple[str, str]:
    """Return (generated_code, full_program). Retries once with validator feedback.

    `feedback` seeds the first prompt with external rejection reasons, e.g. the
    runtime errors Sonic Pi reported for a previous attempt.
    """
    last_errs: list[str] = []
    for _attempt in range(retries + 1):
        prompt = build_prompt(brief, feedback)
        raw = run_llm(prompt, backend, model)
        code = extract_code(raw)
        last_errs = validate_code(code, brief)
        if not last_errs:
            return code, harness(brief, code)
        feedback = "\n".join(f"- {e}" for e in last_errs)
    raise RuntimeError("generated code failed validation:\n" + "\n".join(last_errs))
