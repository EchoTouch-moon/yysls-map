#!/usr/bin/env python3
"""
probe_interleaved_walk.py — H-NEX-003AC: control-aware interleaved walk
over the post-code section.

H-NEX-003AB confirmed control bytes are sub-unit openers (E1 depth-1
survival 0.35-0.38, 3.1-3.9x E0) but rejected pure recursion (depth-2
survival drops to 0.08-0.13; full_frac ~ 0 at every level). This read-only
probe tests the remaining grammar candidate at the top level: a
single-level tokenizer that treats bytes < 0x20 as control tokens and
parses official varint-led [varint v][v-1 payload] records elsewhere:

  T1 coverage        : fraction of blocks whose tail is fully consumed,
      median byte-coverage ratio, and stop-reason census (stream_end /
      varint_truncated / payload_truncated / token_cap).
  T2 control census  : frequency of each control-byte value seen as a
      framing token (not inside payloads — those are skipped by the
      record rule).
  T3 successor parse : per control value, the fraction of occurrences
      where a record parses immediately after it.
  T4 alternation     : token-type transition counts (control/record) and
      per-block token-count median.
  T5 record-tag census: head varint values (v <= TAG_MAX) of record
      tokens under this walk, for comparison with the 003Y census.

Pre-registered gate: INTERLEAVED_WALK_CANDIDATE if median byte coverage
>= GATE_COVERAGE and >= GATE_FULL_FRAC of blocks are fully consumed;
else INTERLEAVED_WALK_PARTIAL. Decisive outcomes: coverage >= 0.90
confirms the interleaved grammar; coverage < 0.50 falsifies it and the
residual bytes become the next census target.

Guardrails: read-only, MAX_TOKENS bound per block, fail-closed per block,
deterministic ordering, selftest on synthetic interleaved streams. No
content export, no decryption, no opcode claims.

Usage:
    python probe_interleaved_walk.py --selftest
    python probe_interleaved_walk.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

TAG_MAX = 4096
MAX_TOKENS = 4096
GATE_COVERAGE = 0.90
GATE_FULL_FRAC = 0.30


def tokenize(tail):
    """Control-aware walk. Returns dict with tokens, consumed, reason."""
    off = 0
    total = len(tail)
    tokens = []
    while off < total and len(tokens) < MAX_TOKENS:
        b = tail[off]
        if b < 0x20:
            tokens.append(("control", b, off))
            off += 1
            continue
        v, n = load_unsigned(tail, off)
        if v is None:
            return {"tokens": tokens, "consumed": off,
                    "reason": "varint_truncated"}
        need = 0 if v == 0 else v - 1
        if off + n + need > total:
            return {"tokens": tokens, "consumed": off,
                    "reason": "payload_truncated"}
        tokens.append(("record", v, off))
        off += n + need
    reason = "stream_end" if off == total else "token_cap"
    return {"tokens": tokens, "consumed": off, "reason": reason}


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.coverage = []
        self.full = 0
        self.reasons = collections.Counter()
        self.control_census = collections.Counter()
        self.control_succ_ok = collections.Counter()
        self.control_succ_n = collections.Counter()
        self.transitions = collections.Counter()
        self.token_counts = []
        self.tags = collections.Counter()

    def add(self, tail):
        self.blocks += 1
        r = tokenize(tail)
        tokens = r["tokens"]
        self.coverage.append(r["consumed"] / len(tail))
        if r["reason"] == "stream_end":
            self.full += 1
        self.reasons[r["reason"]] += 1
        self.token_counts.append(min(len(tokens), MAX_TOKENS))
        prev = "start"
        for i, (kind, val, off) in enumerate(tokens):
            self.transitions[(prev, kind)] += 1
            prev = kind
            if kind == "control":
                self.control_census[val] += 1
                self.control_succ_n[val] += 1
                nxt = tokens[i + 1] if i + 1 < len(tokens) else None
                if nxt is not None and nxt[0] == "record":
                    self.control_succ_ok[val] += 1
            else:
                if val <= TAG_MAX:
                    self.tags[val] += 1


def summarize(acc):
    n = max(1, acc.blocks)
    cov = sorted(acc.coverage)
    counts = sorted(acc.token_counts)
    return {
        "blocks": acc.blocks,
        "coverage_median": cov[len(cov) // 2] if cov else 0.0,
        "full_frac": acc.full / n,
        "reasons": dict(acc.reasons),
        "control_top": acc.control_census.most_common(8),
        "control_succ": [
            (c, acc.control_succ_ok[c], acc.control_succ_n[c])
            for c, _ in acc.control_census.most_common(8)
        ],
        "transitions": dict(acc.transitions),
        "token_count_median": counts[len(counts) // 2] if counts else 0,
        "tags_top": acc.tags.most_common(10),
    }


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# T1 blocks={s['blocks']} coverage_median={s['coverage_median']:.3f} "
          f"full_frac={s['full_frac']:.3f} reasons={s['reasons']}")
    print(f"# T2 control_top={[(hex(c), n) for c, n in s['control_top']]}")
    print("# T3 control successor parse (value, ok, total):")
    for c, ok, tot in s["control_succ"]:
        print(f"#    {hex(c)}: {ok}/{tot} = {ok / max(1, tot):.3f}")
    print(f"# T4 transitions={s['transitions']} "
          f"token_count_median={s['token_count_median']}")
    print(f"# T5 record tags_top={s['tags_top']}")


def gate(s):
    if s["coverage_median"] >= GATE_COVERAGE \
            and s["full_frac"] >= GATE_FULL_FRAC:
        return "INTERLEAVED_WALK_CANDIDATE"
    return "INTERLEAVED_WALK_PARTIAL"


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
    # Fully consumed interleaved stream: C R C R.
    tail = bytes([0x04, 0x83]) + b"ab" + bytes([0x12, 0x82]) + b"x"
    r = tokenize(tail)
    assert r["reason"] == "stream_end", r
    kinds = [t[0] for t in r["tokens"]]
    assert kinds == ["control", "record", "control", "record"], kinds
    assert r["consumed"] == len(tail)
    acc = Accumulator()
    acc.add(tail)
    s = summarize(acc)
    assert s["full_frac"] == 1.0 and s["coverage_median"] == 1.0, s
    assert s["control_top"] == [(0x04, 1), (0x12, 1)] or \
        set(c for c, _ in s["control_top"]) == {0x04, 0x12}, s["control_top"]
    assert all(ok == tot == 1 for _, ok, tot in s["control_succ"]), s
    assert s["transitions"][("start", "control")] == 1
    assert s["transitions"][("control", "record")] == 2
    assert s["transitions"][("record", "control")] == 1
    assert s["tags_top"] == [(3, 1), (2, 1)] or \
        set(t for t, _ in s["tags_top"]) == {2, 3}, s["tags_top"]
    # Payload truncation: record needs 4 bytes, only 1 left.
    r2 = tokenize(bytes([0x04, 0x85]) + b"a")
    assert r2["reason"] == "payload_truncated", r2
    assert r2["consumed"] == 1
    # Varint truncation: continuation byte with no terminator.
    r3 = tokenize(bytes([0x04, 0x61]))
    assert r3["reason"] == "varint_truncated", r3
    assert r3["consumed"] == 1
    # Control run: two consecutive controls.
    r4 = tokenize(bytes([0x04, 0x12, 0x82]) + b"x")
    kinds4 = [t[0] for t in r4["tokens"]]
    assert kinds4 == ["control", "control", "record"], kinds4
    assert r4["reason"] == "stream_end"
    # Gate plumbing.
    assert gate({"coverage_median": 0.95, "full_frac": 0.4}) == \
        "INTERLEAVED_WALK_CANDIDATE"
    assert gate({"coverage_median": 0.6, "full_frac": 0.4}) == \
        "INTERLEAVED_WALK_PARTIAL"
    assert gate({"coverage_median": 0.95, "full_frac": 0.1}) == \
        "INTERLEAVED_WALK_PARTIAL"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AC interleaved walk probe")
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
        print(f"# interleaved walk probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
