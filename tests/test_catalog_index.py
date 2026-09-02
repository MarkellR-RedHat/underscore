"""The catalog index follows the family's bed catalog contract and keeps the Underscore record."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "build_catalog_index.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_catalog_index", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_bed(root: Path, collection: str, title: str, passed: bool = True, loop: bool = False,
              sections=((0.0, 10.0, 0.4), (10.0, 30.0, 0.7))) -> bytes:
    d = root / collection / title
    d.mkdir(parents=True)
    wav = b"RIFF" + title.encode() * 50
    (d / f"{title}.master.wav").write_bytes(wav)
    (d / "brief.json").write_text(json.dumps({
        "title": title, "duration": 30.0, "bpm": 100, "key": "C", "mode": "major", "seed": 7,
        "collection": collection,
        "sections": [{"start": a, "end": b, "mood": "calm", "energy": e} for a, b, e in sections],
    }))
    (d / "manifest.json").write_text(json.dumps({
        "gate_passed": passed, "loop": loop, "engine": "synth", "license": "CC0-1.0",
        "measurements": {"lufs_integrated": -14.1, "true_peak_dbtp": -1.5, "loudness_range_lu": 3.0,
                         "energy_correlation": 0.81234, "spectral_centroid_hz": 1234.56},
        "files": {"master": f"{title}.master.wav", "preview": f"{title}.preview.mp3", "source": f"{title}.rb",
                  "markers_csv": "markers.csv", "markers_edl": "markers.edl"},
    }))
    return wav


def test_index_carries_the_contract_fields_and_the_underscore_record(tmp_path):
    mod = _load()
    wav = _fake_bed(tmp_path, "analog", "demo-cmaj-30s-1")
    _fake_bed(tmp_path, "glass", "launch-cmaj-30s-2", passed=False)
    _fake_bed(tmp_path, "pulse", "keynote-cmaj-30s-3", loop=True, sections=((0.0, 30.0, 0.9),))
    entries = [mod.bed_entry(mp, flat=False) for mp in sorted(tmp_path.glob("*/*/manifest.json"))]
    entries = [e for e in entries if e]
    assert [e["id"] for e in entries] == ["demo-cmaj-30s-1", "keynote-cmaj-30s-3"]  # the failed bed is out
    e = entries[0]
    assert e["file"] == "analog/demo-cmaj-30s-1/demo-cmaj-30s-1.master.wav"
    assert e["sha256"] == hashlib.sha256(wav).hexdigest()
    assert e["mood"] == "demo" and e["profile"] == "demo"
    assert e["energy"] == 0.6  # (10 * 0.4 + 20 * 0.7) / 30, weighted by section length
    assert e["loop_safe"] is False and entries[1]["loop_safe"] is True
    assert entries[1]["energy"] == 0.9
    assert e["license"] == "CC0-1.0" and e["duration_s"] == 30.0 and e["bpm"] == 100
    # the fuller record stays alongside the contract fields
    assert e["collection"] == "analog" and e["key"] == "C" and e["seed"] == 7
    assert e["energy_correlation"] == 0.8123 and e["spectral_centroid_hz"] == 1234.6
    assert e["files"]["source"] == "demo-cmaj-30s-1.rb"
    assert e["recommended_for"] == [] and entries[1]["recommended_for"] == []


def test_recommended_for_video_is_ember_or_playful(tmp_path):
    mod = _load()
    assert mod.recommended_for("ember", "deep-dive") == ["video"]
    assert mod.recommended_for("glass", "playful") == ["video"]
    assert mod.recommended_for("ember", "playful") == ["video"]
    assert mod.recommended_for("glass", "keynote") == []
    _fake_bed(tmp_path, "ember", "keynote-cmaj-30s-9")
    e = mod.bed_entry(tmp_path / "ember" / "keynote-cmaj-30s-9" / "manifest.json", flat=True)
    assert e["recommended_for"] == ["video"]


def test_flat_layout_and_top_level_version(tmp_path):
    _fake_bed(tmp_path, "analog", "demo-cmaj-30s-1")
    out = tmp_path / "release.json"
    subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(tmp_path), "--flat", "-o", str(out)],
                   check=True, capture_output=True)
    index = json.loads(out.read_text())
    assert index["version"] == 1 and index["count"] == 1 and index["license"] == "CC0-1.0"
    assert index["beds"][0]["file"] == "demo-cmaj-30s-1.master.wav"
    subprocess.run([sys.executable, str(SCRIPT), "--catalog", str(tmp_path)], check=True, capture_output=True)
    tree = json.loads((tmp_path / "catalog.json").read_text())
    assert tree["beds"][0]["file"] == "analog/demo-cmaj-30s-1/demo-cmaj-30s-1.master.wav"
