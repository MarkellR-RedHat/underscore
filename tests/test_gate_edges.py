import numpy as np
import soundfile as sf

from underscore.brief import Brief, Section, Span, default_brief
from underscore.master import master, duck
from underscore.measure import measure, gate
from underscore.render import render_synth, SR


def _two_section_brief(title: str, dur: float = 20.0) -> Brief:
    b = default_brief(title, dur)
    b.sections = [Section(0.0, dur / 2, "calm", 0.4), Section(dur / 2, dur, "lift", 0.7)]
    return b


def test_energy_correlation_is_none_below_three_sections(tmp_path):
    b = _two_section_brief("twosec")
    r = render_synth(b, tmp_path / "raw.wav")
    m = measure(r["raw"], b)
    assert m["energy_correlation"] is None
    # the energy check silently does not apply; the gate must still work
    gate(m, b)


def test_gate_catches_a_silent_section(tmp_path):
    b = _two_section_brief("halfsilent")
    n = int(b.duration * SR)
    y = np.zeros((n, 2), dtype=np.float32)
    t = np.arange(n // 2) / SR
    tone = (0.25 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    y[: n // 2, 0] = tone
    y[: n // 2, 1] = tone
    wav = tmp_path / "half.wav"
    sf.write(wav, y, SR, subtype="PCM_24")
    m = measure(wav, b)
    ok, reasons = gate(m, b)
    assert not ok
    assert any("silent" in r for r in reasons)


def test_ducked_variant_is_quieter_under_speech(tmp_path):
    b = default_brief("ducked", 24.0)
    b.speech = [Span(6.0, 14.0)]
    r = render_synth(b, tmp_path / "raw.wav")
    info = master(r["raw"], tmp_path / "master.wav", b)
    out = duck(info["master"], tmp_path / "ducked.wav", b.speech)
    ym, sr = sf.read(info["master"], always_2d=True)
    yd, _ = sf.read(out, always_2d=True)
    a, c = int(8.0 * sr), int(12.0 * sr)
    rms = lambda x: float(np.sqrt(np.mean(x ** 2)))  # noqa: E731
    assert rms(yd[a:c]) < rms(ym[a:c]) * 0.3


def test_reference_match_cleans_up_and_survives_bad_reference(tmp_path):
    b = default_brief("matched", 20.0)
    r = render_synth(b, tmp_path / "raw.wav")
    ref = tmp_path / "ref.wav"
    t = np.arange(int(20.0 * SR)) / SR
    tone = (0.3 * np.sin(2 * np.pi * 330 * t)).astype(np.float32)
    sf.write(ref, np.stack([tone, tone], axis=1), SR, subtype="PCM_24")
    info = master(r["raw"], tmp_path / "master.wav", b, reference=ref)
    # matched or skipped, the temp files never survive
    assert not (tmp_path / "master.pre.wav").exists()
    assert not (tmp_path / "master.matched.wav").exists()
    assert (tmp_path / "master.wav").exists()

    bad = tmp_path / "bad-ref.wav"
    bad.write_bytes(b"not a wav at all")
    info2 = master(r["raw"], tmp_path / "master2.wav", b, reference=bad)
    assert info2["reference_matched"] is False
    assert (tmp_path / "master2.wav").exists()
    assert not (tmp_path / "master2.pre.wav").exists()
    assert not (tmp_path / "master2.matched.wav").exists()
