#!/usr/bin/env python3
"""
probe_string_table.py — H-NEX-003AF: raw concatenated loadString walk.

Five structural models of the post-code region have been rejected
(003Y/003Z/003AA flat records, 003AB recursion, 003AC interleaved,
003AD length prefix, 003AE tagged constant table). The surviving signal is
that 0x04 and 0x14 behave as string markers followed by loadString-shaped
payloads. This read-only probe tests the last registered reading: a string
table with NO count/tag prefix — entries are concatenated official
loadString records, each `[varint size][size-1 bytes]`, self-delimiting.

Method:
  For each block, build a bounded candidate-start set
      {0} union {i+1 : tail[i] in (0x04, 0x14), i < MARKER_SCAN}
  (marker+1 = the byte after a string tag, where the size varint would
  begin). From each candidate start, walk concatenated loadString records
  (size capped at MAX_SIZE, record count capped), and record byte coverage
  and record count. Report the per-block BEST candidate, plus the offset-0
  baseline for comparison.

Metrics:
  S1 best coverage   : median best coverage, fraction of blocks whose best
      candidate reaches >= GATE_COVERAGE, and whether the best candidate is
      offset 0 or marker-derived.
  S2 record counts   : median record count at the best candidate.
  S3 offset-0 only   : coverage when forced to start at 0 (comparison).
  S4 body texture    : printable fraction of consumed string-body bytes.

Pre-registered gate: STRING_TABLE_CANDIDATE if the fraction of blocks whose
best candidate reaches >= GATE_COVERAGE is >= GATE_FRAC and median best
record count >= GATE_RECORDS; else STRING_TABLE_PARTIAL. A collapse here is
the terminal description: the region is text/string content not organized as
counted, tagged, length-prefixed, interleaved, recursive, OR prefix-free
concatenated loadString records.

Guardrails: read-only, bounded candidate/record/size caps, fail-closed per
block, deterministic ordering, selftest on synthetic string tables. No
content export, no decryption, no opcode claims.

Usage:
    python probe_string_table.py --selftest
    python probe_string_table.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_postcode_framing import is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

MARKER_SCAN = 64
MAX_CANDIDATES = 12
MAX_RECORDS = 512
MAX_SIZE = 4096
GATE_COVERAGE = 0.90
GATE_FRAC = 0.30
GATE_RECORDS = 3
MARKERS = (0x04, 0x14)


def walk_strings(tail, start):
    """Concatenated [varint size][size-1 bytes] from start."""
    off = start
    total = len(tail)
    records = 0
    body_bytes = 0
    body_print = 0
    while off < total and records < MAX_RECORDS:
        s, n = load_unsigned(tail, off)
        if s is None:
            return {"records": records, "off": off, "reason": "varint_truncated",
                    "body_bytes": body_bytes, "body_print": body_print}
        off += n
        need = 0 if s == 0 else s - 1
        if need > MAX_SIZE or off + need > total:
            return {"records": records, "off": off - n, "reason": "size_or_payload",
                    "body_bytes": body_bytes, "body_print": body_print}
        body = tail[off:off + need]
        body_bytes += need
        body_print += sum(1 for b in body if is_printable(b))
        off += need
        records += 1
    reason = "stream_end" if off >= total else "record_cap"
    return {"records": records, "off": off, "reason": reason,
            "body_bytes": body_bytes, "body_print": body_print}


def candidate_starts(tail):
    starts = [0]
    for i in range(min(MARKER_SCAN, len(tail))):
        if tail[i] in MARKERS:
            starts.append(i + 1)
    # Deduplicate preserving order, cap.
    seen = set()
    out = []
    for s in starts:
        if s not in seen and s <= len(tail):
            seen.add(s)
            out.append(s)
        if len(out) >= MAX_CANDIDATES:
            break
    return out


def best_walk(tail):
    """Return (best_result, best_start, zero_result)."""
    best = None
    best_start = None
    total = len(tail)
    zero = None
    for start in candidate_starts(tail):
        r = walk_strings(tail, start)
        cov = (r["off"] - start) / max(1, total - start)
        r["coverage"] = cov
        r["start"] = start
        if start == 0:
            zero = r
        if best is None or cov > best["coverage"] or \
                (cov == best["coverage"] and r["records"] > best["records"]):
            best = r
            best_start = start
    return best, best_start, zero


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.best_cov = []
        self.best_records = []
        self.high_cov = 0
        self.marker_best = 0
        self.zero_cov = []
        self.body_bytes = 0
        self.body_print = 0

    def add(self, tail):
        self.blocks += 1
        best, best_start, zero = best_walk(tail)
        self.best_cov.append(best["coverage"])
        self.best_records.append(best["records"])
        if best["coverage"] >= GATE_COVERAGE:
            self.high_cov += 1
        if best_start != 0:
            self.marker_best += 1
        if zero is not None:
            self.zero_cov.append(zero["coverage"])
        self.body_bytes += best["body_bytes"]
        self.body_print += best["body_print"]


def summarize(acc):
    n = max(1, acc.blocks)
    bc = sorted(acc.best_cov)
    br = sorted(acc.best_records)
    zc = sorted(acc.zero_cov)
    return {
        "blocks": acc.blocks,
        "best_cov_median": bc[len(bc) // 2] if bc else 0.0,
        "best_records_median": br[len(br) // 2] if br else 0,
        "high_cov_frac": acc.high_cov / n,
        "marker_best_frac": acc.marker_best / n,
        "zero_cov_median": zc[len(zc) // 2] if zc else 0.0,
        "body_print_frac": acc.body_print / max(1, acc.body_bytes),
    }


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# S1 blocks={s['blocks']} best_cov_median={s['best_cov_median']:.3f} "
          f"high_cov_frac(>={GATE_COVERAGE})={s['high_cov_frac']:.3f} "
          f"marker_best_frac={s['marker_best_frac']:.3f}")
    print(f"# S2 best_records_median={s['best_records_median']}")
    print(f"# S3 zero_cov_median={s['zero_cov_median']:.3f}")
    print(f"# S4 body_print_frac={s['body_print_frac']:.3f}")


def gate(s):
    if s["high_cov_frac"] >= GATE_FRAC \
            and s["best_records_median"] >= GATE_RECORDS:
        return "STRING_TABLE_CANDIDATE"
    return "STRING_TABLE_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    acc = Accumulator()
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:]
        if not tail:
            continue
        acc.add(tail)
        seen += 1
    s = summarize(acc)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Prefix-free concatenated strings: size 3 "ab" (size-1=2), size 2 "x",
    # size 0 empty. Varint sizes: 0x83, 0x82, 0x80.
    tail = bytes([0x83]) + b"ab" + bytes([0x82]) + b"x" + bytes([0x80])
    r = walk_strings(tail, 0)
    assert r["records"] == 3 and r["reason"] == "stream_end", r
    assert r["off"] == len(tail)
    # Marker-derived start: leading junk byte, then a 0x04 tag, then strings.
    tail2 = bytes([0x72, 0x04, 0x83]) + b"ab" + bytes([0x82]) + b"x"
    best, best_start, zero = best_walk(tail2)
    assert best_start == 2, best_start            # right after the 0x04 marker
    assert best["reason"] == "stream_end", best
    assert best["records"] == 2, best
    assert zero["coverage"] < best["coverage"]
    # Unreasonable size rejected: varint 0x21 0x80 = 4224 > MAX_SIZE.
    r3 = walk_strings(bytes([0x21, 0x80]), 0)
    assert r3["reason"] == "size_or_payload" and r3["records"] == 0, r3
    # Truncated payload.
    r4 = walk_strings(bytes([0x89]) + b"ab", 0)
    assert r4["reason"] == "size_or_payload", r4
    # No varint (text run).
    r5 = walk_strings(b"a" * 12, 0)
    assert r5["reason"] == "varint_truncated", r5
    # Accumulator + gate plumbing.
    acc = Accumulator()
    acc.add(tail)
    acc.add(tail2)
    s = summarize(acc)
    assert s["high_cov_frac"] == 1.0, s
    assert s["best_records_median"] >= 2, s
    assert gate(s) == "STRING_TABLE_CANDIDATE"
    assert gate({**s, "high_cov_frac": 0.1}) == "STRING_TABLE_PARTIAL"
    assert gate({**s, "best_records_median": 1}) == "STRING_TABLE_PARTIAL"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AF string table probe")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("mpkinfo", nargs="?")
    ap.add_argument("mpk", nargs="?")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not args.mpkinfo or not args.mpk:
        ap.error("mpkinfo and mpk required (or --selftest)")
    try:
        return probe(args.mpkinfo, args.mpk, args.limit)
    except (OSError, ValueError, IndexError, struct.error) as exc:
        print(f"# string table probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
