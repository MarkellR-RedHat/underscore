from underscore.brief import default_brief, Hit
from underscore.compose import harness, validate_code, extract_code


GOOD = """
define :sec_0 do |bars|
  bars.times do
    synth :prophet, note: :d3
    sleep 4
  end
end
define :sec_1 do |bars|
  bars.times { sleep 4 }
end
define :sec_2 do |bars|
  bars.times { sleep 4 }
end
define :sec_3 do |bars|
  bars.times { sleep 4 }
end
define :hit_riser do
  in_thread do
    synth :sine
  end
end
"""


def test_validate_accepts_good_code_and_rejects_bad():
    b = default_brief("t", 40.0)
    b.hits = [Hit(20.0, "riser")]
    assert validate_code(GOOD, b) == []
    bad = GOOD.replace("define :sec_2", "define :sec_9") + "\nlive_loop :x do\n sleep 1\nend\n"
    errs = validate_code(bad, b)
    assert any("sec_2" in e for e in errs) and any("live_loop" in e for e in errs)


def test_harness_sequences_sections_and_holds_run_open():
    b = default_brief("t", 40.0)
    b.hits = [Hit(20.0, "riser")]
    prog = harness(b, GOOD)
    assert f"use_bpm {b.bpm}" in prog and f"use_random_seed {b.seed}" in prog
    for i, bars in enumerate(b.section_bars()):
        assert f"sec_{i} {bars}" in prog
    assert "hit_riser" in prog and "hold for the recorder tail" in prog


def test_extract_code_pulls_fenced_block():
    assert extract_code("text\n```ruby\nsleep 1\n```\nmore").strip() == "sleep 1"


def test_validate_rejects_core_name_and_unprefixed_helpers():
    b = default_brief("t", 40.0)
    code = GOOD + "\ndefine :tick do\n  1\nend\ndefine :pad do\n  2\nend\ndefine :us_ok do\n  3\nend\n"
    errs = validate_code(code, b)
    assert any(":tick" in e and "core" in e for e in errs)
    assert any(":pad" in e and "us_" in e for e in errs)
    assert not any("us_ok" in e for e in errs)
