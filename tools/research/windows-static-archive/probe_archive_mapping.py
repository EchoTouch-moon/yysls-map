#!/usr/bin/env python3
"""
probe_archive_mapping.py — W-R03: verify a version=3 .mpkinfo entry statically
resolves to a payload inside the paired .mpk. Read-only probe — NOT an extractor.

Usage:
    python probe_archive_mapping.py <file.mpkinfo> <file.mpk> [--limit N] [--ext PS,VS,CS]

Records per sample: entry_index, resource_tag_raw, hash_candidate, offset,
stored_size, flags, payload first bytes, payload SHA-256 (streamed, capped),
actual_read_size, format/compression candidate, result.

Guardrails:
    - bounds check (offset + stored_size within archive)
    - finite MAX_PROBE_BYTES read cap (pathological sizes are skipped, not read)
    - streaming SHA-256 (no full-block buffering beyond the cap)
    - explicit failure when no entry matches the requested extensions
    - recognizes LZMA magic (plus shader/container magics)
"""
import argparse
import hashlib
import os
import struct
import sys
from inspect_mpkinfo import Mpkinfo

# Finite read cap per probed block. Blocks larger than this are reported but not read.
MAX_PROBE_BYTES = 1 << 20  # 1 MiB

MAGICS = {
    b"LZMA": "LZMA compressed block",
    b"LuaT": "LuaT container",
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
    if len(head) >= 4:
        v = struct.unpack_from("<I", head, 0)[0]
        if 0 < v < 1 << 16 and v <= len(head):
            return f"possible block header (u32LE={v})"
    return None


def sha256_stream(f, size):
    """Streaming SHA-256 over `size` bytes; stops early on EOF (returns actual read)."""
    h = hashlib.sha256()
    remaining = size
    read_total = 0
    while remaining > 0:
        chunk = f.read(min(remaining, 1 << 16))
        if not chunk:
            break
        h.update(chunk)
        read_total += len(chunk)
        remaining -= len(chunk)
    return h.hexdigest().upper(), read_total


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def probe(mpkinfo_path, mpk_path, limit, exts):
    mpkinfo_sha = sha256_file(mpkinfo_path)
    mpk_sha = sha256_file(mpk_path)
    mpk_size = os.path.getsize(mpk_path)

    mp = Mpkinfo(open(mpkinfo_path, "rb").read())

    with open(mpk_path, "rb") as f:
        mpk_head = f.read(16)

    print(f"# source_mpkinfo: {mpkinfo_path}")
    print(f"# source_mpkinfo SHA-256: {mpkinfo_sha}")
    print(f"# source_mpk: {mpk_path}")
    print(f"# source_mpk SHA-256: {mpk_sha}")
    print(f"# mpk size: {mpk_size}")
    print(f"# MAX_PROBE_BYTES: {MAX_PROBE_BYTES}")
    print(f"# mpk first 16 bytes: {mpk_head.hex(' ')}  '{mpk_head.decode('ascii','replace')}'")
    print()

    selected = []
    want = set(x.upper() for x in exts)
    for e in mp.entries:
        x = mp.extension(e)
        if x and x.upper() in want and not mp.is_directory(e):
            selected.append(e)
        if len(selected) >= limit:
            break

    if not selected:
        print(f"ERROR: no matching samples for extensions {sorted(want)} "
              f"(limit={limit}); nothing probed.", file=sys.stderr)
        return False

    with open(mpk_path, "rb") as f:
        for e in selected:
            tag = mp.name_text(e)
            off, size, flags = e["offset"], e["stored_size"], e["flags"]

            if off < 0 or size < 0 or off + size > mpk_size:
                print(f"[{e['index']}] tag='{tag}' offset={off} stored_size={size} flags={flags}")
                print(f"    result=BOUNDS_VIOLATION (offset+size={off+size} > mpk_size={mpk_size})")
                print()
                continue
            if size > MAX_PROBE_BYTES:
                print(f"[{e['index']}] tag='{tag}' offset={off} stored_size={size} flags={flags}")
                print(f"    result=EXCEEDS_CAP (stored_size={size} > MAX_PROBE_BYTES={MAX_PROBE_BYTES})")
                print()
                continue

            f.seek(off)
            sha, actual = sha256_stream(f, size)
            f.seek(off)
            head = f.read(min(size, 32))
            magic = detect_magic(head)
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
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="W-R03 archive linkage probe (read-only)")
    ap.add_argument("mpkinfo")
    ap.add_argument("mpk")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--ext", default="PS,VS,CS", help="comma list of extension candidates")
    args = ap.parse_args(argv)
    ok = probe(args.mpkinfo, args.mpk, args.limit, args.ext.split(","))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
