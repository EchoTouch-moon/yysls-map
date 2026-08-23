#!/usr/bin/env python3
"""
nex004a_normalizer.py — NEX-004A / H-NEX-004A: Raw Narrative Observation Normalizer (schema v2).

Purpose: without decoding the private Lua instruction serialization
(H-NEX-003T = INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED), convert
statically observable native narrative metadata into reproducible,
traceable, non-semanticized structural records (RawNarrativeObservation).

Hardening (H-NEX-004A):
  * provenance freeze: extractor_commit MUST resolve to the exact committed
    extractor; artifact generation FAILS if game_version or commit is missing.
  * extractor_source_sha256 recorded (double check on extractor identity).
  * the tool writes its own UTF-8 output (--output), ensure_ascii=False,
    LF newlines, then round-trip validates the written file.
  * MAX_LOCATOR_BYTES = 64 is enforced on UTF-8 BYTES (not characters),
    with a UTF-8-safe trim helper + ASCII/CJK/boundary regressions.
  * taxonomy fixed per evidence semantics (TASK_REF/REGION_REF/TEXT_LOOKUP_KEY/
    TEXT_REF/FIELD_KEY/SCRIPT_FAMILY/CHARACTER_TOKEN candidates).
  * source observation v2: source_status / source_locator / source_segments /
    source_reconstruction / source_truncated — SEGMENTED_PARTIAL locator is a
    lossy PRINTABLE_RUN_JOIN candidate, never presented as observed bytes.
  * hardened guards: mpkinfo exact size (8+c*20+16), entry read exactly 20B,
    Lua version 0x54 / format 0 / LUAC_DATA exact / size fields 4/8/8.

Principles: observations only — no canonical writes, no constant index, no
owning proto, no bulk string dump / full dialogue / full script.

Usage:
    python nex004a_normalizer.py --selftest
    python nex004a_normalizer.py <archive_dir> <archive> <mpkinfo> <entry_index>
                                  --output path.json [--game-version V] [--commit C]
"""
import argparse
import hashlib
import json
import os
import struct
import subprocess
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
MAX_LOCATOR_BYTES = 64
SCHEMA_VERSION = "raw-narrative-observation-2"

# (target, pattern_kind) — taxonomy per H-NEX-004A evidence semantics.
TARGETS = [
    ("dq_610900", "TASK_REF_CANDIDATE"),
    ("EXPANSION_QINGHE", "REGION_REF_CANDIDATE"),
    ("storyline_data", "SCRIPT_FAMILY_CANDIDATE"),
    ("MSD_ST", "SCRIPT_FAMILY_CANDIDATE"),
    ("NodeGraphData", "FIELD_KEY_CANDIDATE"),
    ("TextByNo", "TEXT_LOOKUP_KEY_CANDIDATE"),
    ("70276", "TEXT_REF_CANDIDATE"),
    ("江晏", "CHARACTER_TOKEN"),
]

WARN_BASE = [
    "INSTRUCTION_SERIALIZATION_VARIANT",
    "CONSTANT_OWNERSHIP_UNKNOWN",
    "PROTO_OWNERSHIP_UNKNOWN",
    "SEMANTIC_ROLE_UNVERIFIED",
]


def locator(value, cap=MAX_LOCATOR_BYTES):
    """UTF-8-safe byte cap: encode -> cap at `cap` bytes -> trim an incomplete
    trailing codepoint -> decode.  Returns (capped_str, truncated_bool)."""
    b = value.encode("utf-8")
    if len(b) <= cap:
        return value, False
    b = b[:cap]
    while b and (b[-1] & 0xC0) == 0x80:  # cut continuation byte of a split codepoint
        b = b[:-1]
    if b and b[-1] >= 0xC0:              # cut a dangling lead byte
        b = b[:-1]
    return b.decode("utf-8", errors="replace"), True


def sha256_stream(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_unsigned(data, off):
    """Official Lua 5.4 loadUnsigned (MSB-first 7-bit groups)."""
    x = 0
    i = 0
    while i < 8:
        if off + i >= len(data):
            return None, None
        b = data[off + i]
        x = (x << 7) | (b & 0x7F)
        i += 1
        if b & 0x80:
            return x, i
    return x, i


def printable_runs(blk):
    """Non-empty runs of printable ASCII bytes (32..126), as (offset, bytes)."""
    runs = []
    cur = None
    start = None
    for i, b in enumerate(blk):
        if 32 <= b <= 126:
            if cur is None:
                cur = bytearray()
                start = i
            cur.append(b)
        else:
            if cur is not None:
                runs.append((start, bytes(cur)))
                cur = None
    if cur is not None:
        runs.append((start, bytes(cur)))
    return runs


def observe_source(blk):
    """Source region (varint at 0x20). Returns container v2 dict + warnings."""
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}
    runs = printable_runs(src)
    if not runs:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}
    segments = []
    for _, seg in runs:
        txt = seg.decode("ascii", "replace")
        capped, trunc = locator(txt)
        segments.append({"value": capped, "truncated": trunc})
    if len(runs) == 1:
        status = "EXACT"
        loc, trunc = locator(segments[0]["value"])
        return {"source_status": status, "source_locator": loc,
                "source_segments": segments, "source_reconstruction": None,
                "source_truncated": trunc}
    # SEGMENTED_PARTIAL: locator is a lossy PRINTABLE_RUN_JOIN candidate.
    joined = "/".join(s["value"] for s in segments)
    loc, trunc = locator(joined)
    return {"source_status": "SEGMENTED_PARTIAL", "source_locator": loc,
            "source_segments": segments,
            "source_reconstruction": "PRINTABLE_RUN_JOIN",
            "source_truncated": trunc}


def observe_string(blk, tok, pos, in_source):
    kb = tok.encode("utf-8")
    short, trunc = locator(tok)
    if in_source:
        return {"byte_offset": pos, "framing_tag_raw": None,
                "encoded_length": None, "value_byte_length": len(kb),
                "short_value": short, "value_truncated": trunc,
                "framing_status": "SOURCE_PATH_TEXT"}
    if pos < 1:
        return None
    L, n = load_unsigned(blk, pos - 1)
    if L is not None and L - 1 == len(kb):
        framing_status = "FRAMED_PLAINTEXT"
    else:
        framing_status = "FRAMED_CANDIDATE"
    return {"byte_offset": pos,
            "framing_tag_raw": blk[pos - 2] if pos >= 2 else None,
            "encoded_length": L, "value_byte_length": len(kb),
            "short_value": short, "value_truncated": trunc,
            "framing_status": framing_status}


def harden_mpkinfo(mpkinfo_path):
    """H6 guards: version==3, exact size invariant, entry raw exactly 20B."""
    st = os.path.getsize(mpkinfo_path)
    with open(mpkinfo_path, "rb") as f:
        head = f.read(8)
    if len(head) != 8:
        raise ValueError("mpkinfo too short")
    version, count = struct.unpack("<II", head)
    if version != 3:
        raise ValueError(f"mpkinfo version must be 3, got {version}")
    expected = 8 + count * 20 + 16
    if st != expected:
        raise ValueError(f"mpkinfo size {st} != expected {expected}")
    return count


def read_entry(mpkinfo_path, index, count):
    if not (0 <= index < count):
        raise IndexError(f"entry index {index} out of range 0..{count-1}")
    with open(mpkinfo_path, "rb") as f:
        f.seek(8 + index * 20)
        raw = f.read(20)
    if len(raw) != 20:
        raise ValueError(f"entry raw must be exactly 20B, got {len(raw)}B")
    f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
    return {"f0": f0, "f1": f1, "offset": off, "stored_size": size,
            "flags": flags}


def harden_block(blk):
    """H6 guards: Lua 5.4 fmt 0, LUAC_DATA exact, size fields 4/8/8."""
    sig = blk.find(LUA_SIG)
    if sig < 0:
        raise ValueError("no Lua signature")
    if blk[sig + 4] != 0x54:
        raise ValueError(f"Lua version must be 0x54, got 0x{blk[sig+4]:02X}")
    if blk[sig + 5] != 0:
        raise ValueError(f"format byte must be 0, got {blk[sig+5]}")
    if blk[sig + 6:sig + 12] != LUAC_DATA_STD:
        raise ValueError("LUAC_DATA mismatch")
    if list(blk[sig + 12:sig + 15]) != [4, 8, 8]:
        raise ValueError("size fields must be 4/8/8")
    return sig


def normalize(archive_dir, archive_name, mpkinfo_name, entry_index,
              game_version, commit, output_path):
    archive_path = os.path.join(archive_dir, archive_name)
    mpkinfo_path = os.path.join(archive_dir, mpkinfo_name)

    # H6: fail closed on identity
    if not game_version or game_version == "UNKNOWN":
        raise SystemExit("FAIL: game_version unavailable (fail closed)")
    if not commit or commit == "unknown":
        raise SystemExit("FAIL: extractor commit unavailable (fail closed)")

    rec = {
        "schema_version": SCHEMA_VERSION,
        "extractor_commit": commit,
        "extractor_source_sha256": sha256_file(os.path.abspath(__file__)),
        "game_version": game_version,
        "archive": archive_name,
        "archive_sha256": sha256_stream(archive_path),
        "mpkinfo_sha256": sha256_stream(mpkinfo_path),
    }

    count = harden_mpkinfo(mpkinfo_path)
    e = read_entry(mpkinfo_path, entry_index, count)
    rec.update({
        "entry_index": entry_index,
        "entry_offset": e["offset"],
        "entry_stored_size": e["stored_size"],
        "flags_raw": e["flags"],
    })

    if e["offset"] + e["stored_size"] > os.path.getsize(archive_path):
        raise ValueError("entry offset+size exceeds archive size")
    with open(archive_path, "rb") as f:
        f.seek(e["offset"])
        blk = f.read(e["stored_size"])
    if len(blk) != e["stored_size"]:
        raise ValueError("block read truncated")
    rec["block_sha256"] = hashlib.sha256(blk).hexdigest()

    harden_block(blk)
    src = observe_source(blk)
    rec["container"] = {"lua_version": "5.4", **src}

    rec["strings"] = []
    rec["references"] = []
    Ls, _ = load_unsigned(blk, 0x20)
    src_region_end = 0x21 + (Ls - 1) if Ls else 0
    for tok, pkind in TARGETS:
        pos = blk.find(tok.encode("utf-8"))
        if pos < 0:
            continue
        in_source = pos < src_region_end
        so = observe_string(blk, tok, pos, in_source)
        if so is not None:
            rec["strings"].append(so)
        confidence = "MEDIUM" if (so and so["framing_status"] == "FRAMED_PLAINTEXT") else "LOW"
        short, trunc = locator(tok)
        rec["references"].append({
            "raw_value": short,
            "value_truncated": trunc,
            "byte_offset": pos,
            "source_kind": "source_path" if in_source else "block_string",
            "pattern_kind": pkind,
            "confidence": confidence,
        })

    warnings = list(WARN_BASE)
    if src["source_status"] == "SEGMENTED_PARTIAL":
        warnings.append("SOURCE_SEGMENTED_SERIALIZATION")
    rec["warnings"] = warnings

    if output_path:
        write_record(rec, output_path)
    return rec


def write_record(rec, output_path):
    """H2: the tool writes its own UTF-8 output, then round-trip validates."""
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(output_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if loaded != rec:
        raise ValueError("round-trip validation failed: written record != in-memory record")
    # verify 江晏 survives verbatim when present
    for ref in rec.get("references", []):
        if ref["raw_value"] == "江晏":
            ok = any(r["raw_value"] == "江晏" for r in loaded["references"])
            if not ok:
                raise ValueError("round-trip validation failed: 江晏 corrupted")
    return loaded


def selftest():
    # varint regression
    for blob, expect in [(bytes([0x80]), 0), (bytes([0xBE]), 62),
                         (bytes([0x01, 0xEC]), 236), (bytes([0x01, 0xF5]), 245)]:
        got, _ = load_unsigned(blob, 0)
        assert got == expect, (blob.hex(" "), got, expect)
    # MAX_LOCATOR_BYTES: ASCII cap
    v, t = locator("a" * 100)
    assert len(v.encode("utf-8")) == MAX_LOCATOR_BYTES and t
    # CJK cap: 40 * 汉 = 120 bytes -> capped to 63 bytes (21 汉)
    v, t = locator("汉" * 40)
    assert t and len(v.encode("utf-8")) <= MAX_LOCATOR_BYTES
    assert v == "汉" * 21, repr(v)  # 63 bytes, complete codepoints
    # UTF-8 boundary: cut mid-codepoint must not leave a dangling lead byte
    v, t = locator("a" * 62 + "汉")  # 62 + 3 = 65 bytes -> 64 bytes cut inside 汉
    assert t and v == "a" * 62, repr(v)  # dangling lead byte trimmed; complete codepoints
    # 江晏 round-trip through JSON (ensure_ascii=False)
    import io
    buf = io.StringIO()
    json.dump({"raw_value": "江晏"}, buf, ensure_ascii=False)
    assert json.loads(buf.getvalue())["raw_value"] == "江晏"
    # taxonomy
    tax = {t: k for t, k in TARGETS}
    assert tax["dq_610900"] == "TASK_REF_CANDIDATE"
    assert tax["EXPANSION_QINGHE"] == "REGION_REF_CANDIDATE"
    assert tax["TextByNo"] == "TEXT_LOOKUP_KEY_CANDIDATE"
    assert tax["70276"] == "TEXT_REF_CANDIDATE"
    assert tax["NodeGraphData"] == "FIELD_KEY_CANDIDATE"
    assert tax["江晏"] == "CHARACTER_TOKEN"
    # source v2: EXACT and SEGMENTED_PARTIAL fields
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03])
    src = b"@synthetic/path.lua"
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x94]) + src + body)
    s = observe_source(blk)
    assert s["source_status"] == "EXACT" and s["source_locator"] == "@synthetic/path.lua"
    assert s["source_reconstruction"] is None
    src2 = b"@a/b\x07\x00\xf0\xff\xb8" + b"_c.lua"  # 15 bytes -> varint 0x90
    blk2 = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x90]) + src2 + body)
    s2 = observe_source(blk2)
    assert s2["source_status"] == "SEGMENTED_PARTIAL"
    assert s2["source_reconstruction"] == "PRINTABLE_RUN_JOIN"
    assert len(s2["source_segments"]) == 2
    # harden guards fail closed
    try:
        harden_block(LUA_SIG + bytes([0x53, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8]))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-004A raw narrative observation normalizer")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--game-version", default=None)
    ap.add_argument("--commit", default=None)
    ap.add_argument("--output", default=None)
    ap.add_argument("archive_dir", nargs="?")
    ap.add_argument("archive", nargs="?")
    ap.add_argument("mpkinfo", nargs="?")
    ap.add_argument("entry_index", nargs="?", type=int)
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not (args.archive_dir and args.archive and args.mpkinfo
            and args.entry_index is not None):
        ap.error("archive_dir archive mpkinfo entry_index required (or --selftest)")

    game_version = args.game_version
    if game_version is None:
        vf = os.path.join(args.archive_dir, "patching_version.txt")
        try:
            game_version = open(vf, encoding="utf-8").read().strip()
        except OSError:
            game_version = None
    commit = args.commit
    if commit is None:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                check=True).stdout.strip()
        except Exception:
            commit = None

    rec = normalize(args.archive_dir, args.archive, args.mpkinfo,
                    args.entry_index, game_version, commit, args.output)
    if args.output is None:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.output} (round-trip OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
