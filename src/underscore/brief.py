"""The brief: the only thing the generator ever sees.

A brief is a duration, a tempo, a key, a list of timed sections with a mood
and an energy, optional hit points, and optional speech spans. Brief mode
means a human wrote it. Video mode means analyze.py derived it. The generator
does not care which.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field, asdict
from pathlib import Path

MOODS = ["curious", "focused", "lift", "resolve", "tense", "warm",
         "playful", "serious", "triumphant", "calm"]
HIT_KINDS = ["riser", "soft-hit", "impact", "sparkle"]
BEATS_PER_BAR = 4


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
class Brief:
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

    # ---- timing helpers -------------------------------------------------
    @property
    def beat_len(self) -> float:
        return 60.0 / self.bpm

    @property
    def bar_len(self) -> float:
        return BEATS_PER_BAR * self.beat_len

    def seconds_to_beats(self, t: float) -> float:
        return t / self.beat_len

    def section_bars(self) -> list[int]:
        """Whole bars per section, summing to the brief's bar count."""
        total_bars = max(1, round(self.duration / self.bar_len))
        raw = [s.duration / self.bar_len for s in self.sections]
        bars = [max(1, round(r)) for r in raw]
        # reconcile rounding drift against the total
        drift = total_bars - sum(bars)
        i = 0
        while drift != 0 and self.sections:
            j = i % len(bars)
            if drift > 0:
                bars[j] += 1; drift -= 1
            elif bars[j] > 1:
                bars[j] -= 1; drift += 1
            i += 1
            if i > 10_000:
                break
        return bars

    def quantize_to_bars(self) -> "Brief":
        """Snap section boundaries to the bar grid so changes land on bars."""
        if not self.sections:
            return self
        bars = self.section_bars()
        t = 0.0
        for s, b in zip(self.sections, bars):
            s.start = round(t, 3)
            t += b * self.bar_len
            s.end = round(t, 3)
        self.sections[-1].end = round(self.duration, 3)
        for h in self.hits:
            h.t = round(round(h.t / self.bar_len) * self.bar_len, 3)
        return self

    # ---- validation -----------------------------------------------------
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

    # ---- io -------------------------------------------------------------
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Brief":
        d = dict(d)
        d["sections"] = [Section(**s) for s in d.get("sections", [])]
        d["hits"] = [Hit(**h) for h in d.get("hits", [])]
        d["speech"] = [Span(**s) for s in d.get("speech", [])]
        return cls(**d)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str | Path) -> "Brief":
        return cls.from_dict(json.loads(Path(path).read_text()))


# ---- derivation helpers (used by analyze.py and init) -------------------

def bpm_for_cuts(cuts: list[float], lo: int = 70, hi: int = 130) -> int:
    """Pick the tempo whose bar grid lands closest to the scene cuts."""
    if not cuts:
        return 92
    best, best_err = 92, math.inf
    for bpm in range(lo, hi + 1):
        bar = BEATS_PER_BAR * 60.0 / bpm
        err = sum(min(c % bar, bar - (c % bar)) for c in cuts) / len(cuts)
        if err < best_err - 1e-9:
            best, best_err = bpm, err
    return best


def sections_from_cuts(cuts: list[float], duration: float, min_len: float = 8.0) -> list[Section]:
    """Merge scene cuts into musical sections no shorter than min_len."""
    bounds = [0.0] + [c for c in sorted(cuts) if 0 < c < duration] + [duration]
    merged = [bounds[0]]
    for b in bounds[1:]:
        if b - merged[-1] >= min_len:
            merged.append(b)
    if merged[-1] < duration:
        merged[-1] = duration
    sections: list[Section] = []
    n = len(merged) - 1
    for i in range(n):
        start, end = merged[i], merged[i + 1]
        # cut density inside the span drives energy; opening/closing sit lower
        inside = [c for c in cuts if start < c < end]
        density = len(inside) / max(1.0, (end - start) / 10.0)
        energy = max(0.25, min(0.85, 0.35 + 0.15 * density))
        if i == 0:
            mood, energy = "curious", max(0.45, min(energy, 0.55))
        elif i == n - 1:
            mood, energy = "resolve", min(energy, 0.35)
        elif energy > 0.65:
            mood = "lift"
        else:
            mood = "focused"
        sections.append(Section(start=round(start, 3), end=round(end, 3), mood=mood, energy=round(energy, 2)))
    return sections


def default_brief(title: str, duration: float = 60.0) -> Brief:
    b = Brief(title=title, duration=duration, sections=[
        Section(0.0, duration * 0.15, "curious", 0.5, "open with pulse, pad and light ticks"),
        Section(duration * 0.15, duration * 0.7, "focused", 0.5, "main body, steady pulse"),
        Section(duration * 0.7, duration * 0.88, "lift", 0.7, "lift, add motif"),
        Section(duration * 0.88, duration, "resolve", 0.3, "outro, strip back"),
    ])
    return b.quantize_to_bars()
