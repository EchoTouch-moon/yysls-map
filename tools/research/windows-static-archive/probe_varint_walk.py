#!/usr/bin/env python3
"""
probe_varint_walk.py — H-NEX-003Y: varint-led record walk at code_end.

H-NEX-003X falsified the 0x04-as-delimiter hypothesis and observed that
non-pure segments consistently start with MSB-set bytes (0x85-0x91) — the
signature of official Lua 5.4 loadUnsigned varint TERMINAL bytes — and that
0x04 may be a varint continuation byte. This read-only probe tests whether
the tail after code_end parses as a stream of [varint][payload] records:

  shapes:
    S : loadString-style — v == 0 empty record, else v-1 payload bytes, all
        printable ASCII;
    P : permissive       — v == 0 empty record, else v-1 payload bytes, any
        content (bounds only);
    I : integer stream   — record is the varint alone (no payload).

  starts: code_end + 0..8 (bounded set; H-NEX-003X F5 showed tails usually
          open with content, so near-zero starts are the candidates).

Per (shape, start): median record count (cap MAX_RECORDS), fraction of
blocks whose walk consumes the whole window, stop-reason distribution, and
the top varint values seen at record heads.

Pre-registered gate: VARINT_WALK_CANDIDATE if some (shape, start) reaches
full-window coverage in >= 30% of blocks AND median records >= 8;
else VARINT_WALK_PARTIAL.

Guardrails: read-only, bounded TAIL_SCAN window, fail-closed per block,
deterministic ordering, selftest on synthetic varint streams. No content
export, no decryption, no opcode claims.

Usage:
    python probe_varint_walk.py --selftest
    python probe_varint_walk.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_postcode_framing import TAIL_SCAN, is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

MAX_RECORDS = 64
STARTS = range(0, 9)
SHAPES = ("S", "P", "I")
GATE_COVERAGE = 0.30
GATE_MEDIAN_RECORDS = 8


def walk(tail, start, shape):
    """Walk [varint][payload] records. Returns (records, consumed, reason)."""
    off = start
    records = 0
    while off < len(tail) and records < MAX_RECORDS:
        v, n = load_unsigned(tail, off)
        if v is None:
            return records, off - start, "varint_truncated"
        off += n
        if shape != "I":
            need = 0 if v == 0 else v - 1
            if off + need > len(tail):
                return records, off - start, "payload_truncated"
            if shape == "S" and need > 0 and not all(
                    is_printable(b) for b in tail[off:off + need]):
                return records, off - start, "payload_nonprintable"
            off += need
        records += 1
    return records, off - start, ("window_end" if off >= len(tail)
                                  else "record_cap")


class WalkAcc:
    def __init__(self):
        self.records = []
        self.full = 0
        self.blocks = 0
        self.stops = collections.Counter()

    def add(self, records, consumed, reason):
        self.blocks += 1
        self.records.append(min(records, MAX_RECORDS))
        self.stops[reason] += 1
        if reason == "window_end":
            self.full += 1


def summarize(walks, head_values, blocks):
    out = {"blocks": blocks, "walk": {}, "head_values": head_values}
    for key, acc in sorted(walks.items()):
        records = sorted(acc.records)
        out["walk"][key] = {
            "median_records": records[len(records) // 2] if records else 0,
            "full_frac": acc.full / max(1, acc.blocks),
            "stops": dict(acc.stops.most_common()),
        }
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# blocks={s['blocks']}")
    for (shape, start), w in s["walk"].items():
        print(f"# {shape}@+{start}: median_records={w['median_records']} "
              f"full_coverage_frac={w['full_frac']:.3f} stops={w['stops']}")
    print(f"# head varint values at +0 (top 10): {s['head_values']}")


def gate(s):
    for w in s["walk"].values():
        if (w["full_frac"] >= GATE_COVERAGE
                and w["median_records"] >= GATE_MEDIAN_RECORDS):
            return "VARINT_WALK_CANDIDATE"
    return "VARINT_WALK_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    walks = {(shape, start): WalkAcc()
             for shape in SHAPES for start in STARTS}
    head_values = collections.Counter()
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:framing["code_end"] + TAIL_SCAN]
        if not tail:
            continue
        v, _ = load_unsigned(tail, 0)
        if v is not None and v <= 4096:
            head_values[v] += 1
        for shape in SHAPES:
            for start in STARTS:
                if start >= len(tail):
                    continue
                walks[(shape, start)].add(*walk(tail, start, shape))
        seen += 1
    s = summarize(walks, head_values.most_common(10), seen)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Known-good loadString-style stream: v=0, v=2(+1B), v=1, v=5(+4B).
    tail = (bytes([0x80]) + bytes([0x82]) + b"x" + bytes([0x81])
            + bytes([0x85]) + b"abcd")
    r, consumed, reason = walk(tail, 0, "S")
    assert (r, reason) == (4, "window_end"), (r, consumed, reason)
    assert consumed == len(tail), consumed
    r, consumed, reason = walk(tail, 0, "P")
    assert (r, reason) == (4, "window_end"), (r, consumed, reason)
    # Non-printable payload stops shape S but not shape P.
    bad = bytes([0x85]) + b"ab\xffd"
    r, consumed, reason = walk(bad, 0, "S")
    assert reason == "payload_nonprintable" and r == 0, (r, reason)
    r, consumed, reason = walk(bad, 0, "P")
    assert reason == "window_end" and r == 1, (r, reason)
    # Truncated varint and truncated payload fail closed.
    r, consumed, reason = walk(bytes([0x01]), 0, "I")
    assert reason == "varint_truncated" and r == 0, (r, reason)
    r, consumed, reason = walk(bytes([0x85]) + b"ab", 0, "P")
    assert reason == "payload_truncated" and r == 0, (r, reason)
    # Integer stream on a pure varint tail.
    r, consumed, reason = walk(bytes([0x81, 0x82, 0x01, 0xEC]), 0, "I")
    assert (r, reason) == (3, "window_end"), (r, reason)
    # Gate logic: below thresholds stays PARTIAL.
    s = {"walk": {("S", 0): {"full_frac": 0.2, "median_records": 20}}}
    assert gate(s) == "VARINT_WALK_PARTIAL"
    s = {"walk": {("S", 0): {"full_frac": 0.5, "median_records": 9}}}
    assert gate(s) == "VARINT_WALK_CANDIDATE"
    # Full synthetic block through locate_body.
    src = b"@s"
    block = bytearray(0x20)
    block.append(len(src) + 1 | 0x80)
    block.extend(src)
    block.extend(bytes([0x80, 0x80, 0x00, 0x01, 0x05]))
    block.append(0x80 | 2)                     # sizecode = 2
    block.extend(bytes([0x60, 0, 0, 0, 0x0C, 0, 0, 0]))
    block.extend(tail)
    blk = bytes(block)
    framing = locate_body(blk)
    assert blk[framing["code_end"]:] == tail
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003Y varint walk probe")
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
        print(f"# varint walk probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
