#!/usr/bin/env python3
"""
discovery_engine.py — NEX-004B: Structural Discovery & Generalization Pilot engine.

Generic structural discovery WITHOUT any hard-coded narrative token allowlist:
  * FRAMED_STRING_SCAN : scan the block for [tag][len varint][len-1 bytes] framed
                         printable strings (structural framing pattern), then
                         classify each value with the frozen generic rules.
  * SOURCE_PATH_SCAN   : classify components of the observed source path
                         (split on '/' and '.'), generic rule-based.

Frozen classifier rules (R1..R5):
  R1  ^dq_[0-9]+$                    -> TASK_REF_CANDIDATE
  R2  ^EXPANSION_[A-Z0-9_]+$         -> REGION_REF_CANDIDATE
  R3  ^[0-9]{4,10}$                  -> TEXT_REF_CANDIDATE
  R4  ^[A-Za-z_][A-Za-z0-9_]{2,47}$  -> IDENTIFIER_TOKEN_CANDIDATE
  R5  ^[\u4e00-\u9fff]{2,4}$         -> SHORT_CJK_TERM_CANDIDATE
No generic CJK -> CHARACTER_TOKEN. No generic identifier -> FIELD_KEY.

Limits: MAX_LOCATOR_BYTES=64 (UTF-8 bytes), MAX_OBSERVATIONS_PER_ENTRY=32,
per-class cap 8.  No prose/dialogue dump, no full script dump.

Record schema: raw-structural-observation-1 (provenance like RawNarrativeObservation
v2 + observations[] with discovery_rule_id/discovery_method/pattern_kind/confidence).

Usage:
    python discovery_engine.py --selftest
    python discovery_engine.py <archive_dir> <archive> <mpkinfo> <entry_index>
                               --output path.json [--game-version V] [--commit C]
"""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
MAX_LOCATOR_BYTES = 64
MAX_OBSERVATIONS_PER_ENTRY = 32
PER_CLASS_CAP = 8
SCHEMA_VERSION = "raw-structural-observation-1"

# Structural framing tags observed to frame strings (raw bytes; NOT Lua constant tags).
FRAMING_TAGS = {0x04, 0x05, 0x06, 0x07, 0x08, 0x14, 0x15, 0x16}

# Frozen generic classifier rules (ordered; first match wins).
RULES = [
    (re.compile(r"^dq_[0-9]+$"), "TASK_REF_CANDIDATE", "R1"),
    (re.compile(r"^EXPANSION_[A-Z0-9_]+$"), "REGION_REF_CANDIDATE", "R2"),
    (re.compile(r"^[0-9]{4,10}$"), "TEXT_REF_CANDIDATE", "R3"),
    (re.compile(r"^[A-Za-z_][A-Za-z0-9_]{2,47}$"), "IDENTIFIER_TOKEN_CANDIDATE", "R4"),
    (re.compile(r"^[\u4e00-\u9fff]{2,4}$"), "SHORT_CJK_TERM_CANDIDATE", "R5"),
]
CONFIDENCE = {
    "TASK_REF_CANDIDATE": "MEDIUM",
    "REGION_REF_CANDIDATE": "MEDIUM",
    "TEXT_REF_CANDIDATE": "MEDIUM",
    "SHORT_CJK_TERM_CANDIDATE": "MEDIUM",
    "IDENTIFIER_TOKEN_CANDIDATE": "LOW",
}

WARN_BASE = [
    "INSTRUCTION_SERIALIZATION_VARIANT",
    "CONSTANT_OWNERSHIP_UNKNOWN",
    "PROTO_OWNERSHIP_UNKNOWN",
    "SEMANTIC_ROLE_UNVERIFIED",
]


def classify(value):
    """Return (pattern_kind, rule_id) for a value, or (None, None)."""
    for rx, kind, rid in RULES:
        if rx.match(value):
            return kind, rid
    return None, None


def locator(value, cap=MAX_LOCATOR_BYTES):
    """UTF-8-safe byte cap: encode -> cap at `cap` bytes -> trim incomplete trailing codepoint."""
    b = value.encode("utf-8")
    if len(b) <= cap:
        return value, False
    b = b[:cap]
    while b and (b[-1] & 0xC0) == 0x80:
        b = b[:-1]
    if b and b[-1] >= 0xC0:
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


def is_printable(s):
    try:
        t = s.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return t.isprintable() and "\x00" not in t


def harden_mpkinfo(mpkinfo_path):
    st = os.path.getsize(mpkinfo_path)
    with open(mpkinfo_path, "rb") as f:
        head = f.read(8)
    if len(head) != 8:
        raise ValueError("mpkinfo too short")
    version, count = struct.unpack("<II", head)
    if version != 3:
        raise ValueError(f"mpkinfo version must be 3, got {version}")
    if st != 8 + count * 20 + 16:
        raise ValueError(f"mpkinfo size {st} != expected {8 + count * 20 + 16}")
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
    return {"offset": off, "stored_size": size, "flags": flags}


def harden_block(blk):
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


def printable_runs(blk):
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
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}, 0
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}, 0
    runs = printable_runs(src)
    if not runs:
        return {"source_status": "UNAVAILABLE", "source_locator": None,
                "source_segments": [], "source_reconstruction": None,
                "source_truncated": False}, 0
    segments = []
    for off, seg in runs:
        txt = seg.decode("ascii", "replace")
        capped, trunc = locator(txt)
        segments.append({"value": capped, "truncated": trunc, "offset": 0x21 + off})
    if len(runs) == 1:
        loc, trunc = locator(segments[0]["value"])
        return {"source_status": "EXACT", "source_locator": loc,
                "source_segments": segments, "source_reconstruction": None,
                "source_truncated": trunc}, 0x21 + slen
    joined = "/".join(s["value"] for s in segments)
    loc, trunc = locator(joined)
    return {"source_status": "SEGMENTED_PARTIAL", "source_locator": loc,
            "source_segments": segments,
            "source_reconstruction": "PRINTABLE_RUN_JOIN",
            "source_truncated": trunc}, 0x21 + slen


class Collector:
    """Bounds observations (MAX per entry, per-class cap)."""

    def __init__(self):
        self.obs = []
        self.class_count = {}

    def add(self, ob):
        kind = ob["pattern_kind"]
        if self.class_count.get(kind, 0) >= PER_CLASS_CAP:
            return
        if len(self.obs) >= MAX_OBSERVATIONS_PER_ENTRY:
            return
        self.class_count[kind] = self.class_count.get(kind, 0) + 1
        self.obs.append(ob)


def framed_scan(blk, prov):
    """FRAMED_STRING_SCAN: [tag][len varint][len-1 bytes] printable values."""
    col = Collector()
    n = len(blk)
    for p in range(n):
        tag = blk[p]
        if tag not in FRAMING_TAGS:
            continue
        L, ln = load_unsigned(blk, p + 1)
        if L is None or L < 2 or L > MAX_LOCATOR_BYTES + 1:
            continue
        vlen = L - 1
        start = p + 1 + ln
        end = start + vlen
        if end > n:
            continue
        val = blk[start:end]
        if not is_printable(val):
            continue
        try:
            text = val.decode("utf-8")
        except UnicodeDecodeError:
            continue
        kind, rid = classify(text)
        if kind is None:
            continue
        short, trunc = locator(text)
        col.add({
            "byte_offset": p,
            "framing_tag_raw": hex(tag),
            "encoded_length": L,
            "value_byte_length": len(val),
            "raw_value": short,
            "value_truncated": trunc,
            "discovery_rule_id": rid,
            "discovery_method": "FRAMED_STRING_SCAN",
            "pattern_kind": kind,
            "confidence": CONFIDENCE[kind],
            "provenance": prov,
        })
    return col.obs


def source_path_scan(src_obs, prov):
    """SOURCE_PATH_SCAN: classify components of observed source path."""
    col = Collector()
    for seg in src_obs.get("source_segments", []):
        base = seg["offset"]
        value = seg["value"]
        # split on '/' and '.' while tracking offsets
        pos = 0
        for piece in re.split(r"([/\.])", value):
            if piece in ("/", ".") or piece == "":
                pos += len(piece)
                continue
            kind, rid = classify(piece)
            if kind is None:
                pos += len(piece)
                continue
            col.add({
                "byte_offset": base + pos,
                "framing_tag_raw": None,
                "encoded_length": None,
                "value_byte_length": len(piece.encode("utf-8")),
                "raw_value": piece,
                "value_truncated": False,
                "discovery_rule_id": rid,
                "discovery_method": "SOURCE_PATH_SCAN",
                "pattern_kind": kind,
                "confidence": CONFIDENCE[kind],
                "provenance": prov,
            })
            pos += len(piece)
    return col.obs


def discover(archive_dir, archive_name, mpkinfo_name, entry_index,
             game_version, commit, output_path):
    if not game_version or game_version == "UNKNOWN":
        raise SystemExit("FAIL: game_version unavailable (fail closed)")
    if not commit or commit == "unknown":
        raise SystemExit("FAIL: extractor commit unavailable (fail closed)")

    archive_path = os.path.join(archive_dir, archive_name)
    mpkinfo_path = os.path.join(archive_dir, mpkinfo_name)
    rec = {
        "schema_version": SCHEMA_VERSION,
        "extractor_commit": commit,
        "extractor_source_sha256": sha256_file(os.path.abspath(__file__)),
        "game_version": game_version,
        "archive": archive_name,
        "archive_sha256": sha256_stream(archive_path),
        "mpkinfo_sha256": sha256_stream(mpkinfo_path),
        "entry_index": entry_index,
    }
    count = harden_mpkinfo(mpkinfo_path)
    e = read_entry(mpkinfo_path, entry_index, count)
    rec.update({"entry_offset": e["offset"], "entry_stored_size": e["stored_size"],
                "flags_raw": e["flags"]})
    if e["offset"] + e["stored_size"] > os.path.getsize(archive_path):
        raise ValueError("entry offset+size exceeds archive size")
    with open(archive_path, "rb") as f:
        f.seek(e["offset"])
        blk = f.read(e["stored_size"])
    if len(blk) != e["stored_size"]:
        raise ValueError("block read truncated")
    rec["block_sha256"] = hashlib.sha256(blk).hexdigest()
    harden_block(blk)

    src_obs, _ = observe_source(blk)
    rec["container"] = {"lua_version": "5.4", **src_obs}

    prov = {"schema_version": SCHEMA_VERSION, "extractor_commit": commit,
            "archive": archive_name, "entry_index": entry_index,
            "block_sha256": rec["block_sha256"]}
    obs = framed_scan(blk, prov) + source_path_scan(src_obs, prov)
    rec["observations"] = obs
    rec["observation_limits"] = {"max_locator_bytes": MAX_LOCATOR_BYTES,
                                 "max_per_entry": MAX_OBSERVATIONS_PER_ENTRY,
                                 "per_class_cap": PER_CLASS_CAP}
    warnings = list(WARN_BASE)
    if src_obs["source_status"] == "SEGMENTED_PARTIAL":
        warnings.append("SOURCE_SEGMENTED_SERIALIZATION")
    rec["warnings"] = warnings

    if output_path:
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
            f.write("\n")
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if loaded != rec:
            raise ValueError("round-trip validation failed")
    return rec


def selftest():
    # classifier rules
    cases = [
        ("dq_610900", "TASK_REF_CANDIDATE", "R1"),
        ("EXPANSION_QINGHE", "REGION_REF_CANDIDATE", "R2"),
        ("70276", "TEXT_REF_CANDIDATE", "R3"),
        ("NodeGraphData", "IDENTIFIER_TOKEN_CANDIDATE", "R4"),
        ("TextByNo", "IDENTIFIER_TOKEN_CANDIDATE", "R4"),
        ("江晏", "SHORT_CJK_TERM_CANDIDATE", "R5"),
        ("storyline_data", "IDENTIFIER_TOKEN_CANDIDATE", "R4"),
        ("abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ_1", None, None),  # >48 chars
        ("a1", None, None),       # too short for R4
        ("123", None, None),      # 3 digits < R3 min 4
        ("", None, None),
    ]
    for val, kind, rid in cases:
        got_kind, got_rid = classify(val)
        assert got_kind == kind and got_rid == rid, (val, got_kind, got_rid)
    # CJK 5 chars -> no match (R5 max 4)
    assert classify("江晏先生你好") == (None, None)
    # identifier with dot -> no match
    assert classify("dq_610900.lua") == (None, None)
    # byte cap
    v, t = locator("汉" * 40)
    assert t and len(v.encode("utf-8")) <= 64 and v == "汉" * 21
    # framed scan on synthetic block
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    src = b"@synthetic/path.lua"
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03])
    framed = bytes([0x04, 0x8E]) + b"NodeGraphData" + bytes([0x04, 0x86]) + b"70276"
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x94]) + src + body + framed)
    obs = framed_scan(blk, {"p": 1})
    kinds = {o["pattern_kind"] for o in obs}
    assert "IDENTIFIER_TOKEN_CANDIDATE" in kinds and "TEXT_REF_CANDIDATE" in kinds
    # source path scan recovers dq_610900 as TASK_REF
    src2 = b"@a/b\x07\x00\xf0\xff\xb8" + b"dq_610900.lua"  # 21 bytes -> varint 22 = 0x96
    blk2 = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x96]) + src2 + body)
    s2, _ = observe_source(blk2)
    obs2 = source_path_scan(s2, {"p": 1})
    assert any(o["pattern_kind"] == "TASK_REF_CANDIDATE" and o["raw_value"] == "dq_610900"
               for o in obs2), obs2
    # collector caps
    col = Collector()
    for i in range(100):
        col.add({"pattern_kind": "IDENTIFIER_TOKEN_CANDIDATE", "x": i})
    assert len(col.obs) == PER_CLASS_CAP
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-004B generic structural discovery")
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
    rec = discover(args.archive_dir, args.archive, args.mpkinfo,
                   args.entry_index, game_version, commit, args.output)
    if args.output is None:
        print(json.dumps(rec, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.output} (round-trip OK)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
