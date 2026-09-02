"""The brief: the only thing the generator ever sees.

A brief is a duration, a tempo, a key, a list of timed sections with a mood
and an energy, optional hit points, and optional speech spans. Brief mode
means a human wrote it. Video mode means analyze.py derived it. The generator
does not care which.

The schema (fields, validation, JSON in and out) is the family's shared
MusicBrief from rawlslab-core, vendored under _vendor/. What lives here is
the music arithmetic: beats, bars, quantizing section boundaries to the bar
grid, and the helpers that derive a brief from scene cuts.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from ._vendor.brief import BriefError, Hit, MusicBrief, Section, Span, MOODS, HIT_KINDS  # noqa: F401

BEATS_PER_BAR = 4


@dataclass
class Brief(MusicBrief):
    """MusicBrief plus the timing helpers the composer and renderer need."""

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

    @classmethod
    def load(cls, path: str | Path) -> "Brief":
        """Read and validate; a bad brief raises BriefError carrying every problem."""
        b = cls.from_dict(json.loads(Path(path).read_text()))
        errs = b.validate()
        if errs:
            raise BriefError(str(path), errs)
        return b


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
