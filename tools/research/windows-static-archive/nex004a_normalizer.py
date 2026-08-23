#!/usr/bin/env python3
"""
nex004a_normalizer.py — NEX-004A: Raw Narrative Observation Normalizer.

Purpose: without decoding the private Lua instruction serialization
(H-NEX-003T = INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED), convert
statically observable native narrative metadata into reproducible,
traceable, non-semanticized structural records (RawNarrativeObservation).

Principles:
  * observations only — no canonical writes, no constant index, no owning proto.
  * framing_tag_raw is a RAW byte, never called a Lua constant tag.
  * short locators only: MAX_LOCATOR_BYTES bound on every recorded value.
  * no bulk string dump / full dialogue / full script.

Record schema (v1):
  provenance: schema_version, extractor_commit, game_version, archive,
              archive_sha256, mpkinfo_sha256, entry_index, entry_offset,
              entry_stored_size, flags_raw, block_sha256
  container : lua_version, source_status (EXACT|SEGMENTED_PARTIAL|UNAVAILABLE),
              source_path_observed
  strings   : byte_offset, framing_tag_raw, encoded_length, value_byte_length,
              short_value, framing_status
  references: raw_value, byte_offset, source_kind, pattern_kind, confidence
  warnings  : SOURCE_SEGMENTED_SERIALIZATION, INSTRUCTION_SERIALIZATION_VARIANT,
              CONSTANT_OWNERSHIP_UNKNOWN, PROTO_OWNERSHIP_UNKNOWN,
              SEMANTIC_ROLE_UNVERIFIED

Usage:
    python nex004a_normalizer.py --selftest
    python nex004a_normalizer.py <archive_dir> <archive> <mpkinfo> <entry_index>
                                  [--game-version V] [--commit C]
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
SCHEMA_VERSION = "raw-narrative-observation-1"

# (target, default pattern_kind, source_kind hint)
TARGETS = [
    ("dq_610900", "SCRIPT_FAMILY_CANDIDATE", "source_path"),
    ("EXPANSION_QINGHE", "TEXT_LOOKUP_KEY_CANDIDATE", "block_string"),
    ("storyline_data", "SCRIPT_FAMILY_CANDIDATE", "source_path"),
    ("MSD_ST", "SCRIPT_FAMILY_CANDIDATE", "source_path"),
    ("NodeGraphData", "FIELD_KEY_CANDIDATE", "block_string"),
    ("TextByNo", "FIELD_KEY_CANDIDATE", "block_string"),
    ("70276", "TASK_REF_CANDIDATE", "block_string"),
    ("江晏", "CHARACTER_TOKEN", "block_string"),
]

WARN_BASE = [
    "INSTRUCTION_SERIALIZATION_VARIANT",
    "CONSTANT_OWNERSHIP_UNKNOWN",
    "PROTO_OWNERSHIP_UNKNOWN",
    "SEMANTIC_ROLE_UNVERIFIED",
]


def sha256_stream(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


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
    cur = []
    start = None
    for i, b in enumerate(blk):
        if 32 <= b <= 126:
            if cur is None:
                cur = bytearray(); start = i
            cur.append(b)
        else:
            if cur:
                runs.append((start, bytes(cur)))
                cur = None
    if cur:
        runs.append((start, bytes(cur)))
    return runs


def observe_source(blk):
    """Source region (varint at 0x20, official MSB-first); return obs + status."""
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        return None, "UNAVAILABLE"
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        return None, "UNAVAILABLE"
    runs = printable_runs(src)
    if len(runs) == 0:
        return None, "UNAVAILABLE"
    if len(runs) == 1:
        status = "EXACT"
    else:
        status = "SEGMENTED_PARTIAL"
    # observed path: printable runs joined with "/" (bounded locator)
    parts = [r[1].decode("ascii", "replace") for r in runs]
    path = "/".join(parts)
    return path[:MAX_LOCATOR_BYTES], status


def find_target(blk, tok):
    kb = tok.encode("utf-8")
    return blk.find(kb)


def observe_string(blk, tok, pos, in_source):
    kb = tok.encode("utf-8")
    if in_source:
        return {
            "byte_offset": pos,
            "framing_tag_raw": None,
            "encoded_length": None,
            "value_byte_length": len(kb),
            "short_value": kb.decode("utf-8", "replace")[:MAX_LOCATOR_BYTES],
            "framing_status": "SOURCE_PATH_TEXT",
        }
    if pos < 1:
        return None
    L, n = load_unsigned(blk, pos - 1)
    if L is not None and L - 1 == len(kb):
        framing_status = "FRAMED_PLAINTEXT"
    else:
        framing_status = "FRAMED_CANDIDATE"
    return {
        "byte_offset": pos,
        "framing_tag_raw": blk[pos - 2] if pos >= 2 else None,
        "encoded_length": L,
        "value_byte_length": len(kb),
        "short_value": kb.decode("utf-8", "replace")[:MAX_LOCATOR_BYTES],
        "framing_status": framing_status,
    }


def normalize(archive_dir, archive_name, mpkinfo_name, entry_index,
              game_version, commit):
    archive_path = os.path.join(archive_dir, archive_name)
    mpkinfo_path = os.path.join(archive_dir, mpkinfo_name)

    # provenance
    rec = {
        "schema_version": SCHEMA_VERSION,
        "extractor_commit": commit,
        "game_version": game_version,
        "archive": archive_name,
        "archive_sha256": sha256_stream(archive_path),
        "mpkinfo_sha256": sha256_stream(mpkinfo_path),
    }

    # entry
    head = open(mpkinfo_path, "rb").read(8)
    version, count = struct.unpack("<II", head)
    if version != 3:
        raise ValueError(f"mpkinfo version must be 3, got {version}")
    if not (0 <= entry_index < count):
        raise IndexError(f"entry index {entry_index} out of range 0..{count-1}")
    with open(mpkinfo_path, "rb") as f:
        f.seek(8 + entry_index * 20)
        raw = f.read(20)
    f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
    rec.update({
        "entry_index": entry_index,
        "entry_offset": off,
        "entry_stored_size": size,
        "flags_raw": flags,
    })

    # block (seek + bounded read)
    if off + size > os.path.getsize(archive_path):
        raise ValueError("entry offset+size exceeds archive size")
    with open(archive_path, "rb") as f:
        f.seek(off)
        blk = f.read(size)
    rec["block_sha256"] = hashlib.sha256(blk).hexdigest()

    # container
    sig = blk.find(LUA_SIG)
    if sig < 0 or blk[sig + 4] != 0x54 or blk[sig + 5] != 0:
        raise ValueError("not Lua 5.4 format 0")
    source_path, source_status = observe_source(blk)
    rec["container"] = {
        "lua_version": "5.4",
        "source_status": source_status,
        "source_path_observed": source_path,
    }

    # string + reference observations for the targets
    rec["strings"] = []
    rec["references"] = []
    src_end = 0x21 + len(blk[0x21:])  # block end; source region is 0x21..(varint end)
    Ls, _ = load_unsigned(blk, 0x20)
    src_region_end = 0x21 + (Ls - 1) if Ls else 0

    for tok, pkind, skind in TARGETS:
        pos = find_target(blk, tok)
        if pos < 0:
            continue
        in_source = pos < src_region_end
        so = observe_string(blk, tok, pos, in_source)
        if so is not None:
            rec["strings"].append(so)
        confidence = "MEDIUM" if (so and so["framing_status"] == "FRAMED_PLAINTEXT") else "LOW"
        rec["references"].append({
            "raw_value": tok[:MAX_LOCATOR_BYTES],
            "byte_offset": pos,
            "source_kind": "source_path" if in_source else "block_string",
            "pattern_kind": pkind,
            "confidence": confidence,
        })

    # warnings
    warnings = list(WARN_BASE)
    if source_status == "SEGMENTED_PARTIAL":
        warnings.append("SOURCE_SEGMENTED_SERIALIZATION")
    rec["warnings"] = warnings
    return rec


def selftest():
    # synthetic block: header + source + one framed target
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    src = b"@synthetic/path.lua"
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03])
    framed = bytes([0x04, 0x8E]) + b"NodeGraphData"
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x94]) + src + body + framed)
    src2, status = observe_source(blk)
    assert status == "EXACT" and src2 == "@synthetic/path.lua", (src2, status)
    pos = blk.find(b"NodeGraphData")
    assert pos == 0x34 + len(body) + 2  # +2 for tag(04) + len(8e) before the string
    so = observe_string(blk, "NodeGraphData", pos, False)
    assert so["framing_status"] == "FRAMED_PLAINTEXT"
    assert so["encoded_length"] == 14 and so["value_byte_length"] == 13
    assert so["framing_tag_raw"] == 0x04
    # segmented source (2 printable runs)
    src2b = b"@a/b\x07\x00\xf0\xff\xb8" + b"_c.lua"  # 15 bytes -> varint 16 = 0x90
    blk2 = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x90]) + src2b + body)
    sp, st2 = observe_source(blk2)
    assert st2 == "SEGMENTED_PARTIAL", st2
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-004A raw narrative observation normalizer")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--game-version", default=None)
    ap.add_argument("--commit", default=None)
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
            game_version = open(vf).read().strip()
        except OSError:
            game_version = "UNKNOWN"
    commit = args.commit
    if commit is None:
        try:
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                check=True).stdout.strip()
        except Exception:
            commit = "unknown"
    rec = normalize(args.archive_dir, args.archive, args.mpkinfo,
                    args.entry_index, game_version, commit)
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
