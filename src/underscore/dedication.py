"""The CC0 dedication travels inside the audio file, not only beside it.

Every WAV the bundle ships gets a Broadcast Wave `bext` chunk (EBU Tech 3285, version 2) and every MP3 gets ID3
tags, each naming the bed, the license URL, and the sha256 of the bundle's manifest.json, so a file separated from
its folder still says what it is, that it is public domain, and which manifest describes it.

WAV: the chunk is written by hand (RIFF is simple and nothing else here should depend on a tag library for it);
an existing bext chunk is replaced. Loudness fields carry the measured integrated loudness, range, and true peak.
MP3: mutagen writes ID3v2.4 (TIT2 title, TPUB publisher, TCOP copyright statement, WCOP license URL, COMM the
dedication text, TXXX:UNDERSCORE_BED and TXXX:MANIFEST_SHA256).
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/"
DEDICATION = "CC0 1.0 Universal: dedicated to the public domain, no attribution required."
ORIGINATOR = "RawlsLab Underscore"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fixed(s: str, n: int) -> bytes:
    b = s.encode("ascii", "replace")[:n]
    return b + b"\x00" * (n - len(b))


def _clamp16(x: float) -> int:
    return max(-32768, min(32767, int(round(x))))


def bext_chunk(bed_id: str, manifest_sha256: str, version: str, measurements: dict | None = None,
               date: str = "", time_: str = "") -> bytes:
    """The bext chunk body (602 bytes plus coding history)."""
    m = measurements or {}
    description = f"{bed_id}. {DEDICATION} {LICENSE_URL} manifest sha256 {manifest_sha256}"
    body = b"".join([
        _fixed(description, 256),
        _fixed(f"{ORIGINATOR} {version}", 32),
        _fixed(bed_id, 32),
        _fixed(date, 10),
        _fixed(time_, 8),
        struct.pack("<II", 0, 0),          # TimeReference low, high
        struct.pack("<H", 2),              # Version 2: loudness fields are valid
        b"\x00" * 64,                      # UMID
        struct.pack("<h", _clamp16(m.get("lufs_integrated", 0.0) * 100) if "lufs_integrated" in m else 0x7FFF),
        struct.pack("<h", _clamp16(m.get("loudness_range_lu", 0.0) * 100) if "loudness_range_lu" in m else 0x7FFF),
        struct.pack("<h", _clamp16(m.get("true_peak_dbtp", 0.0) * 100) if "true_peak_dbtp" in m else 0x7FFF),
        struct.pack("<h", 0x7FFF),         # max momentary loudness: not measured
        struct.pack("<h", 0x7FFF),         # max short-term loudness: not measured
        b"\x00" * 180,                     # reserved
        f"A=PCM,F=48000,W=24,M=stereo,T={ORIGINATOR} {version}\r\n".encode("ascii"),
    ])
    return body


def _chunks(data: bytes) -> list[tuple[bytes, bytes]]:
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise ValueError("not a RIFF/WAVE file")
    out, pos = [], 12
    while pos + 8 <= len(data):
        cid = data[pos:pos + 4]
        size = struct.unpack("<I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + size]
        out.append((cid, body))
        pos += 8 + size + (size & 1)
    return out


def write_bext(path: str | Path, bed_id: str, manifest_sha256: str, version: str,
               measurements: dict | None = None, date: str = "", time_: str = "") -> None:
    """Insert (or replace) the bext chunk right after fmt; keeps every other chunk byte for byte."""
    p = Path(path)
    data = p.read_bytes()
    chunks = [(cid, body) for cid, body in _chunks(data) if cid != b"bext"]
    bext = bext_chunk(bed_id, manifest_sha256, version, measurements, date, time_)
    rebuilt = []
    for cid, body in chunks:
        rebuilt.append((cid, body))
        if cid == b"fmt ":
            rebuilt.append((b"bext", bext))
    if not any(cid == b"bext" for cid, _ in rebuilt):
        rebuilt.insert(0, (b"bext", bext))
    payload = b"WAVE"
    for cid, body in rebuilt:
        payload += cid + struct.pack("<I", len(body)) + body + (b"\x00" if len(body) & 1 else b"")
    p.write_bytes(b"RIFF" + struct.pack("<I", len(payload)) + payload)


def read_bext(path: str | Path) -> dict | None:
    for cid, body in _chunks(Path(path).read_bytes()):
        if cid == b"bext":
            def s(a, b): return body[a:b].split(b"\x00", 1)[0].decode("ascii", "replace")
            lv, lr, tp = struct.unpack("<hhh", body[412:418])
            return {"description": s(0, 256), "originator": s(256, 288), "originator_reference": s(288, 320),
                    "version": struct.unpack("<H", body[346:348])[0],
                    "loudness_value": None if lv == 0x7FFF else lv / 100, "loudness_range": None if lr == 0x7FFF else lr / 100,
                    "max_true_peak": None if tp == 0x7FFF else tp / 100, "coding_history": body[602:].decode("ascii", "replace")}
    return None


def write_id3(path: str | Path, bed_id: str, manifest_sha256: str, version: str) -> None:
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPUB, TCOP, WCOP, COMM, TXXX
    try:
        tags = ID3(str(path))
    except ID3NoHeaderError:
        tags = ID3()
    tags.delall("TIT2"); tags.delall("TPUB"); tags.delall("TCOP"); tags.delall("WCOP"); tags.delall("COMM"); tags.delall("TXXX")
    tags.add(TIT2(encoding=3, text=bed_id))
    tags.add(TPUB(encoding=3, text=ORIGINATOR))
    tags.add(TCOP(encoding=3, text=f"{DEDICATION} {LICENSE_URL}"))
    tags.add(WCOP(url=LICENSE_URL))
    tags.add(COMM(encoding=3, lang="eng", desc="license", text=f"{DEDICATION} {LICENSE_URL}"))
    tags.add(TXXX(encoding=3, desc="UNDERSCORE_BED", text=bed_id))
    tags.add(TXXX(encoding=3, desc="MANIFEST_SHA256", text=manifest_sha256))
    tags.add(TXXX(encoding=3, desc="ENCODER", text=f"{ORIGINATOR} {version}"))
    tags.save(str(path), v2_version=4)


def read_id3(path: str | Path) -> dict:
    from mutagen.id3 import ID3
    t = ID3(str(path))
    out = {"title": str(t.get("TIT2", "")), "publisher": str(t.get("TPUB", "")), "copyright": str(t.get("TCOP", "")),
           "license_url": t["WCOP"].url if "WCOP" in t else None}
    for fr in t.getall("TXXX"):
        out[fr.desc] = str(fr)
    return out


def tag_bundle(outdir: str | Path, bed_id: str, files: dict, version: str, measurements: dict | None,
               generated_at: str = "") -> str:
    """Tag every audio file the manifest lists; returns the manifest's sha256 (computed first, so the tag
    can name the manifest that describes the file). manifest.json itself stays untouched."""
    out = Path(outdir)
    msha = sha256_file(out / "manifest.json")
    date, time_ = "", ""
    if generated_at and len(generated_at) >= 19:
        date, time_ = generated_at[:10], generated_at[11:19]
    for name in files.values():
        p = out / name
        if not p.exists():
            continue
        if p.suffix.lower() == ".wav":
            write_bext(p, bed_id, msha, version, measurements, date, time_)
        elif p.suffix.lower() == ".mp3":
            write_id3(p, bed_id, msha, version)
    return msha
