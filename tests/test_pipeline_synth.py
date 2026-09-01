import json
from pathlib import Path

from underscore.brief import default_brief, Span
from underscore.render import render_synth
from underscore.master import master, duck
from underscore.measure import measure, gate
from underscore.export import export_bundle


def test_synth_pipeline_passes_gate(tmp_path: Path):
    b = default_brief("unit", 24.0)
    b.speech = [Span(2.0, 10.0)]
    r = render_synth(b, tmp_path / "raw.wav")
    assert set(r["stems"]) == {"pads", "bass", "drums", "motif"}
    m = master(r["raw"], tmp_path / "master.wav", b)
    d = duck(m["master"], tmp_path / "ducked.wav", b.speech)
    meas = measure(m["master"], b)
    ok, reasons = gate(meas, b)
    assert ok, reasons
    assert abs(meas["lufs_integrated"] - b.target_lufs) <= 1.0
    assert meas["true_peak_dbtp"] <= -1.0
    man = export_bundle(tmp_path / "bundle", b, None, r, m, d, meas, ok, reasons)
    assert man["gate_passed"] and man["license"] == "CC0-1.0"
    assert (tmp_path / "bundle" / "markers.csv").exists()
    assert json.loads((tmp_path / "bundle" / "manifest.json").read_text())["seed"] == b.seed
