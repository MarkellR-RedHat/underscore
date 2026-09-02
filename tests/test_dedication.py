"""The CC0 dedication is inside the files: bext in every WAV, ID3 in the MP3, both naming the manifest."""
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from underscore.dedication import write_bext, read_bext, write_id3, read_id3, tag_bundle, sha256_file, LICENSE_URL


def _wav(path, seconds=1.0, sr=48000):
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    sf.write(path, np.stack([np.sin(2 * np.pi * 220 * t) * 0.3] * 2, axis=1), sr, subtype="PCM_24")


def test_bext_round_trips_and_keeps_the_audio(tmp_path):
    p = tmp_path / "a.wav"; _wav(p)
    before, sr = sf.read(p)
    write_bext(p, "demo-cmaj-60s-1", "ab" * 32, "0.1.0rc1", {"lufs_integrated": -14.03, "loudness_range_lu": 3.2, "true_peak_dbtp": -1.5},
               "2026-09-02", "01:02:03")
    write_bext(p, "demo-cmaj-60s-1", "cd" * 32, "0.1.0rc1")  # replacing, not stacking
    after, sr2 = sf.read(p)
    assert sr == sr2 and np.array_equal(before, after)
    b = read_bext(p)
    assert b["originator_reference"] == "demo-cmaj-60s-1" and b["originator"].startswith("RawlsLab Underscore")
    assert LICENSE_URL in b["description"] and ("cd" * 32) in b["description"] and ("ab" * 32) not in b["description"]
    assert b["version"] == 2 and b["loudness_value"] is None  # second write carried no measurements
    write_bext(p, "demo-cmaj-60s-1", "cd" * 32, "0.1.0rc1", {"lufs_integrated": -14.03, "loudness_range_lu": 3.2, "true_peak_dbtp": -1.5})
    b = read_bext(p)
    assert b["loudness_value"] == -14.03 and b["loudness_range"] == 3.2 and b["max_true_peak"] == -1.5
    assert sum(1 for c in Path(p).read_bytes().split(b"bext") if c) >= 1


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg encodes the mp3")
def test_id3_round_trips(tmp_path):
    w = tmp_path / "a.wav"; _wav(w)
    m = tmp_path / "a.mp3"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-codec:a", "libmp3lame", "-b:a", "128k", str(m)], check=True)
    write_id3(m, "demo-cmaj-60s-1", "ef" * 32, "0.1.0rc1")
    t = read_id3(m)
    assert t["title"] == "demo-cmaj-60s-1" and t["license_url"] == LICENSE_URL
    assert t["UNDERSCORE_BED"] == "demo-cmaj-60s-1" and t["MANIFEST_SHA256"] == "ef" * 32 and "CC0" in t["copyright"]


def test_tag_bundle_names_the_manifest_it_sits_beside(tmp_path):
    (tmp_path / "x.master.wav").write_bytes(b"")
    _wav(tmp_path / "x.master.wav"); _wav(tmp_path / "x.stem-pads.wav")
    manifest = {"seed": 1, "files": {"master": "x.master.wav", "stem_pads": "x.stem-pads.wav", "source": "x.rb"}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "x.rb").write_text("play 60")
    msha = tag_bundle(tmp_path, "x", manifest["files"], "0.1.0rc1", {"lufs_integrated": -14.0}, "2026-09-02T00:00:00Z")
    assert msha == sha256_file(tmp_path / "manifest.json")  # manifest untouched by the tagging
    for f in ("x.master.wav", "x.stem-pads.wav"):
        assert msha in read_bext(tmp_path / f)["description"]
    assert (tmp_path / "x.rb").read_text() == "play 60"
