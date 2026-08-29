#!/usr/bin/env python3
"""
probe_head_length.py — H-NEX-003AD: head varint vs tail length census.

H-NEX-003AC showed the control-aware walk dies at the first token in ~98%
of blocks: ~48% start with a run of bytes that never forms a varint
(varint_truncated), ~50% parse a head varint whose v-1 payload overflows
the tail (payload_truncated). Coverage median ~ 0 falsified the
interleaved grammar as a full-stream tokenizer. One reading remains open:
the head varint may not be a tag at all in most blocks but a LENGTH field
for the post-code section. This read-only probe classifies the relation
between the head varint value v and the available tail length:

  H1 parse census      : fraction of blocks whose head varint parses; for
      the rest, the offset of the first MSB-set byte (>= 0x80) within the
      first MSB_SCAN bytes — the earliest position any official varint
      could terminate.
  H2 fit classes       : for parsed heads with n varint bytes and tail
      length L: exact (v-1 == L-n), overflow (v-1 > L-n), underflow
      (v-1 < L-n).
  H3 overflow anatomy  : split by v <= TAG_MAX (known tag family with a
      tail too short for its payload) vs v > TAG_MAX; capped histogram of
      the excess delta = (v-1) - (L-n).
  H4 underflow anatomy : capped histogram of the residual
      (L-n) - (v-1); byte class at the record-end position.

Pre-registered gate: HEAD_LENGTH_CANDIDATE if, among parsed-head blocks,
exact + overflow with delta <= OFF_BY + underflow with residual <= OFF_BY
cover >= GATE_LEN_FRAC — i.e. the head varint tracks the section length
within 2 bytes; else HEAD_LENGTH_PARTIAL.

Guardrails: read-only, bounded scans, fail-closed per block, deterministic
ordering, selftest on synthetic heads. No content export, no decryption,
no opcode claims.

Usage:
    python probe_head_length.py --selftest
    python probe_head_length.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_interleaved_walk import TAG_MAX
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

MSB_SCAN = 64
OFF_BY = 2
GATE_LEN_FRAC = 0.50
HIST_CAP = 32


def first_msb(tail):
    """Offset of first byte >= 0x80 within MSB_SCAN, else None."""
    for i in range(min(MSB_SCAN, len(tail))):
        if tail[i] >= 0x80:
            return i
    return None


def byte_kind(b):
    if b < 0x20:
        return "control"
    if b < 0x7F:
        return "printable"
    return "high"


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.no_varint = 0
        self.msb_offset = collections.Counter()
        self.fit = collections.Counter()
        self.overflow_tag = 0
        self.overflow_big = 0
        self.delta_hist = collections.Counter()
        self.residual_hist = collections.Counter()
        self.end_byte = collections.Counter()

    def add(self, tail):
        self.blocks += 1
        v, n = load_unsigned(tail, 0)
        if v is None:
            self.no_varint += 1
            off = first_msb(tail)
            self.msb_offset[off if off is not None else MSB_SCAN + 1] += 1
            return
        remaining = len(tail) - n
        need = 0 if v == 0 else v - 1
        if need == remaining:
            self.fit["exact"] += 1
        elif need > remaining:
            self.fit["overflow"] += 1
            if v <= TAG_MAX:
                self.overflow_tag += 1
            else:
                self.overflow_big += 1
            self.delta_hist[min(need - remaining, HIST_CAP)] += 1
        else:
            self.fit["underflow"] += 1
            self.residual_hist[min(remaining - need, HIST_CAP)] += 1
            end = n + need
            if end < len(tail):
                self.end_byte[byte_kind(tail[end])] += 1


def summarize(acc):
    n = max(1, acc.blocks)
    parsed = acc.blocks - acc.no_varint
    p = max(1, parsed)
    exact = acc.fit["exact"]
    near_overflow = sum(c for d, c in acc.delta_hist.items() if d <= OFF_BY)
    near_underflow = sum(c for d, c in acc.residual_hist.items()
                         if d <= OFF_BY)
    return {
        "blocks": acc.blocks,
        "parsed_frac": parsed / n,
        "no_varint": acc.no_varint,
        "msb_offset_top": acc.msb_offset.most_common(8),
        "fit": dict(acc.fit),
        "overflow_tag": acc.overflow_tag,
        "overflow_big": acc.overflow_big,
        "delta_hist": dict(sorted(acc.delta_hist.items())),
        "residual_hist": dict(sorted(acc.residual_hist.items())),
        "end_byte": dict(acc.end_byte),
        "near_len_frac": (exact + near_overflow + near_underflow) / p,
    }


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# H1 blocks={s['blocks']} parsed_frac={s['parsed_frac']:.3f} "
          f"no_varint={s['no_varint']} msb_offset_top={s['msb_offset_top']}")
    print(f"# H2 fit={s['fit']}")
    print(f"# H3 overflow: tag_family(v<={TAG_MAX})={s['overflow_tag']} "
          f"big={s['overflow_big']} delta_hist={s['delta_hist']}")
    print(f"# H4 underflow residual_hist={s['residual_hist']} "
          f"end_byte={s['end_byte']}")
    print(f"# near-length share (exact + off-by<={OFF_BY}) = "
          f"{s['near_len_frac']:.3f}")


def gate(s):
    if s["near_len_frac"] >= GATE_LEN_FRAC:
        return "HEAD_LENGTH_CANDIDATE"
    return "HEAD_LENGTH_PARTIAL"


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
    acc = Accumulator()
    # exact: v=4, n=1, tail length 1+3 -> need 3 == remaining 3.
    acc.add(bytes([0x84]) + b"abc")
    # overflow by 1: v=6 need 5, remaining 4.
    acc.add(bytes([0x86]) + b"abcd")
    # underflow by 1: v=2 need 1, remaining 2; end byte control.
    acc.add(bytes([0x82]) + b"x" + bytes([0x04]))
    # no varint: 70 printable bytes, first MSB at offset 64+ -> capped.
    acc.add(b"a" * 70)
    # no varint within the 8-byte reader window: 10 low bytes, then a high
    # byte at offset 10. load_unsigned reads bytes 0..7 (all < 0x80) and
    # returns None; first_msb (64-byte scan) still finds the MSB byte at 10.
    acc.add(b"a" * 10 + bytes([0x90]) + b"bc")
    s = summarize(acc)
    assert s["blocks"] == 5, s
    assert s["no_varint"] == 2, s
    assert s["fit"] == {"exact": 1, "overflow": 1, "underflow": 1}, s["fit"]
    assert s["delta_hist"] == {1: 1}, s["delta_hist"]
    assert s["residual_hist"] == {1: 1}, s["residual_hist"]
    assert s["end_byte"] == {"control": 1}, s["end_byte"]
    msb = dict(s["msb_offset_top"])
    assert msb.get(MSB_SCAN + 1) == 1 and msb.get(10) == 1, msb
    # 3 of 3 parsed blocks are within off-by-2 of a length field.
    assert abs(s["near_len_frac"] - 1.0) < 1e-9, s
    assert gate(s) == "HEAD_LENGTH_CANDIDATE"
    assert gate({**s, "near_len_frac": 0.2}) == "HEAD_LENGTH_PARTIAL"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AD head length probe")
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
        print(f"# head length probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
