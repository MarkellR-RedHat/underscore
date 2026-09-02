"""The CLI's exit contract: a missing backend is one line and exit 2; --ship-anyway keeps a failed bed shippable."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from underscore import cli
from underscore.brief import default_brief

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "brief.example.json"


def test_compose_without_a_backend_is_one_line_and_exit_2(tmp_path):
    env = {k: v for k, v in os.environ.items() if not k.startswith("UNDERSCORE_")}
    env["PATH"] = os.environ.get("PATH", "")
    r = subprocess.run([sys.executable, "-m", "underscore.cli", "compose", str(EXAMPLE), "-o", str(tmp_path / "x.rb")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2
    assert "Traceback" not in r.stderr
    lines = [ln for ln in r.stderr.splitlines() if ln.strip()]
    assert len(lines) == 1 and lines[0].startswith("compose: set UNDERSCORE_CLI")


def test_score_with_sonicpi_engine_and_no_backend_is_one_line_and_exit_2(tmp_path, monkeypatch):
    env = {k: v for k, v in os.environ.items() if not k.startswith("UNDERSCORE_")}
    env["PATH"] = os.environ.get("PATH", "")
    r = subprocess.run([sys.executable, "-m", "underscore.cli", "score", "--brief", str(EXAMPLE), "--engine", "sonicpi",
                        "--workdir", str(tmp_path / "w"), "-o", str(tmp_path / "o")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 2 and "Traceback" not in r.stderr
    assert [ln for ln in r.stderr.splitlines() if ln.startswith("compose: set UNDERSCORE_CLI")]


def _forced_fail(monkeypatch):
    # cli imports gate from measure at call time, so patching the measure module is what reaches score
    import underscore.measure as measure_mod
    monkeypatch.setattr(measure_mod, "gate", lambda m, brief, **kw: (False, ["forced by the test"]))


def test_failed_gate_exits_2_without_ship_anyway(tmp_path, monkeypatch):
    b = default_brief("shipcheck", 12.0); b.save(tmp_path / "b.json")
    _forced_fail(monkeypatch)
    with pytest.raises(SystemExit) as e:
        cli.main(["score", "--brief", str(tmp_path / "b.json"), "--engine", "synth",
                  "--workdir", str(tmp_path / "w"), "-o", str(tmp_path / "o")])
    assert e.value.code == 2
    m = json.loads((tmp_path / "o" / "manifest.json").read_text())
    assert m["gate_passed"] is False and m["gate_reasons"] == ["forced by the test"]


def test_ship_anyway_keeps_the_bundle_and_exits_0(tmp_path, monkeypatch):
    b = default_brief("shipcheck", 12.0); b.save(tmp_path / "b.json")
    _forced_fail(monkeypatch)
    cli.main(["score", "--brief", str(tmp_path / "b.json"), "--engine", "synth", "--ship-anyway",
              "--workdir", str(tmp_path / "w"), "-o", str(tmp_path / "o")])  # no SystemExit
    m = json.loads((tmp_path / "o" / "manifest.json").read_text())
    assert m["gate_passed"] is False and (tmp_path / "o" / "shipcheck.master.wav").exists()
