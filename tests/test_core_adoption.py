"""Underscore runs on the family's shared brief schema and gate report, vendored from rawlslab-core."""
import json
from pathlib import Path

import pytest

from underscore._vendor.brief import MusicBrief
from underscore.brief import Brief, BriefError, default_brief
from underscore.export import gate_report


def test_brief_is_the_shared_music_brief_plus_timing(tmp_path):
    b = default_brief("adopt", 30.0)
    assert isinstance(b, MusicBrief) and isinstance(b, Brief)
    assert b.bar_len == 4 * 60.0 / b.bpm  # the arithmetic stays in Underscore
    b.save(tmp_path / "b.json")
    again = Brief.load(tmp_path / "b.json")
    assert type(again) is Brief and again.to_dict() == b.to_dict()


def test_load_raises_every_problem_at_once(tmp_path):
    d = default_brief("bad", 30.0).to_dict()
    d["bpm"] = 500; d["mode"] = "dorian"; d["sections"][0]["mood"] = "nope"
    (tmp_path / "b.json").write_text(json.dumps(d))
    with pytest.raises(BriefError) as e:
        Brief.load(tmp_path / "b.json")
    assert len(e.value.errors) == 3 and e.value.path.endswith("b.json")


def test_gate_report_has_the_shared_shape():
    clean = gate_report([], {"lufs_integrated": -14.0, "sections": [1]})
    assert clean.passed and clean.exit_code == 0
    d = clean.to_dict()
    assert d["passed"] is True and d["measure"]["errors"] == [] and d["measure"]["stats"] == {"lufs_integrated": -14.0}
    held = gate_report(["too quiet", "too long"], {})
    assert not held.passed and held.exit_code == 2
    assert [e["msg"] for e in held.to_dict()["measure"]["errors"]] == ["too quiet", "too long"]


def test_bundle_carries_gates_json(tmp_path):
    from underscore.cli import main
    b = default_brief("gated", 12.0); b.save(tmp_path / "b.json")
    main(["score", "--brief", str(tmp_path / "b.json"), "--engine", "synth", "--workdir", str(tmp_path / "w"), "-o", str(tmp_path / "o")])
    g = json.loads((tmp_path / "o" / "gates.json").read_text())
    assert g["passed"] is True and "measure" in g and g["measure"]["stats"]["lufs_integrated"] < 0
