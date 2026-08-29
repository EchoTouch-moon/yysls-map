#!/usr/bin/env python3
"""
probe_constant_table.py — H-NEX-003AE: official Lua 5.4 constant-table walk
at code_end.

Four full-stream models of the post-code section have been rejected
(003Y/003Z/003AA flat records, 003AB pure recursion, 003AC interleaved
tokenizer, 003AD length prefix). This read-only probe tests the remaining
structural reading: the region is the proto's constant table in official
loadConstant layout:

    sizek = loadUnsigned
    sizek x [tag byte][value]

with official dumped tag values (Lua 5.4 lobject.h makevariant):
    0x00 nil, 0x01 false, 0x11 true, 0x03 float (8 B), 0x13 int (8 B),
    0x04 short string, 0x14 long string; strings via official loadString
    (varint size s; s == 0 empty, else s-1 bytes).

Note the coincidence with the 003AC framing census: the dominant framing
bytes were 0x04 (successor parse 0.94-0.97) and 0x14 (0.61-0.80) — the
official short/long string tags — and the "record" after them had exactly
the loadString shape [varint][v-1].

Metrics:
  C1 outcome census : full_consumed (all sizek constants parsed AND the
      tail is exhausted) / constants_complete (all parsed, bytes remain) /
      truncated / bad_tag / no_sizek / sizek_unreasonable (sizek > cap).
  C2 sizek census   : capped histogram of sizek values; constants actually
      consumed before a stop.
  C3 tag histogram  : tag-byte frequencies over all consumed constants.
  C4 string texture : printable fraction of short/long string bodies.
  C5 leftover byte  : for constants_complete blocks, classify the first
      byte after the table (the sizeupval / next-section candidate).

Pre-registered gate: CONSTANT_TABLE_CANDIDATE if constants_complete +
full_consumed >= GATE_COMPLETE_FRAC of blocks AND the official tag share
>= GATE_TAG_SHARE; else CONSTANT_TABLE_PARTIAL.

Guardrails: read-only, MAX_CONST cap (fail-closed), bounded reads,
deterministic ordering, selftest on synthetic constant tables. No content
export, no decryption, no opcode claims.

Usage:
    python probe_constant_table.py --selftest
    python probe_constant_table.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_postcode_framing import is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

MAX_CONST = 4096
OFFICIAL_TAGS = {0x00, 0x01, 0x11, 0x03, 0x13, 0x04, 0x14}
GATE_COMPLETE_FRAC = 0.50
GATE_TAG_SHARE = 0.90
HIST_CAP = 32


def walk_constants(tail):
    """Official loadConstant walk. Returns outcome dict."""
    sizek, n = load_unsigned(tail, 0)
    if sizek is None:
        return {"outcome": "no_sizek", "consumed": 0, "tags": [],
                "str_bytes": 0, "str_printable": 0}
    if sizek > MAX_CONST:
        return {"outcome": "sizek_unreasonable", "consumed": 0, "tags": [],
                "sizek": sizek, "str_bytes": 0, "str_printable": 0}
    off = n
    tags = []
    str_bytes = str_printable = 0
    total = len(tail)
    for _ in range(sizek):
        if off >= total:
            return {"outcome": "truncated", "consumed": len(tags),
                    "sizek": sizek, "tags": tags, "off": off,
                    "str_bytes": str_bytes, "str_printable": str_printable}
        t = tail[off]
        off += 1
        tags.append(t)
        if t in (0x00, 0x01, 0x11):
            continue
        if t in (0x03, 0x13):
            if off + 8 > total:
                return {"outcome": "truncated", "consumed": len(tags),
                        "sizek": sizek, "tags": tags, "off": off,
                        "str_bytes": str_bytes,
                        "str_printable": str_printable}
            off += 8
            continue
        if t in (0x04, 0x14):
            s, m = load_unsigned(tail, off)
            if s is None:
                return {"outcome": "truncated", "consumed": len(tags),
                        "sizek": sizek, "tags": tags, "off": off,
                        "str_bytes": str_bytes,
                        "str_printable": str_printable}
            off += m
            need = 0 if s == 0 else s - 1
            if off + need > total:
                return {"outcome": "truncated", "consumed": len(tags),
                        "sizek": sizek, "tags": tags, "off": off,
                        "str_bytes": str_bytes,
                        "str_printable": str_printable}
            body = tail[off:off + need]
            str_bytes += need
            str_printable += sum(1 for b in body if is_printable(b))
            off += need
            continue
        return {"outcome": "bad_tag", "consumed": len(tags) - 1,
                "sizek": sizek, "tags": tags, "off": off, "bad": t,
                "str_bytes": str_bytes, "str_printable": str_printable}
    outcome = "full_consumed" if off == total else "constants_complete"
    return {"outcome": outcome, "consumed": len(tags), "sizek": sizek,
            "tags": tags, "off": off, "next_byte": tail[off] if off < total else None,
            "str_bytes": str_bytes, "str_printable": str_printable}


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.outcomes = collections.Counter()
        self.sizek_hist = collections.Counter()
        self.consumed_hist = collections.Counter()
        self.tag_hist = collections.Counter()
        self.bad_tag_hist = collections.Counter()
        self.str_bytes = 0
        self.str_printable = 0
        self.coverage = []
        self.next_byte = collections.Counter()

    def add(self, tail):
        self.blocks += 1
        r = walk_constants(tail)
        self.outcomes[r["outcome"]] += 1
        if "sizek" in r:
            self.sizek_hist[min(r["sizek"], HIST_CAP)] += 1
        if r["tags"]:
            self.consumed_hist[min(len(r["tags"]), HIST_CAP)] += 1
        for t in r["tags"]:
            self.tag_hist[t] += 1
        if r["outcome"] == "bad_tag":
            self.bad_tag_hist[r["bad"]] += 1
        self.str_bytes += r["str_bytes"]
        self.str_printable += r["str_printable"]
        if r["outcome"] in ("constants_complete", "full_consumed"):
            self.coverage.append(r["off"] / len(tail))
            if r.get("next_byte") is not None:
                self.next_byte[r["next_byte"]] += 1


def summarize(acc):
    n = max(1, acc.blocks)
    complete = acc.outcomes["constants_complete"] + acc.outcomes["full_consumed"]
    total_tags = sum(acc.tag_hist.values())
    official = sum(c for t, c in acc.tag_hist.items() if t in OFFICIAL_TAGS)
    cov = sorted(acc.coverage)
    return {
        "blocks": acc.blocks,
        "outcomes": dict(acc.outcomes),
        "complete_frac": complete / n,
        "sizek_hist": dict(sorted(acc.sizek_hist.items())),
        "consumed_hist": dict(sorted(acc.consumed_hist.items())),
        "tag_top": acc.tag_hist.most_common(12),
        "official_tag_share": official / max(1, total_tags),
        "bad_tag_top": acc.bad_tag_hist.most_common(8),
        "str_printable_frac": acc.str_printable / max(1, acc.str_bytes),
        "coverage_median": cov[len(cov) // 2] if cov else 0.0,
        "next_byte_top": acc.next_byte.most_common(8),
    }


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# C1 blocks={s['blocks']} outcomes={s['outcomes']} "
          f"complete_frac={s['complete_frac']:.3f}")
    print(f"# C2 sizek_hist={s['sizek_hist']} consumed_hist={s['consumed_hist']}")
    print(f"# C3 tag_top={[(hex(t), c) for t, c in s['tag_top']]} "
          f"official_share={s['official_tag_share']:.3f}")
    print(f"#    bad_tag_top={[(hex(t), c) for t, c in s['bad_tag_top']]}")
    print(f"# C4 string printable_frac={s['str_printable_frac']:.3f}")
    print(f"# C5 coverage_median={s['coverage_median']:.3f} "
          f"next_byte_top={[(hex(b), c) for b, c in s['next_byte_top']]}")


def gate(s):
    if s["complete_frac"] >= GATE_COMPLETE_FRAC \
            and s["official_tag_share"] >= GATE_TAG_SHARE:
        return "CONSTANT_TABLE_CANDIDATE"
    return "CONSTANT_TABLE_PARTIAL"


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
    # full_consumed: sizek=2, short string "ab" then nil.
    tail = bytes([0x82, 0x04, 0x83]) + b"ab" + bytes([0x00])
    r = walk_constants(tail)
    assert r["outcome"] == "full_consumed", r
    assert r["tags"] == [0x04, 0x00], r
    assert r["str_bytes"] == 2 and r["str_printable"] == 2
    # constants_complete with a leftover byte.
    tail2 = tail + bytes([0x80])
    r2 = walk_constants(tail2)
    assert r2["outcome"] == "constants_complete", r2
    assert r2["next_byte"] == 0x80
    # int constant consumes 8 bytes.
    tail3 = bytes([0x81, 0x13]) + bytes(8)
    assert walk_constants(tail3)["outcome"] == "full_consumed"
    # empty string: size 0.
    tail4 = bytes([0x81, 0x04, 0x80])
    r4 = walk_constants(tail4)
    assert r4["outcome"] == "full_consumed" and r4["str_bytes"] == 0, r4
    # bad tag.
    r5 = walk_constants(bytes([0x81, 0x55]))
    assert r5["outcome"] == "bad_tag" and r5["bad"] == 0x55, r5
    # truncated: string size overruns.
    r6 = walk_constants(bytes([0x81, 0x04, 0x89]) + b"ab")
    assert r6["outcome"] == "truncated", r6
    # no_sizek: 8 low bytes (varint window exhausted).
    r7 = walk_constants(b"a" * 12)
    assert r7["outcome"] == "no_sizek", r7
    # sizek_unreasonable: varint 0x21 0x80 = 4224 > MAX_CONST.
    r8 = walk_constants(bytes([0x21, 0x80]))
    assert r8["outcome"] == "sizek_unreasonable", r8
    # Accumulator + gate plumbing.
    acc = Accumulator()
    acc.add(tail)
    acc.add(tail2)
    s = summarize(acc)
    assert s["complete_frac"] == 1.0, s
    assert s["official_tag_share"] == 1.0, s
    assert gate(s) == "CONSTANT_TABLE_CANDIDATE"
    assert gate({**s, "complete_frac": 0.1}) == "CONSTANT_TABLE_PARTIAL"
    assert gate({**s, "official_tag_share": 0.5}) == "CONSTANT_TABLE_PARTIAL"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AE constant table probe")
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
        print(f"# constant table probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
