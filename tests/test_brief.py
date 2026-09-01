from underscore.brief import Brief, Section, bpm_for_cuts, sections_from_cuts, default_brief


def test_default_brief_is_valid_and_quantized():
    b = default_brief("t", 60.0)
    assert b.validate() == []
    bars = b.section_bars()
    assert sum(bars) == round(60.0 / b.bar_len)
    assert abs(b.sections[-1].end - 60.0) < 1e-6


def test_validate_catches_gaps_and_bad_values():
    b = Brief(title="x", duration=20, sections=[Section(0, 8, "focused", 0.5), Section(9, 20, "focused", 0.5)])
    errs = b.validate()
    assert any("contiguous" in e for e in errs)
    b2 = Brief(title="x", duration=20, sections=[Section(0, 20, "nonsense", 1.5)])
    errs2 = b2.validate()
    assert any("mood" in e for e in errs2) and any("energy" in e for e in errs2)


def test_bpm_for_cuts_stays_in_range_and_prefers_grid_fit():
    bpm = bpm_for_cuts([10.0, 20.0, 30.0], 70, 130)
    assert 70 <= bpm <= 130
    bar = 4 * 60 / bpm
    assert min(10.0 % bar, bar - 10.0 % bar) < 0.5


def test_sections_from_cuts_are_contiguous_and_cover_duration():
    secs = sections_from_cuts([5, 12, 30, 33, 47], 60.0, min_len=8.0)
    assert secs[0].start == 0.0 and abs(secs[-1].end - 60.0) < 1e-6
    for a, b in zip(secs, secs[1:]):
        assert abs(a.end - b.start) < 1e-6
    assert all(s.duration >= 8.0 - 1e-6 for s in secs)
