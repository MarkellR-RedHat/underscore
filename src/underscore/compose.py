"""compose: brief -> Sonic Pi code, written by the user's own model.

Backends, in order of preference:
  claude   : the Claude Code CLI (`claude -p`), i.e. the user's own subscription
  anthropic: the Anthropic API if ANTHROPIC_API_KEY is set and the SDK is installed
  ollama   : a local model, for source material that must not leave the machine
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .brief import Brief

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "compose.md"
KEY_OCTAVE = 3


def _spec() -> str:
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    raise FileNotFoundError(f"prompt spec missing at {PROMPT_PATH}")


def build_prompt(brief: Brief, feedback: str | None = None) -> str:
    bars = brief.section_bars()
    lines = [
        _spec(),
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

def _run_claude(prompt: str, model: str | None) -> str:
    if not shutil.which("claude"):
        raise RuntimeError("claude CLI not found; install Claude Code or use --llm anthropic/ollama")
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if model:
        cmd += ["--model", model]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if out.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {out.stderr.strip()[:400]}")
    return out.stdout


def _run_anthropic(prompt: str, model: str | None) -> str:
    try:
        import anthropic  # type: ignore
    except ImportError as e:
        raise RuntimeError("pip install anthropic, or use --llm claude") from e
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model or "claude-sonnet-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(getattr(b, "text", "") for b in msg.content)


def _run_ollama(prompt: str, model: str | None) -> str:
    if not shutil.which("ollama"):
        raise RuntimeError("ollama not found")
    out = subprocess.run(["ollama", "run", model or "llama3.1"], input=prompt,
                         capture_output=True, text=True, timeout=900)
    if out.returncode != 0:
        raise RuntimeError(f"ollama failed: {out.stderr.strip()[:400]}")
    return out.stdout


BACKENDS = {"claude": _run_claude, "anthropic": _run_anthropic, "ollama": _run_ollama}


def run_llm(prompt: str, backend: str = "claude", model: str | None = None) -> str:
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


def compose(brief: Brief, backend: str = "claude", model: str | None = None,
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
