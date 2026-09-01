"""The four e2e gaps from the Sep 1 pipeline test (12 speech map, 13 master -o, 14 backend default, 15 receipts)."""
import json
import os
from pathlib import Path

from underscore.analyze import speech_map
from underscore.brief import Span, default_brief
from underscore.cli import default_llm, resolve_out
from underscore.export import export_bundle
from underscore.master import master
from underscore.render import render_synth


def _contiguous_transcript(n: int, seg: float = 5.0):
    return [{"start": i * seg, "end": (i + 1) * seg, "text": "..."} for i in range(n)]


def test_12_vad_pauses_survive_a_contiguous_transcript():
    vad = [Span(0.0, 12.0), Span(13.5, 40.0), Span(41.0, 88.0), Span(90.0, 180.0)]
    spans, source = speech_map(vad, _contiguous_transcript(36))   # 36 x 5 s = one unbroken talk
    assert source == "vad+transcript" and len(spans) == 4        # not one 0..180 span
    assert spans[1].start == 13.5


def test_12_room_noise_outside_the_transcript_is_dropped():
    vad = [Span(0.0, 10.0), Span(120.0, 125.0)]                    # the second is a chair scrape after the talk
    spans, _ = speech_map(vad, [{"start": 0.0, "end": 10.0, "text": "hi"}])
    assert spans == [Span(0.0, 10.0)]


def test_12_fallbacks():
    assert speech_map([Span(1, 2)], []) == ([Span(1, 2)], "vad")
    spans, source = speech_map([], _contiguous_transcript(3))
    assert source == "transcript" and spans == [Span(0.0, 15.0)]


def test_13_master_accepts_a_directory(tmp_path: Path):
    b = default_brief("gap13", 8.0)
    r = render_synth(b, tmp_path / "raw.wav")
    out = resolve_out(str(tmp_path / "bundle"), "gap13.master.wav")
    assert out == tmp_path / "bundle" / "gap13.master.wav" and out.parent.is_dir()
    info = master(r["raw"], out, b)
    assert Path(info["master"]).exists()
    assert resolve_out(str(tmp_path / "x.wav"), "d.wav") == tmp_path / "x.wav"
    assert resolve_out(None, "d.wav") == Path("d.wav")


def test_14_video_mode_uses_the_configured_backend(monkeypatch):
    for v in ("UNDERSCORE_CLI", "UNDERSCORE_API_URL", "UNDERSCORE_LOCAL"):
        monkeypatch.delenv(v, raising=False)
    assert default_llm(None) is None
    monkeypatch.setenv("UNDERSCORE_CLI", "some-agent")
    assert default_llm(None) == "cli"
    assert default_llm("local") == "local"
    monkeypatch.delenv("UNDERSCORE_CLI")
    monkeypatch.setenv("UNDERSCORE_API_URL", "http://x")
    assert default_llm(None) == "api"


def test_15_manifest_records_the_briefs_provenance(tmp_path: Path):
    b = default_brief("gap15", 8.0)
    r = render_synth(b, tmp_path / "raw.wav")
    m = master(r["raw"], tmp_path / "m.wav", b)
    info = {"source": "model", "analyze_backend": "cli", "analyze_model": None, "analyze_seconds": 12.3, "speech_source": "vad+transcript"}
    man = export_bundle(tmp_path / "out", b, None, r, m, None, {"lufs_integrated": -14.0}, True, [], {}, brief_info=info, compose_backend=None)
    assert man["brief"] == {"source": "model", "analyze_backend": "cli", "analyze_model": None, "analyze_seconds": 12.3, "speech_source": "vad+transcript"}
    assert man["compose_backend"] is None
    on_disk = json.loads((tmp_path / "out" / "manifest.json").read_text())
    assert on_disk["brief"]["source"] == "model"
    man2 = export_bundle(tmp_path / "out2", b, None, r, m, None, {}, True, [], {})
    assert man2["brief"]["source"] == "file"
