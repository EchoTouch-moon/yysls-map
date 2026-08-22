#!/usr/bin/env python3
"""
inspect_mpkinfo.py — deterministic, read-only parser for NetEase .mpkinfo
resource index files (燕云十六声 / yysls). Wave 1.6 W-R02.

Format (confirmed on 7 samples):

    header : uint32 LE version (=3) + uint32 LE entry_count   (8 bytes)
    entries: entry_count * 20 bytes each (fixed)
    trailer: 16 bytes (purpose unknown; present in all samples)

Entry (20 bytes):
    +0x00  name_fragment  u32   partial name / 16-bit hex hash (ASCII); NOT a full path
    +0x04  hash           u32   unique per entry
    +0x08  offset         u32   byte offset into the paired .mpk (0 for directory)
    +0x0C  stored_size    u32   stored size (0 for directory)
    +0x10  flags          u32   1 = directory/empty, 0 = file (other values observed in patch indexes)

This tool only reads the index. It never opens, extracts, or decrypts .mpk payloads.
Fail-closed: unknown version, size/count mismatch, and truncation raise an error
instead of guessing.

Verification (run and expect):
    python inspect_mpkinfo.py --selftest            ->  prints "selftest PASS"
    python inspect_mpkinfo.py <valid_v3>.mpkinfo --summary   ->  version 3 summary
    python inspect_mpkinfo.py <truncated>           ->  exit 1 (fail-closed)
    python inspect_mpkinfo.py <version4>            ->  exit 1 (unsupported version)
    python inspect_mpkinfo.py <HEXB_variant>        ->  exit 1 (unsupported version)
"""
import argparse
import struct
import sys
from collections import Counter

# Only this version is understood. Anything else fails closed.
SUPPORTED_VERSION = 3

ENTRY_SIZE = 20
HEADER_SIZE = 8
TRAILER_SIZE = 16

# Uppercase 2-char codes observed at the tail of name_fragment; treated as extension candidates.
KNOWN_EXT = ("PS", "VS", "CS", "HS", "GS", "DS", "TS", "SS")


class Mpkinfo:
    def __init__(self, data):
        self.data = data
        if len(data) < HEADER_SIZE:
            raise ValueError(f"truncated: {len(data)} bytes < {HEADER_SIZE}-byte header")
        self.version, self.count = struct.unpack_from("<II", data, 0)
        if self.version != SUPPORTED_VERSION:
            raise ValueError(
                f"unsupported version {self.version}; only version {SUPPORTED_VERSION} is supported")
        expected = HEADER_SIZE + self.count * ENTRY_SIZE + TRAILER_SIZE
        if len(data) < expected:
            raise ValueError(
                f"truncated: need {expected} bytes for {self.count} entries, got {len(data)}")
        if len(data) > expected:
            raise ValueError(
                f"unexpected trailing data: have {len(data)} bytes, expected {expected}")
        self.entries = []
        for i in range(self.count):
            off = HEADER_SIZE + i * ENTRY_SIZE
            f0, f1, f2, f3, f4 = struct.unpack_from("<IIIII", data, off)
            self.entries.append({
                "index": i,
                "entry_offset": off,
                "name_fragment": f0,
                "hash": f1,
                "offset": f2,
                "stored_size": f3,
                "flags": f4,
            })

    @staticmethod
    def _ascii(v):
        b = struct.pack("<I", v)
        return "".join(chr(x) if 32 <= x < 127 else "." for x in b)

    def name_text(self, e):
        return self._ascii(e["name_fragment"])

    def extension(self, e):
        """Best-effort extension from the printable tail of name_fragment."""
        t = self.name_text(e)
        tail = t.rstrip(".")
        if not tail:
            return None
        # trailing 2-char uppercase code (e.g. 'pPS' -> 'PS')
        if len(tail) >= 2 and tail[-2:].isupper() and tail[-2].isalpha() and tail[-1].isalpha():
            return tail[-2:]
        # last dot-separated chunk
        return tail.rsplit(".", 1)[-1] if "." in tail else None

    def is_directory(self, e):
        return e["flags"] == 1

    def summary(self):
        dirs = sum(1 for e in self.entries if self.is_directory(e))
        files = self.count - dirs
        exts = Counter()
        for e in self.entries:
            x = self.extension(e)
            if x:
                exts[x] += 1
        lines = [
            f"version       : {self.version}",
            f"entry_count   : {self.count}",
            f"entry_size    : {ENTRY_SIZE} (fixed)",
            f"body_size     : {self.count * ENTRY_SIZE}",
            f"trailer_size  : {TRAILER_SIZE}",
            f"file_size     : {len(self.data)}",
            f"directories   : {dirs} (flags==1, offset=size=0)",
            f"files         : {files}",
        ]
        if exts:
            top = ", ".join(f"{k}={v}" for k, v in exts.most_common(12))
            lines.append(f"extensions    : {top}")
        return "\n".join(lines)


def render_list(mp, limit=None):
    rows = mp.entries if limit is None else mp.entries[:limit]
    header = (f"{'idx':>4} {'entry_off':>8} {'name_fragment':>14} {'hash':>10} "
              f"{'offset':>10} {'stored_size':>11} {'flags':>5} {'type':<5}")
    out = [header]
    for e in rows:
        typ = "dir" if mp.is_directory(e) else "file"
        out.append(
            f"{e['index']:>4} 0x{e['entry_offset']:06X} "
            f"{mp.name_text(e):>14} {e['hash']:08X} "
            f"{e['offset']:>10} {e['stored_size']:>11} {e['flags']:>5} {typ:<5}")
    if limit is not None and limit < mp.count:
        out.append(f"... ({mp.count - limit} more entries)")
    return "\n".join(out)


def render_extensions(mp):
    exts = Counter()
    samples = {}
    for e in mp.entries:
        x = mp.extension(e)
        if x:
            exts[x] += 1
            samples.setdefault(x, e["index"])
    out = [f"{'extension':>10} {'count':>6}  first_index"]
    for k, v in exts.most_common():
        out.append(f"{k:>10} {v:>6}  {samples[k]}")
    if not exts:
        out.append("(no extension candidates detected)")
    return "\n".join(out)


def build_synthetic(count=3):
    """Build a minimal valid version=3 index for regression testing (synthetic, no game data)."""
    header = struct.pack("<II", SUPPORTED_VERSION, count)
    entries = b"".join(
        struct.pack("<IIIII", 0x30303030 + i, 0x11111111 + i, 100 + i * 16, 40 + i, 0)
        for i in range(count))
    trailer = b"\x00" * TRAILER_SIZE
    return header + entries + trailer


def _must_raise(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(f"{label}: expected ValueError, none raised")


def selftest():
    """Synthetic regression: valid parse + fail-closed on malformed/unsupported inputs."""
    data = build_synthetic(3)
    mp = Mpkinfo(data)
    assert mp.version == SUPPORTED_VERSION and mp.count == 3, "valid parse failed"
    assert len(mp.entries) == 3, "entry count mismatch"

    # truncated (drop trailer byte)
    _must_raise(lambda: Mpkinfo(data[:-1]), "truncated")
    # extra trailing bytes
    _must_raise(lambda: Mpkinfo(data + b"\x00"), "extra-bytes")
    # unsupported version
    bad = struct.pack("<II", SUPPORTED_VERSION + 1, 1) + build_synthetic(1)[HEADER_SIZE:]
    _must_raise(lambda: Mpkinfo(bad), "unsupported-version")
    # count mismatch (header claims 5, body has 3)
    mismatch = struct.pack("<II", SUPPORTED_VERSION, 5) + data[HEADER_SIZE:]
    _must_raise(lambda: Mpkinfo(mismatch), "count-mismatch")
    # too short for header
    _must_raise(lambda: Mpkinfo(b"\x03\x00\x00"), "short-header")
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic read-only .mpkinfo index parser")
    ap.add_argument("file", nargs="?", help="path to a .mpkinfo file")
    ap.add_argument("--summary", action="store_true", help="print structural summary")
    ap.add_argument("--list", action="store_true", help="list entries")
    ap.add_argument("--limit", type=int, default=50, help="max entries for --list (default 50)")
    ap.add_argument("--extensions", action="store_true", help="extension histogram")
    ap.add_argument("--selftest", action="store_true", help="run synthetic regression and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        try:
            selftest()
            print("selftest PASS")
            return 0
        except AssertionError as exc:
            print(f"selftest FAIL: {exc}", file=sys.stderr)
            return 1

    if not args.file:
        ap.error("a file path is required (or use --selftest)")

    with open(args.file, "rb") as f:
        data = f.read()

    try:
        mp = Mpkinfo(data)
    except ValueError as exc:
        print(f"ERROR: fail-closed: {exc}", file=sys.stderr)
        return 1

    if args.summary or not (args.list or args.extensions):
        print(mp.summary())
    if args.list:
        print(render_list(mp, args.limit))
    if args.extensions:
        print(render_extensions(mp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
