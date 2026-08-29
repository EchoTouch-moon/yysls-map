#!/usr/bin/env python3
"""
probe_tag_grammar.py — H-NEX-003Z: tag-grammar record walk on the full block
tail after code_end.

H-NEX-003Y showed that head varint values at code_end form two stable
families — bare small values {5..13, 17, 30} and 512+k values whose
continuation byte is 0x04 (520 = 512+8, 529 = 512+17, 542 = 512+30) — and
that the 256-byte window was provably too short for the 512+k payloads.
This read-only probe re-runs the walk on the FULL block remainder with a
tag-grammar record model:

  shapes:
    S : loadString-style — v == 0 empty record, else v-1 payload bytes, all
        printable ASCII;
    P : permissive       — v == 0 empty record, else v-1 payload bytes, any
        content (bounds only);
    R : raw length       — payload is v bytes (no Lua-style minus one), any
        content (bounds only);
    N : nested           — record is [varint tag][varint m][m payload bytes].

Per shape: median records (cap MAX_RECORDS), fraction of blocks whose walk
consumes the ENTIRE tail, stop-reason distribution, and per-head-tag walk
success profile (the registered discriminator: do v and v+512 share the
same payload-shape success profile?).

Pre-registered gate: TAG_GRAMMAR_CANDIDATE if some shape reaches full-tail
coverage in >= 30% of blocks AND median records >= 8;
else TAG_GRAMMAR_PARTIAL.

Guardrails: read-only, tail bounded by block size (read_block bounds already
applied upstream), fail-closed per block, deterministic ordering, selftest
on synthetic streams. No content export, no decryption, no opcode claims.

Usage:
    python probe_tag_grammar.py --selftest
    python probe_tag_grammar.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_postcode_framing import is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

MAX_RECORDS = 1024
SHAPES = ("S", "P", "R", "N")
TAG_TOP = 10
GATE_COVERAGE = 0.30
GATE_MEDIAN_RECORDS = 8


def walk(tail, shape):
    """Walk [varint tag][payload] records over the full tail.

    Returns (records, consumed, reason).
    """
    off = 0
    records = 0
    total = len(tail)
    while off < total and records < MAX_RECORDS:
        v, n = load_unsigned(tail, off)
        if v is None:
            return records, off, "varint_truncated"
        off += n
        if shape == "N":
            m, n2 = load_unsigned(tail, off)
            if m is None:
                return records, off, "nested_varint_truncated"
            off += n2
            need = m
        elif shape == "R":
            need = v
        else:
            need = 0 if v == 0 else v - 1
        if off + need > total:
            return records, off, "payload_truncated"
        if shape == "S" and need > 0 and not all(
                is_printable(b) for b in tail[off:off + need]):
            return records, off, "payload_nonprintable"
        off += need
        records += 1
    return records, off, ("window_end" if off >= total else "record_cap")


class ShapeAcc:
    def __init__(self):
        self.records = []
        self.full = 0
        self.blocks = 0
        self.stops = collections.Counter()
        # per_tag slots: [full_walk, first_record_ok, blocks]
        self.per_tag = collections.defaultdict(lambda: [0, 0, 0])

    def add(self, records, consumed, reason, head_tag):
        self.blocks += 1
        self.records.append(min(records, MAX_RECORDS))
        self.stops[reason] += 1
        if reason == "window_end":
            self.full += 1
        if head_tag is not None:
            slot = self.per_tag[head_tag]
            slot[2] += 1
            if records >= 1:
                slot[1] += 1
            if reason == "window_end":
                slot[0] += 1


def head_tag(tail):
    v, _ = load_unsigned(tail, 0)
    if v is None or v > 4096:
        return None
    return v


def summarize(accs):
    out = {}
    for shape, acc in accs.items():
        records = sorted(acc.records)
        per_tag = []
        for tag, (full, first_ok, n) in sorted(
                acc.per_tag.items(), key=lambda kv: -kv[1][2])[:TAG_TOP]:
            per_tag.append((tag, n, round(first_ok / n, 3),
                            round(full / n, 3)))
        out[shape] = {
            "blocks": acc.blocks,
            "median_records": records[len(records) // 2] if records else 0,
            "full_frac": acc.full / max(1, acc.blocks),
            "stops": dict(acc.stops.most_common()),
            "per_tag": per_tag,
        }
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    for shape, w in s.items():
        print(f"# {shape}: blocks={w['blocks']} "
              f"median_records={w['median_records']} "
              f"full_coverage_frac={w['full_frac']:.3f}")
        print(f"#    stops={w['stops']}")
        print(f"#    per-tag (tag, blocks, first_ok_frac, full_frac): {w['per_tag']}")


def gate(s):
    for w in s.values():
        if (w["full_frac"] >= GATE_COVERAGE
                and w["median_records"] >= GATE_MEDIAN_RECORDS):
            return "TAG_GRAMMAR_CANDIDATE"
    return "TAG_GRAMMAR_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    accs = {shape: ShapeAcc() for shape in SHAPES}
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:]
        if not tail:
            continue
        tag = head_tag(tail)
        for shape in SHAPES:
            accs[shape].add(*walk(tail, shape), tag)
        seen += 1
    s = summarize(accs)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # S/P walk: v=0 empty, v=2 (+1B), v=1, v=5 (+4B printable).
    tail = (bytes([0x80]) + bytes([0x82]) + b"x" + bytes([0x81])
            + bytes([0x85]) + b"abcd")
    assert walk(tail, "S") == (4, len(tail), "window_end"), walk(tail, "S")
    assert walk(tail, "P") == (4, len(tail), "window_end"), walk(tail, "P")
    # R walk: raw length — v=1 consumes 1 byte, v=2 consumes 2 bytes.
    tail_r = bytes([0x81]) + b"a" + bytes([0x82]) + b"bc"
    assert walk(tail_r, "R") == (2, len(tail_r), "window_end"), walk(tail_r, "R")
    # N walk: [tag 7][m=2][2B] then [tag 3][m=0].
    tail_n = bytes([0x87]) + bytes([0x82]) + b"xy" + bytes([0x83, 0x80])
    assert walk(tail_n, "N") == (2, len(tail_n), "window_end"), walk(tail_n, "N")
    # Non-printable payload stops S but not P.
    bad = bytes([0x85]) + b"ab\xffd"
    assert walk(bad, "S")[2] == "payload_nonprintable"
    assert walk(bad, "P")[2] == "window_end"
    # Truncation fails closed.
    assert walk(bytes([0x01]), "P")[2] == "varint_truncated"
    assert walk(bytes([0x85]) + b"ab", "P")[2] == "payload_truncated"
    assert walk(bytes([0x85]), "N")[2] == "nested_varint_truncated"
    # Long payload (519 bytes, the 512+k family case) walks when the full
    # tail is available.
    long_tail = bytes([0x04, 0x88]) + b"z" * 519  # v = 520 -> need 519
    assert walk(long_tail, "P") == (1, len(long_tail), "window_end")
    assert walk(long_tail[:100], "P")[2] == "payload_truncated"
    # Gate logic.
    assert gate({"P": {"full_frac": 0.2, "median_records": 20}}) == \
        "TAG_GRAMMAR_PARTIAL"
    assert gate({"P": {"full_frac": 0.5, "median_records": 9}}) == \
        "TAG_GRAMMAR_CANDIDATE"
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
    ap = argparse.ArgumentParser(description="H-NEX-003Z tag grammar probe")
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
        print(f"# tag grammar probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
