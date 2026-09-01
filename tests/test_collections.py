from underscore.collections import COLLECTIONS, get
from underscore.brief import default_brief
from underscore.compose import build_prompt


def test_picks_are_deterministic_and_within_lists():
    for name, c in COLLECTIONS.items():
        a, b = c.pick(1109), c.pick(1109)
        assert a == b
        assert a["lead"] in c.leads and a["pad"] in c.pads and a["bass"] in c.basses
        assert a["kick"] in c.kicks and a["hat"] in c.hats and a["accent"] in c.accents


def test_prompt_carries_collection_block_and_assigned_instruments():
    b = default_brief("t", 30.0)
    b.collection = "pulse"; b.seed = 42
    p = build_prompt(b)
    pick = get("pulse").pick(42)
    assert "## Collection: pulse" in p
    assert pick["lead"] in p and pick["kick"] in p
    assert "Allowed synths:" in p and "Allowed samples:" in p


def test_unknown_collection_raises():
    import pytest
    with pytest.raises(KeyError):
        get("nope")
