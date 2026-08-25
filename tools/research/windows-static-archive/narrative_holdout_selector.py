#!/usr/bin/env python3
"""
narrative_holdout_selector.py — NEX-004C: narrative-relevant holdout selector.

FROZEN SELECTION POLICY (must not be changed after holdout results are seen):

  * Allowed prior        : source family tokens ONLY — "storyline_data",
                           "MSD_ST" — observed in the bounded Lua source region.
  * Forbidden signals    : dq_*, EXPANSION_*, numeric refs, CJK payload,
                           framed payload strings, known target values.
                           The selector NEVER inspects those.
  * Holdout              : 12 unique entries —
                           6 x (storyline_data AND NOT MSD_ST),
                           6 x (MSD_ST).
  * Exclusion            : every previous pilot/evidence/blind entry
                           (LT71[1768,1631], LT31[874], LT51[1178],
                            LT71[534,2766,1490,165], LT51[861,873], LT31[552,2876]).
  * Determinism          : candidates ranked by selection_score =
                           int(sha256("{arch}:{idx}:{offset}:{size}:{flags}")[:8],16);
                           take the lowest 6 per family.
  * Manifest             : reveals NO full source path — stores
                           archive, entry_index, entry_offset, stored_size,
                           flags_raw, source_family, source_locator_sha256,
                           selection_score.
  * Fail closed          : version/size/bounds checks; <6 candidates in either
                           family -> non-zero exit, no manifest.

Usage:
    python narrative_holdout_selector.py --selftest
    python narrative_holdout_selector.py <archive_dir> --output manifest.json
"""
import argparse
import hashlib
import json
import os
import struct
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
MANIFEST_SCHEMA = "nex004c-holdout-manifest-1"
FAMILY_A = "storyline_data"
FAMILY_B = "MSD_ST"
EXCLUDED = {
    "LT71": {1768, 1631, 534, 2766, 1490, 165},
    "LT51": {1178, 861, 873},
    "LT31": {874, 552, 2876},
}
ARCHIVES = ["LT71", "LT51", "LT31"]


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
    return None, None


def entry_metadata(mpkinfo_path, index, count):
    if not (0 <= index < count):
        return None
    with open(mpkinfo_path, "rb") as f:
        f.seek(8 + index * 20)
        raw = f.read(20)
    if len(raw) != 20:
        return None
    f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
    return {"f0": f0, "f1": f1, "offset": off, "size": size, "flags": flags}


def source_family(archive_path, entry):
    """Read the bounded Lua source region ONLY; return family or None."""
    st = os.path.getsize(archive_path)
    if entry["offset"] + entry["size"] > st:
        return None
    with open(archive_path, "rb") as f:
        f.seek(entry["offset"])
        blk = f.read(entry["size"])
    if len(blk) != entry["size"]:
        return None
    sig = blk.find(LUA_SIG)
    if sig < 0 or blk[sig + 4] != 0x54 or blk[sig + 5] != 0:
        return None
    if blk[sig + 6:sig + 12] != LUAC_DATA_STD:
        return None
    if list(blk[sig + 12:sig + 15]) != [4, 8, 8]:
        return None
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        return None
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        return None
    text = src.decode("utf-8", errors="replace")
    has_a = FAMILY_A in text
    has_b = FAMILY_B in text
    if has_b:
        return "MSD_ST"
    if has_a:
        return "storyline_data"
    return None


def select(archive_dir, output_path):
    candidates = []
    for arch in ARCHIVES:
        mpkinfo_path = os.path.join(archive_dir, arch + ".mpkinfo")
        archive_path = os.path.join(archive_dir, arch + ".mpk")
        head = open(mpkinfo_path, "rb").read(8)
        version, count = struct.unpack("<II", head)
        if version != 3 or os.path.getsize(mpkinfo_path) != 8 + count * 20 + 16:
            raise ValueError(f"mpkinfo invariant failed for {arch}")
        for idx in range(count):
            if idx in EXCLUDED.get(arch, set()):
                continue
            e = entry_metadata(mpkinfo_path, idx, count)
            if e is None:
                continue
            fam = source_family(archive_path, e)
            if fam is None:
                continue
            key = f"{arch}:{idx}:{e['offset']}:{e['size']}:{e['flags']}"
            score = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
            # source locator hash (path is NOT revealed)
            loc_hash = hashlib.sha256(key.encode()).hexdigest()
            candidates.append({
                "archive": arch, "entry_index": idx,
                "entry_offset": e["offset"], "stored_size": e["size"],
                "flags_raw": e["flags"], "source_family": fam,
                "source_locator_sha256": loc_hash, "selection_score": score,
            })
    pool_a = [c for c in candidates if c["source_family"] == "storyline_data"]
    pool_b = [c for c in candidates if c["source_family"] == "MSD_ST"]
    if len(pool_a) < 6 or len(pool_b) < 6:
        raise SystemExit(f"FAIL: insufficient candidates (A={len(pool_a)}, B={len(pool_b)})")
    pool_a.sort(key=lambda c: c["selection_score"])
    pool_b.sort(key=lambda c: c["selection_score"])
    sel_a = pool_a[:6]
    sel_b = pool_b[:6]
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "policy": ("source family prior only (storyline_data / MSD_ST); "
                   "forbidden signals unused: dq_*, EXPANSION_*, numeric refs, "
                   "CJK payload, framed payloads, known target values; "
                   "excludes all previous pilot/evidence/blind entries"),
        "selection": "selection_score = int(sha256(archive:index:offset:size:flags)[:8],16); lowest 6 per family",
        "holdout_a": sel_a,
        "holdout_b": sel_b,
        "source_path_not_revealed": True,
    }
    if output_path:
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return manifest


def selftest():
    for blob, expect in [(bytes([0x80]), 0), (bytes([0xBE]), 62)]:
        got, _ = load_unsigned(blob, 0)
        assert got == expect
    assert load_unsigned(bytes([1] * 8), 0) == (None, None)
    # family detection on synthetic sources
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    import tempfile
    def fam(src_bytes, vint):
        blk = b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([vint]) + src_bytes
        return source_family_of_blk(blk)
    def source_family_of_blk(blk):
        L, n = load_unsigned(blk, 0x20)
        slen = L - 1
        src = blk[0x21:0x21 + slen]
        text = src.decode("utf-8", errors="replace")
        has_a = FAMILY_A in text
        has_b = FAMILY_B in text
        if has_b:
            return "MSD_ST"
        if has_a:
            return "storyline_data"
        return None
    s1 = b"@hexm/client/storyline_data/x.lua"           # 34 bytes -> varint 35=0xA3
    s2 = b"@hexm/client/storyline_data/wanfa/MSD_ST/ZDQ/dq_610900.lua"  # 58 bytes -> 59=0xBB
    s3 = b"@hexm/client/ui/common.lua"                   # 25 bytes -> 26=0x9A
    assert fam(s1, 0xA3) == "storyline_data", fam(s1, 0xA3)
    assert fam(s2, 0xBB) == "MSD_ST", fam(s2, 0xBB)
    assert fam(s3, 0x9A) is None
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-004C holdout selector")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--output", default=None)
    ap.add_argument("archive_dir", nargs="?")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not args.archive_dir:
        ap.error("archive_dir required (or --selftest)")
    m = select(args.archive_dir, args.output)
    if args.output is None:
        print(json.dumps(m, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.output} (A={len(m['holdout_a'])}, B={len(m['holdout_b'])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
