import numpy as np
import soundfile as sf

from underscore.brief import default_brief
from underscore.render import render_synth
from underscore.master import master
from underscore.measure import measure, gate


def test_loop_master_is_tileable_and_passes_gate(tmp_path):
    b = default_brief("looper", 24.0)
    r = render_synth(b, tmp_path / "raw.wav")
    info = master(r["raw"], tmp_path / "master.wav", b, loop=True)
    assert info["loop"] and info["loop_crossfade_s"] == 0.5
    assert info["loop_trim_s"] >= 0.5

    y, sr = sf.read(tmp_path / "master.wav", always_2d=True)
    assert abs(len(y) / sr - (24.0 - info["loop_trim_s"])) < 0.05

    m = measure(tmp_path / "master.wav", b, loop=True)
    assert m["loop_seam_db"] <= 6.0
    ok, reasons = gate(m, b, loop_trim_s=info["loop_trim_s"])
    assert ok, reasons

    # tiled joint: the last and first samples must not jump
    joint = abs(float(y[-1].mean()) - float(y[0].mean()))
    assert joint < 0.1


def test_non_loop_master_keeps_fades_and_full_duration(tmp_path):
    b = default_brief("faded", 24.0)
    r = render_synth(b, tmp_path / "raw.wav")
    info = master(r["raw"], tmp_path / "master.wav", b)
    assert not info["loop"]
    y, sr = sf.read(tmp_path / "master.wav", always_2d=True)
    assert abs(len(y) / sr - 24.0) < 0.05
    # fade-out means the tail is much quieter than the middle
    tail = float(np.abs(y[-int(0.2 * sr):]).max())
    mid = float(np.abs(y[len(y) // 2: len(y) // 2 + int(0.2 * sr)]).max())
    assert tail < mid * 0.5


def test_gate_flags_a_bad_seam():
    b = default_brief("seam", 24.0)
    m = {"lufs_integrated": b.target_lufs, "true_peak_dbtp": -1.5,
         "duration_s": 23.5, "sections": [], "energy_correlation": None,
         "loop_seam_db": 12.0}
    ok, reasons = gate(m, b, loop_trim_s=0.5)
    assert not ok and any("seam" in r for r in reasons)
