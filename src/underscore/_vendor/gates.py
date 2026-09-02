# Vendored from rawlslab-core 3e2563e (2026-09-01). Do not edit here; change MarkellRawls/core and re-run scripts/vendor.py.
"""The gate skeleton every tool runs: named checks whose failures are counted, reported, and never quietly shipped.

Extracted from the gate running in Galley (style, citations, consistency,
brand), Backdrop (source, style, transcript), Underscore (measure and gate),
and Rot (per document verdicts). The shared shape: a Gate has a name and a
check; a check yields issues at three severities (error blocks, warning shows
in review, flag is informational); results collect into a gates.json shaped
report with the failing gates first; the process exits 0 when clean and 2
when any gate has errors. Depends on nothing outside the standard library.

A check may return Issue objects, plain dicts with a "severity" key, or a
Galley style {"errors": [...], "warnings": [...], "stats": {...}} dict, so
the existing gate functions plug in unchanged.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SEVERITIES = ("error", "warning", "flag")


@dataclass
class Issue:
    rule: str
    msg: str
    severity: str = "error"
    line: int | None = None
    loc: str = ""
    excerpt: str = ""

    def to_dict(self) -> dict:
        d = {"rule": self.rule, "msg": self.msg}
        if self.line is not None:
            d["line"] = self.line
        if self.loc:
            d["loc"] = self.loc
        if self.excerpt:
            d["excerpt"] = self.excerpt
        return d


def error(rule: str, msg: str, line: int | None = None, loc: str = "", excerpt: str = "") -> Issue:
    return Issue(rule, msg, "error", line, loc, excerpt[:120])


def warning(rule: str, msg: str, line: int | None = None, loc: str = "", excerpt: str = "") -> Issue:
    return Issue(rule, msg, "warning", line, loc, excerpt[:120])


def flag(rule: str, msg: str, line: int | None = None, loc: str = "", excerpt: str = "") -> Issue:
    return Issue(rule, msg, "flag", line, loc, excerpt[:120])


@dataclass
class Gate:
    """A named check. The callable takes the subject and returns issues in any of the accepted shapes."""

    name: str
    check: object  # callable(subject) -> issues

    def run(self, subject) -> dict:
        return _normalize(self.check(subject))


def _issue_dict(x, severity: str) -> dict:
    if isinstance(x, Issue):
        return x.to_dict()
    if isinstance(x, dict):
        return {k: v for k, v in x.items() if k != "severity"}
    return {"rule": "gate", "msg": str(x)}


def _normalize(result) -> dict:
    out = {"errors": [], "warnings": [], "flags": [], "stats": {}}
    if result is None:
        return out
    if isinstance(result, dict) and ("errors" in result or "warnings" in result):
        for sev, key in (("error", "errors"), ("warning", "warnings"), ("flag", "flags")):
            for x in result.get(key, []) or []:
                out[key].append(_issue_dict(x, sev))
        stats = result.get("stats")
        if isinstance(stats, dict):
            out["stats"] = stats
        return out
    for x in result:
        sev = x.severity if isinstance(x, Issue) else (x.get("severity", "error") if isinstance(x, dict) else "error")
        if sev not in SEVERITIES:
            sev = "error"
        out[sev + "s"].append(_issue_dict(x, sev))
    return out


@dataclass
class Report:
    """Every gate's result, ordered for the review page: gates with errors first."""

    gates: dict = field(default_factory=dict)

    def add(self, name: str, result: dict) -> None:
        self.gates[name] = _normalize(result)

    @property
    def passed(self) -> bool:
        return all(not g["errors"] for g in self.gates.values())

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 2

    def counts(self) -> dict:
        return {name: {"errors": len(g["errors"]), "warnings": len(g["warnings"]), "flags": len(g["flags"])}
                for name, g in self.gates.items()}

    def _ordered(self) -> list[str]:
        names = list(self.gates)
        return sorted(names, key=lambda n: (0 if self.gates[n]["errors"] else (1 if self.gates[n]["warnings"] else 2),
                                            names.index(n)))

    def to_dict(self) -> dict:
        return {"passed": self.passed, **{n: self.gates[n] for n in self._ordered()}}

    def write(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    def summary(self) -> str:
        lines = []
        for n in self._ordered():
            g = self.gates[n]
            verdict = "FAIL" if g["errors"] else "pass"
            lines.append(f"{verdict}  {n}: {len(g['errors'])} errors, {len(g['warnings'])} warnings, {len(g['flags'])} flags")
        lines.append("PASS: every gate clean." if self.passed else "HOLD: a gate has errors.")
        return "\n".join(lines)


def run_gates(gates: list[Gate], subject) -> Report:
    report = Report()
    for g in gates:
        report.add(g.name, g.run(subject))
    return report
