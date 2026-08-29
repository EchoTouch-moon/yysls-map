#!/usr/bin/env python3
"""
probe_segment_split.py — H-NEX-003X: post-code segment split on delimiter
candidates.

H-NEX-003W found that the region after code_end is dense interleaved
identifier-style text with no fixed header and no boundary-aligned length
prefixes, and that 0x04 terminates 42-44% of longest printable runs across
all three frozen archives (then 0x00, 0x12, 0x09). This read-only probe
tests whether splitting the tail on those delimiter candidates yields a
deterministic segment grammar:

  X1 segment purity   : for each bounded delimiter hypothesis, the fraction
      of segments that are pure printable ASCII and the fraction that are
      identifier-like (>= 90% printable, len >= 3).
  X2 segment length   : capped length histogram and median — a grammar with
      length-prefixed fields would show structure; pure noise would not.
  X3 segment leading bytes : for non-pure segments, first-byte concentration
      and (first, second) byte bigrams — recurring tags imply a tag/length
      record grammar between text runs.
  X4 intra-segment bytes : byte-value histogram of non-pure segment bodies
      to detect further delimiter candidates.
  X5 tail start       : fraction of blocks whose tail begins with a
      delimiter byte (leading-marker hypothesis) vs. with segment content.

Delimiter hypotheses (bounded, from H-NEX-003W run-terminator histogram):
    D0 = {0x04}
    D1 = {0x04, 0x00}
    D2 = {0x04, 0x00, 0x12, 0x09}

Guardrails: read-only, bounded TAIL_SCAN window, fail-closed per block,
deterministic ordering, selftest on a synthetic tail. No content export,
no decryption, no opcode claims.

Usage:
    python probe_segment_split.py --selftest
    python probe_segment_split.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_postcode_framing import TAIL_SCAN, is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader

IDENT_PRINTABLE_FRAC = 0.9
IDENT_MIN_LEN = 3
LEN_HIST_CAP = 32
MAX_SEGS_PER_BLOCK = 256
MIN_TOTAL_SEGMENTS = 1000
GATE_PURE_FRAC = 0.7

DELIM_HYPOTHESES = (
    ("D0_0x04", frozenset((0x04,))),
    ("D1_0x04_0x00", frozenset((0x04, 0x00))),
    ("D2_top4", frozenset((0x04, 0x00, 0x12, 0x09))),
)


def split_segments(tail, delims):
    """Split tail on delimiter bytes. Returns (segments, empty_gaps)."""
    segs = []
    gaps = 0
    start = None
    prev_delim = False
    for i, b in enumerate(tail):
        if b in delims:
            if start is not None:
                segs.append((start, i - start))
                start = None
            elif prev_delim or i == 0:
                gaps += 1
            prev_delim = True
        else:
            if start is None:
                start = i
            prev_delim = False
    if start is not None:
        segs.append((start, len(tail) - start))
    return segs[:MAX_SEGS_PER_BLOCK], gaps


def classify_segment(body):
    length = len(body)
    printable = sum(1 for b in body if is_printable(b))
    frac = printable / length
    if frac == 1.0:
        return "pure"
    if frac >= IDENT_PRINTABLE_FRAC and length >= IDENT_MIN_LEN:
        return "ident"
    return "other"


class HypothesisAcc:
    def __init__(self):
        self.segments = 0
        self.empty_gaps = 0
        self.klass = collections.Counter()
        self.length_hist = collections.Counter()
        self.lengths = []
        self.other_lead = collections.Counter()
        self.other_bigram = collections.Counter()
        self.other_body_bytes = collections.Counter()
        self.tail_starts_delim = 0
        self.blocks = 0

    def add_block(self, tail, delims):
        if not tail:
            return
        self.blocks += 1
        if tail[0] in delims:
            self.tail_starts_delim += 1
        segs, gaps = split_segments(tail, delims)
        self.empty_gaps += gaps
        for start, length in segs:
            body = tail[start:start + length]
            self.segments += 1
            klass = classify_segment(body)
            self.klass[klass] += 1
            self.length_hist[min(length, LEN_HIST_CAP)] += 1
            self.lengths.append(min(length, LEN_HIST_CAP))
            if klass == "other":
                self.other_lead[body[0]] += 1
                if length >= 2:
                    self.other_bigram[(body[0], body[1])] += 1
                for b in body:
                    if not is_printable(b):
                        self.other_body_bytes[b] += 1


def summarize(accs):
    out = {}
    for name, acc in accs.items():
        n = max(1, acc.segments)
        lengths = sorted(acc.lengths)
        out[name] = {
            "blocks": acc.blocks,
            "segments": acc.segments,
            "empty_gaps": acc.empty_gaps,
            "segs_per_block_median":
                lengths[len(lengths) // 2] if lengths else 0,
            "pure_frac": acc.klass["pure"] / n,
            "ident_frac": acc.klass["ident"] / n,
            "other_frac": acc.klass["other"] / n,
            "length_hist": dict(sorted(acc.length_hist.items())),
            "tail_starts_delim_frac":
                acc.tail_starts_delim / max(1, acc.blocks),
            "other_lead_top": [(hex(b), c)
                               for b, c in acc.other_lead.most_common(8)],
            "other_bigram_top": [
                (f"{a:02X} {b:02X}", c)
                for (a, b), c in acc.other_bigram.most_common(8)
            ],
            "other_body_top": [(hex(b), c)
                               for b, c in acc.other_body_bytes.most_common(8)],
        }
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    for hyp, h in s.items():
        print(f"# {hyp}: blocks={h['blocks']} segments={h['segments']} "
              f"empty_gaps={h['empty_gaps']} "
              f"tail_starts_delim_frac={h['tail_starts_delim_frac']:.3f}")
        print(f"#    pure_frac={h['pure_frac']:.3f} ident_frac={h['ident_frac']:.3f} "
              f"other_frac={h['other_frac']:.3f} "
              f"seg_len_median={h['segs_per_block_median']}")
        hist = h["length_hist"]
        shown = {k: v for k, v in hist.items() if k <= 16 or k == LEN_HIST_CAP}
        print(f"#    length_hist(<=16, cap{LEN_HIST_CAP})={shown}")
        print(f"#    other-segment lead bytes: {h['other_lead_top']}")
        print(f"#    other-segment lead bigrams: {h['other_bigram_top']}")
        print(f"#    other-segment non-printable bytes: {h['other_body_top']}")


def gate(s):
    for h in s.values():
        if (h["segments"] >= MIN_TOTAL_SEGMENTS
                and h["pure_frac"] >= GATE_PURE_FRAC):
            return "SEGMENTATION_RULE_CANDIDATE"
    return "SEGMENTATION_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    accs = {name: HypothesisAcc() for name, _ in DELIM_HYPOTHESES}
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:framing["code_end"] + TAIL_SCAN]
        for name, delims in DELIM_HYPOTHESES:
            accs[name].add_block(tail, delims)
        seen += 1
    s = summarize(accs)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Synthetic tail: 0x04-delimited pure segments plus one other segment.
    tail = (b"\x04" + b"abc_def" + b"\x04" + b"ghi.jk"
            + b"\x04" + bytes([0x12, 0xFF]))
    segs, gaps = split_segments(tail, frozenset((0x04,)))
    assert len(segs) == 3 and gaps == 1, (segs, gaps)  # leading delim gap
    assert classify_segment(b"abc_def") == "pure"
    assert classify_segment(b"ab") == "pure"
    assert classify_segment(b"ab_cde\xffghi") == "ident"  # 9/10 printable
    assert classify_segment(bytes([0x12, 0xFF])) == "other"
    acc = HypothesisAcc()
    acc.add_block(tail, frozenset((0x04,)))
    full = summarize({"D0": acc})
    s = full["D0"]
    assert s["segments"] == 3, s
    assert abs(s["pure_frac"] - 2 / 3) < 1e-9, s
    assert abs(s["other_frac"] - 1 / 3) < 1e-9, s
    assert s["tail_starts_delim_frac"] == 1.0, s
    assert s["other_lead_top"][0][0] == "0x12", s["other_lead_top"]
    assert {b for b, _ in s["other_body_top"]} == {"0x12", "0xff"}, s["other_body_top"]
    # gate: below MIN_TOTAL_SEGMENTS stays PARTIAL even at high purity
    assert gate(full) == "SEGMENTATION_PARTIAL"
    # full synthetic block through locate_body
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
    t2 = blk[framing["code_end"]:framing["code_end"] + TAIL_SCAN]
    assert t2 == tail, "code_end must land exactly before the tail"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003X segment split probe")
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
        print(f"# segment split probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
