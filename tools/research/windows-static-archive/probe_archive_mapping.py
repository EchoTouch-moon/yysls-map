#!/usr/bin/env python3
"""
probe_archive_mapping.py — W-R03: verify a version=3 .mpkinfo entry statically
resolves to a payload inside the paired .mpk (read-only, no extraction beyond a
handful of low-risk shader samples).

Usage:
    python probe_archive_mapping.py <file.mpkinfo> <file.mpk> [--limit N] [--ext PS,VS,CS]

Records per sample: entry_index, resource_tag_raw, hash_candidate, offset,
stored_size, flags, payload first bytes, payload SHA-256, actual_read_size,
format/compression candidate, result.
"""
import argparse
import hashlib
import struct
import sys
from inspect_mpkinfo import Mpkinfo

MAGICS = {
    b"DXBC": "DirectX shader bytecode (DXBC)",
    b"DXIL": "DirectX shader (DXIL)",
    b"SPIR": "SPIR-V",
    b"\x1f\x8b": "gzip",
    b"\x78\x9c": "zlib (default)",
    b"\x78\xda": "zlib (best)",
    b"\x78\x01": "zlib (no compression)",
    b"\x04\x22\x4d\x18": "LZ4 frame",
    b"PK\x03\x04": "ZIP",
    b"7z\xbc\xaf": "7z",
    b"\xfd7zXZ\x00": "xz",
    b"OggS": "Ogg",
    b"RIFF": "RIFF container",
    b"\x00\x00\x00\x00": "(all zeros)",
}


def detect_magic(head):
    for m, label in MAGICS.items():
        if head.startswith(m):
            return label
    # heuristics: looks like a little-endian u32 size/flag header?
    if len(head) >= 4:
        v = struct.unpack_from("<I", head, 0)[0]
        if 0 < v < 1 << 16 and v <= len(head):
            return f"possible block header (u32LE={v})"
    return None


def probe(mpkinfo_path, mpk_path, limit, exts):
    mp = Mpkinfo(open(mpkinfo_path, "rb").read())
    mpkinfo_sha = hashlib.sha256(open(mpkinfo_path, "rb").read()).hexdigest().upper()
    # mpk sha and header
    mpk_sha = hashlib.sha256(open(mpk_path, "rb").read()).hexdigest().upper()
    with open(mpk_path, "rb") as f:
        f.seek(0)
        mpk_head = f.read(16)

    print(f"# source_mpkinfo: {mpkinfo_path}")
    print(f"# source_mpkinfo SHA-256: {mpkinfo_sha}")
    print(f"# source_mpk: {mpk_path}")
    print(f"# source_mpk SHA-256: {mpk_sha}")
    print(f"# mpk first 16 bytes: {mpk_head.hex(' ')}  '{mpk_head.decode('ascii','replace')}'")
    print(f"# mpk size: {__import__('os').path.getsize(mpk_path)}")
    print()

    selected = []
    want = set(x.upper() for x in exts)
    for e in mp.entries:
        x = mp.extension(e)
        if x and x.upper() in want and not mp.is_directory(e):
            selected.append(e)
        if len(selected) >= limit:
            break

    with open(mpk_path, "rb") as f:
        for e in selected:
            tag = mp.name_text(e)
            off, size, flags = e["offset"], e["stored_size"], e["flags"]
            # sanity: read only within file bounds; cap read to avoid pathological sizes
            f.seek(off)
            payload = f.read(size)
            actual = len(payload)
            head = payload[:32]
            magic = detect_magic(head)
            sha = hashlib.sha256(payload).hexdigest().upper()
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in head)
            result = "PAYLOAD_READ" if actual == size else f"SHORT_READ({actual}/{size})"
            print(f"[{e['index']}] tag='{tag}' hash_candidate={e['hash']:08X} "
                  f"offset={off} stored_size={size} flags={flags}")
            print(f"    actual_read_size={actual} payload_sha256={sha}")
            print(f"    first_bytes={head.hex(' ')}")
            print(f"    first_ascii='{printable}'")
            print(f"    magic_candidate={magic}")
            print(f"    result={result}")
            print()
    return selected


def main(argv=None):
    ap = argparse.ArgumentParser(description="W-R03 archive linkage probe (read-only)")
    ap.add_argument("mpkinfo")
    ap.add_argument("mpk")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--ext", default="PS,VS,CS", help="comma list of extension candidates")
    args = ap.parse_args(argv)
    probe(args.mpkinfo, args.mpk, args.limit, args.ext.split(","))
    return 0


if __name__ == "__main__":
    sys.exit(main())
