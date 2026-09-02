# Vendored from rawlslab-core 64f6302 (2026-09-01). Do not edit here; change MarkellRawls/core and re-run scripts/vendor.py.
"""Brief schemas: the content brief (Galley) and the music brief (Underscore).

These are different documents describing different work, and this module does
not pretend otherwise. What they genuinely share, and what lives here: the
load-validate-refuse pattern, a frontmatter splitter, validation that returns
every problem at once as a list of plain messages, and one typed error
(BriefError) that carries the path and that list. The two schemas themselves
are documented dataclasses, side by side, not merged: the content brief has no
sections or duration, the music brief has no outputs or audience, so there is
no common section shape to extract.

What stayed tool specific and why: Galley keeps its prompt assembly around the
brief; Underscore keeps the timing arithmetic (beat and bar lengths, bar
quantization) and the video derivation helpers (bpm_for_cuts,
sections_from_cuts), which are music generation logic, not schema. One
behavior change against Galley's parser: it raised ValueError at the first
problem, while load_content_brief raises BriefError carrying all of them.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml


class BriefError(ValueError):
    """A brief that failed validation: the path and every problem found."""

    def __init__(self, path: str, errors: list[str]):
        self.path = str(path)
        self.errors = list(errors)
        super().__init__(f"{path}: " + "; ".join(errors))


def split_frontmatter(text: str) -> tuple[dict, str]:
    """YAML frontmatter and the body below it; ({}, text) when there is none."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            return (meta if isinstance(meta, dict) else {}), parts[2].strip()
    return {}, text.strip()


# ---- content brief (Galley) ---------------------------------------------

CONTENT_TYPES = {"finding", "tutorial", "opinion", "explainer"}
_DURATION = re.compile(r"^(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration_seconds(value: str) -> int | None:
    """Seconds for a duration string like 3m, 90s, or 2m30s; None when it is not one."""
    m = _DURATION.match(value.strip())
    if not m or not (m.group(1) or m.group(2)):
        return None
    total = int(m.group(1) or 0) * 60 + int(m.group(2) or 0)
    return total if total > 0 else None
DEFAULT_CONTENT_OUTPUTS = ["blog", "thread", "linkedin", "newsletter", "carousel", "cfp"]
# every output a brief may request; "script" ships only when asked for
CONTENT_OUTPUTS = DEFAULT_CONTENT_OUTPUTS + ["script"]


@dataclass
class ContentBrief:
    """A brief.md: YAML frontmatter plus the paragraph that is the actual brief."""

    body: str
    title_hint: str = ""
    audience: str = "engineers"
    type: str = "finding"
    depth: int = 2
    outputs: list[str] = field(default_factory=lambda: list(DEFAULT_CONTENT_OUTPUTS))
    video_length: str | None = "3m"
    path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def video_length_seconds(self) -> int | None:
        """The video budget in seconds (Galley spends about 140 spoken words a minute); None when video_length is null."""
        return None if self.video_length is None else parse_duration_seconds(self.video_length)

    def validate(self) -> list[str]:
        errs: list[str] = []
        if not self.body.strip():
            errs.append("the brief has no body paragraph")
        if self.type not in CONTENT_TYPES:
            errs.append(f"type must be one of {sorted(CONTENT_TYPES)}, got {self.type!r}")
        if self.depth not in (1, 2):
            errs.append("depth must be 1 or 2")
        bad = [o for o in self.outputs if o not in CONTENT_OUTPUTS]
        if bad:
            errs.append(f"unknown outputs {bad}; valid: {CONTENT_OUTPUTS}")
        if self.video_length is not None and parse_duration_seconds(self.video_length) is None:
            errs.append(f"video_length {self.video_length!r} is not a duration; accepted forms: 3m, 90s, 2m30s, or null")
        return errs


def load_content_brief(path: str | Path) -> ContentBrief:
    p = Path(path)
    meta, body = split_frontmatter(p.read_text(encoding="utf-8"))
    b = ContentBrief(
        body=body,
        title_hint=str(meta.get("title_hint", "") or ""),
        audience=str(meta.get("audience", "engineers")),
        type=str(meta.get("type", "finding")).lower(),
        depth=int(meta.get("depth", 2)),
        outputs=[str(o).lower() for o in (meta.get("outputs") or DEFAULT_CONTENT_OUTPUTS)],
        video_length=None if meta.get("video_length", "3m") is None else str(meta.get("video_length", "3m")),
        path=str(p),
    )
    errs = b.validate()
    if errs:
        raise BriefError(str(p), errs)
    if "blog" not in b.outputs:
        b.outputs.insert(0, "blog")
    return b


# ---- music brief (Underscore) -------------------------------------------

MOODS = ["curious", "focused", "lift", "resolve", "tense", "warm",
         "playful", "serious", "triumphant", "calm"]
HIT_KINDS = ["riser", "soft-hit", "impact", "sparkle"]


@dataclass
class Section:
    start: float
    end: float
    mood: str = "focused"
    energy: float = 0.5
    notes: str = ""

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Hit:
    t: float
    kind: str = "soft-hit"


@dataclass
class Span:
    start: float
    end: float


@dataclass
class MusicBrief:
    """A brief.json: a duration, tempo, key, timed sections with mood and
    energy, optional hit points, optional speech spans."""

    title: str
    duration: float
    bpm: int = 92
    key: str = "D"
    mode: str = "minor"
    style: str = "warm electronic, analog pads, soft percussion"
    seed: int = 1
    target_lufs: float = -14.0
    collection: str = "analog"
    sections: list[Section] = field(default_factory=list)
    hits: list[Hit] = field(default_factory=list)
    speech: list[Span] = field(default_factory=list)

    def validate(self) -> list[str]:
        errs: list[str] = []
        if self.duration <= 0:
            errs.append("duration must be positive")
        if not 40 <= self.bpm <= 200:
            errs.append("bpm out of range 40-200")
        if self.mode not in ("major", "minor"):
            errs.append("mode must be major or minor")
        if not self.sections:
            errs.append("at least one section required")
        t = 0.0
        for i, s in enumerate(self.sections):
            if abs(s.start - t) > 0.05:
                errs.append(f"section {i} starts at {s.start}, expected {t:.2f} (sections must be contiguous)")
            if s.end <= s.start:
                errs.append(f"section {i} has non-positive length")
            if not 0.0 <= s.energy <= 1.0:
                errs.append(f"section {i} energy must be 0..1")
            if s.mood not in MOODS:
                errs.append(f"section {i} mood '{s.mood}' not in {MOODS}")
            t = s.end
        if self.sections and abs(t - self.duration) > 0.05:
            errs.append(f"sections end at {t:.2f}, brief duration is {self.duration}")
        for h in self.hits:
            if not 0 <= h.t <= self.duration:
                errs.append(f"hit at {h.t} outside duration")
            if h.kind not in HIT_KINDS:
                errs.append(f"hit kind '{h.kind}' not in {HIT_KINDS}")
        return errs

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "MusicBrief":
        d = dict(d)
        d["sections"] = [Section(**s) for s in d.get("sections", [])]
        d["hits"] = [Hit(**h) for h in d.get("hits", [])]
        d["speech"] = [Span(**s) for s in d.get("speech", [])]
        return cls(**d)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))


def load_music_brief(path: str | Path) -> MusicBrief:
    p = Path(path)
    b = MusicBrief.from_dict(json.loads(p.read_text()))
    errs = b.validate()
    if errs:
        raise BriefError(str(p), errs)
    return b
