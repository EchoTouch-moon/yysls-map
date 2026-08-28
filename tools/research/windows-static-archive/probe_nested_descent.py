#!/usr/bin/env python3
"""
probe_nested_descent.py — H-NEX-003AB: bounded recursive descent into
post-code payloads.

H-NEX-003AA showed the flat [varint][v-1 payload] walk fails at level 1
(record-2 boundary) and again at level 2 (one byte past the first internal
control byte), with T1 continuation median = 1 record. That pattern is the
signature of recursion, not of a wrong length convention. This read-only
probe applies the official varint walk recursively inside record payloads:

  D1 depth walk      : P-shape walk ([varint v][v-1 bytes]) applied at
      depth 0 (the block tail) and, depth-capped, inside every record
      payload. Per depth: streams visited, record-count median, fraction of
      streams parsing >= 1 record (conditional survival), and full-consumption
      fraction (does the walk explain every byte of the stream?).
  D2 entry conventions: each record payload spawns up to two child streams —
      E0 from the payload start, E1 from one byte past the first internal
      control byte (< 0x20) inside the payload, generalizing the 003AA T1
      restart from first records to all records.
  D3 tag census      : per-depth top varint values (v <= TAG_MAX) at record
      heads — the vocabulary the next increment must classify.

Pre-registered gate: NESTED_DESCENT_CANDIDATE if some depth d in {1, 2}
and entry convention reaches >= MIN_STREAMS child streams with conditional
ge1_frac >= GATE_GE1_FRAC; else NESTED_DESCENT_PARTIAL. Decisive outcomes:
(a) conditional survival decays smoothly with depth -> nested TLV grammar
confirmed; (b) survival collapses at depth 1 everywhere under both entries
-> control bytes are not record heads, closing the TLV direction.

Bounds: MAX_DEPTH (inclusive depth cap), MAX_UNITS_PER_STREAM, and a
per-block MAX_UNIT_VISITS budget over the whole descent tree. Read-only,
fail-closed per block, deterministic ordering, selftest on a synthetic
nested stream. No content export, no decryption, no opcode claims.

Usage:
    python probe_nested_descent.py --selftest
    python probe_nested_descent.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

TAG_MAX = 4096
MAX_DEPTH = 3
MAX_UNITS_PER_STREAM = 32
MAX_UNIT_VISITS = 256
MIN_STREAMS = 100
GATE_GE1_FRAC = 0.30


def walk_stream(stream):
    """P-shape walk; returns list of (v, payload_start, payload_end)."""
    off = 0
    recs = []
    total = len(stream)
    while off < total and len(recs) < MAX_UNITS_PER_STREAM:
        v, n = load_unsigned(stream, off)
        if v is None:
            break
        need = 0 if v == 0 else v - 1
        if off + n + need > total:
            break
        recs.append((v, off + n, off + n + need))
        off += n + need
    return recs, off


def first_control(payload):
    for i, b in enumerate(payload):
        if b < 0x20:
            return i
    return None


class DepthStats:
    def __init__(self):
        self.streams = 0
        self.ge1 = 0
        self.full = 0
        self.records = []
        self.tags = collections.Counter()

    def note(self, recs, consumed, stream_len):
        self.streams += 1
        self.records.append(len(recs))
        if recs:
            self.ge1 += 1
        if consumed == stream_len:
            self.full += 1
        for v, _, _ in recs:
            if v <= TAG_MAX:
                self.tags[v] += 1


def descend(tail):
    """Walk the tree; returns {(depth, entry): DepthStats}."""
    stats = collections.defaultdict(DepthStats)
    budget = [MAX_UNIT_VISITS]

    def visit(stream, depth, entry):
        if depth > MAX_DEPTH or budget[0] <= 0 or not stream:
            return
        recs, consumed = walk_stream(stream)
        st = stats[(depth, entry)]
        st.note(recs, consumed, len(stream))
        for v, ps, pe in recs:
            if budget[0] <= 0:
                return
            budget[0] -= 1
            payload = stream[ps:pe]
            if not payload or depth == MAX_DEPTH:
                continue
            visit(payload, depth + 1, "E0")
            t = first_control(payload)
            if t is not None and t + 1 < len(payload):
                visit(payload[t + 1:], depth + 1, "E1")

    visit(tail, 0, "head")
    return stats


def summarize(all_stats):
    out = {}
    for key in sorted(all_stats):
        st = all_stats[key]
        n = max(1, st.streams)
        recs = sorted(st.records)
        out[key] = {
            "streams": st.streams,
            "records_median": recs[len(recs) // 2] if recs else 0,
            "ge1_frac": st.ge1 / n,
            "full_frac": st.full / n,
            "tags_top": st.tags.most_common(8),
        }
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    for key in sorted(s):
        depth, entry = key
        r = s[key]
        print(f"# [depth={depth} entry={entry}] streams={r['streams']} "
              f"records_median={r['records_median']} "
              f"ge1_frac={r['ge1_frac']:.3f} full_frac={r['full_frac']:.3f}")
        print(f"#    tags_top={r['tags_top']}")


def gate(s):
    for (depth, entry), r in s.items():
        if depth in (1, 2) and entry in ("E0", "E1") \
                and r["streams"] >= MIN_STREAMS \
                and r["ge1_frac"] >= GATE_GE1_FRAC:
            return "NESTED_DESCENT_CANDIDATE"
    return "NESTED_DESCENT_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    all_stats = collections.defaultdict(DepthStats)
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:]
        if not tail:
            continue
        seen += 1
        block_stats = descend(tail)
        for key, st in block_stats.items():
            tgt = all_stats[key]
            tgt.streams += st.streams
            tgt.ge1 += st.ge1
            tgt.full += st.full
            tgt.records.extend(st.records)
            tgt.tags.update(st.tags)
    s = summarize(all_stats)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Nested synthetic stream: head record v=6 whose 5-byte payload holds
    # two records [v=2]['x'] and [v=3]['a','b'].
    payload1 = bytes([0x82]) + b"x" + bytes([0x83]) + b"ab"
    tail = bytes([0x86]) + payload1
    assert len(payload1) == 5
    stats = descend(tail)
    assert stats[(0, "head")].streams == 1
    assert stats[(0, "head")].records == [1], stats[(0, "head")].records
    assert stats[(0, "head")].full == 1
    e0 = stats[(1, "E0")]
    assert e0.streams == 1 and e0.records == [2], (e0.streams, e0.records)
    assert dict(e0.tags) == {2: 1, 3: 1}, e0.tags
    # E1 entry: payload opens with a control byte, then a record.
    payload2 = bytes([0x00, 0x82]) + b"y" + bytes([0x80])
    tail2 = bytes([0x85]) + payload2
    assert len(payload2) == 4
    stats2 = descend(tail2)
    e0_2 = stats2[(1, "E0")]
    e1_2 = stats2[(1, "E1")]
    assert e0_2.streams == 1 and e0_2.records[0] >= 1, e0_2.records
    assert e1_2.streams == 1 and e1_2.records == [2], e1_2.records
    # Depth cap: records inside depth-MAX_DEPTH payloads are not visited.
    inner = bytes([0x82]) + b"z"
    mid_payload = bytes([len(inner) + 1 | 0x80]) + inner
    deep = mid_payload
    for _ in range(MAX_DEPTH):
        deep = bytes([len(deep) + 1 | 0x80]) + deep
    stats3 = descend(deep)
    assert all(d <= MAX_DEPTH for d, _ in stats3), sorted(stats3)
    # Summarize + gate plumbing.
    s = summarize(stats)
    assert s[(1, "E0")]["ge1_frac"] == 1.0
    g = gate({(1, "E0"): {"streams": 200, "ge1_frac": 0.4}})
    assert g == "NESTED_DESCENT_CANDIDATE", g
    g = gate({(1, "E0"): {"streams": 200, "ge1_frac": 0.2}})
    assert g == "NESTED_DESCENT_PARTIAL", g
    g = gate({(1, "E0"): {"streams": 50, "ge1_frac": 0.9}})
    assert g == "NESTED_DESCENT_PARTIAL", g
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AB nested descent probe")
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
        print(f"# nested descent probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
