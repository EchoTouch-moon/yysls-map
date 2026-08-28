#!/usr/bin/env python3
"""
probe_record_boundary.py — H-NEX-003AA: first-record boundary test
(length vs terminator) and record-2 continuation walk.

H-NEX-003Z showed the first [varint v][v-1 payload] unit after code_end
consumes almost everywhere, but the walk dies at the record-2 boundary.
This read-only probe dissects that boundary:

  B1 terminator agreement : offset t of the first control byte (< 0x20)
      after the payload start, compared with v-1 and v. t == v-1 confirms
      the official loadString length with an explicit terminator.
  B2 record-2 byte class  : classify the byte at L1 = n+(v-1) and
      L2 = n+v (control / printable / MSB-set) and try to parse a varint
      there — which convention lands on a record head?
  B3 continuation walk    : restart a permissive [varint][m-1 bytes] walk
      at L1 and at L2; report median records and the fraction of blocks
      reaching >= CONT_OK records. If the stream walks from record 2, the
      first unit is a section header and the rest is homogeneous.
  B4 terminator restart   : when a control byte falls INSIDE the nominal
      payload (t < v-1), also restart the continuation walk at T0 = n+t
      (the control byte) and T1 = n+t+1 (just past it) — the control byte
      may be a nested-record head rather than raw payload.

Families: bare head values (v < 512) vs the 0x04-continuation family
(v >= 512), reported separately.

Pre-registered gate: RECORD_BOUNDARY_CANDIDATE if some convention (L1 or
L2) yields >= CONT_OK continuation records in >= GATE_CONT_FRAC of blocks
with a parsed head varint; else RECORD_BOUNDARY_PARTIAL.

Guardrails: read-only, tail bounded by block size, fail-closed per block,
deterministic ordering, selftest on synthetic boundaries. No content
export, no decryption, no opcode claims.

Usage:
    python probe_record_boundary.py --selftest
    python probe_record_boundary.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_postcode_framing import is_printable
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

HEAD_TAG_MAX = 4096
CONT_MAX_RECORDS = 64
CONT_OK = 3
GATE_CONT_FRAC = 0.30
TERM_EXTRA = 16


def is_control(b):
    return b < 0x20


def byte_class(b):
    if b < 0x20:
        return "control"
    if b < 0x7F:
        return "printable"
    return "high"


def terminator_offset(tail, payload_start, v):
    """Offset (relative to payload start) of first control byte, or None."""
    window = min(len(tail), payload_start + v + TERM_EXTRA)
    for i in range(payload_start, window):
        if is_control(tail[i]):
            return i - payload_start
    return None


def continuation(tail, start):
    """Permissive [varint][m-1] walk from start; returns record count."""
    off = start
    records = 0
    total = len(tail)
    while off < total and records < CONT_MAX_RECORDS:
        v, n = load_unsigned(tail, off)
        if v is None:
            break
        off += n
        need = 0 if v == 0 else v - 1
        if off + need > total:
            break
        off += need
        records += 1
    return records


class FamilyAcc:
    def __init__(self):
        self.blocks = 0
        self.term_eq_vm1 = 0
        self.term_eq_v = 0
        self.term_lt = 0
        self.term_gt = 0
        self.term_none = 0
        self.byte_at = {"L1": collections.Counter(), "L2": collections.Counter()}
        self.varint_ok = {"L1": 0, "L2": 0}
        self.cont = {"L1": [], "L2": [], "T0": [], "T1": []}

    def add(self, tail, n, v):
        self.blocks += 1
        payload_start = n
        t = terminator_offset(tail, payload_start, v)
        if t is None:
            self.term_none += 1
        elif t == v - 1:
            self.term_eq_vm1 += 1
        elif t == v:
            self.term_eq_v += 1
        elif t < v - 1:
            self.term_lt += 1
        else:
            self.term_gt += 1
        for name, pos in (("L1", n + v - 1), ("L2", n + v)):
            if pos < len(tail):
                self.byte_at[name][byte_class(tail[pos])] += 1
                m, _ = load_unsigned(tail, pos)
                if m is not None:
                    self.varint_ok[name] += 1
            self.cont[name].append(min(continuation(tail, pos),
                                       CONT_MAX_RECORDS))
        if t is not None:
            for name, pos in (("T0", n + t), ("T1", n + t + 1)):
                self.cont[name].append(min(continuation(tail, pos),
                                           CONT_MAX_RECORDS))
        else:
            for name in ("T0", "T1"):
                self.cont[name].append(0)


def summarize(accs):
    out = {}
    for fam, acc in accs.items():
        n = max(1, acc.blocks)
        row = {"blocks": acc.blocks,
               "term_eq_vm1": acc.term_eq_vm1 / n,
               "term_eq_v": acc.term_eq_v / n,
               "term_lt": acc.term_lt / n,
               "term_gt": acc.term_gt / n,
               "term_none": acc.term_none / n,
               "byte_at": {}, "varint_ok": {}, "cont": {}}
        for name in ("L1", "L2"):
            row["byte_at"][name] = dict(acc.byte_at[name])
            row["varint_ok"][name] = acc.varint_ok[name] / n
        for name in ("L1", "L2", "T0", "T1"):
            conts = sorted(acc.cont[name])
            row["cont"][name] = {
                "median": conts[len(conts) // 2] if conts else 0,
                "ge3_frac": (sum(1 for c in conts if c >= CONT_OK)
                             / max(1, len(conts))),
            }
        out[fam] = row
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    for fam, r in s.items():
        print(f"# [{fam}] blocks={r['blocks']}")
        print(f"#   B1 terminator: t==v-1 {r['term_eq_vm1']:.3f} "
              f"t==v {r['term_eq_v']:.3f} t<v-1 {r['term_lt']:.3f} "
              f"t>v {r['term_gt']:.3f} none {r['term_none']:.3f}")
        for pos in ("L1", "L2"):
            print(f"#   B2 {pos}: bytes={r['byte_at'][pos]} "
                  f"varint_ok={r['varint_ok'][pos]:.3f} | "
                  f"B3 cont median={r['cont'][pos]['median']} "
                  f"ge{CONT_OK}_frac={r['cont'][pos]['ge3_frac']:.3f}")
        for pos in ("T0", "T1"):
            print(f"#   B4 {pos}: cont median={r['cont'][pos]['median']} "
                  f"ge{CONT_OK}_frac={r['cont'][pos]['ge3_frac']:.3f}")


def gate(s):
    for r in s.values():
        for pos in ("L1", "L2", "T0", "T1"):
            if r["cont"][pos]["ge3_frac"] >= GATE_CONT_FRAC:
                return "RECORD_BOUNDARY_CANDIDATE"
    return "RECORD_BOUNDARY_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    accs = {"bare": FamilyAcc(), "plus512": FamilyAcc()}
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = parsed = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        tail = blk[framing["code_end"]:]
        if not tail:
            continue
        seen += 1
        v, n = load_unsigned(tail, 0)
        if v is None or v > HEAD_TAG_MAX:
            continue
        parsed += 1
        fam = "plus512" if v >= 512 else "bare"
        accs[fam].add(tail, n, v)
    s = summarize(accs)
    print(f"# archive entries={total} luat_blocks_used={seen} "
          f"head_varint_parsed={parsed}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # v = 5: payload "abcd" + terminator 0x04 -> t == v-1 == 4 at L1.
    tail = bytes([0x85]) + b"abcd" + bytes([0x04]) + bytes([0x82]) + b"z"
    assert terminator_offset(tail, 1, 5) == 4
    acc = FamilyAcc()
    acc.add(tail, 1, 5)
    s = summarize({"bare": acc})["bare"]
    assert abs(s["term_eq_vm1"] - 1.0) < 1e-9, s
    assert s["byte_at"]["L1"]["control"] == 1, s["byte_at"]
    # Continuation from L2 (the 0x04 is a continuation byte of a varint):
    # 04 82 = value 514 -> payload too long -> 0 records; from L1 the byte
    # is 0x04 alone (continuation, needs a terminal after) -> varint 514?
    # Actually load_unsigned(tail, L1) reads 0x04 0x82 = 514, need 513 ->
    # truncated -> 0 records. Craft a walking continuation instead:
    tail2 = bytes([0x82]) + b"x" + bytes([0x81]) + bytes([0x83]) + b"ab"
    # v = 2, payload "x"; L1 = 1 + 1 = 2 -> [0x81][0x83 'a' 'b']: record
    # v=1 empty, then v=3 payload "ab" -> 2 records.
    assert continuation(tail2, 2) == 2, continuation(tail2, 2)
    acc2 = FamilyAcc()
    acc2.add(tail2, 1, 2)
    s2 = summarize({"bare": acc2})["bare"]
    assert s2["cont"]["L1"]["median"] == 2, s2["cont"]
    # Terminator absent within window.
    tail3 = bytes([0x82]) + b"xy" + b"z" * 32
    assert terminator_offset(tail3, 1, 2) is None
    # B4: internal control byte (t < v-1) restarts.
    # v=5, payload bytes = 'a' 0x00 0x81 0x82; t=1. From T0=2: varint
    # [0x00 0x81] = 1 (empty payload) then [0x82] 'q' -> 2 records; from
    # T1=3: [0x81] then [0x82] 'q' -> 2 records.
    tail4 = bytes([0x85]) + b"a" + bytes([0x00, 0x81, 0x82]) + b"q"
    assert terminator_offset(tail4, 1, 5) == 1
    assert continuation(tail4, 2) == 2, continuation(tail4, 2)
    assert continuation(tail4, 3) == 2, continuation(tail4, 3)
    acc4 = FamilyAcc()
    acc4.add(tail4, 1, 5)
    s4 = summarize({"bare": acc4})["bare"]
    assert abs(s4["term_lt"] - 1.0) < 1e-9, s4
    assert s4["cont"]["T0"]["median"] == 2 and s4["cont"]["T1"]["median"] == 2, s4["cont"]
    # Gate logic.
    assert gate({"bare": {"cont": {"L1": {"ge3_frac": 0.2}, "L2": {"ge3_frac": 0.1},
                                   "T0": {"ge3_frac": 0.1}, "T1": {"ge3_frac": 0.1}}}}) == \
        "RECORD_BOUNDARY_PARTIAL"
    assert gate({"bare": {"cont": {"L1": {"ge3_frac": 0.4}, "L2": {"ge3_frac": 0.1},
                                   "T0": {"ge3_frac": 0.1}, "T1": {"ge3_frac": 0.1}}}}) == \
        "RECORD_BOUNDARY_CANDIDATE"
    # Full synthetic block through locate_body.
    src = b"@s"
    block = bytearray(0x20)
    block.append(len(src) + 1 | 0x80)
    block.extend(src)
    block.extend(bytes([0x80, 0x80, 0x00, 0x01, 0x05]))
    block.append(0x80 | 2)                     # sizecode = 2
    block.extend(bytes([0x60, 0, 0, 0, 0x0C, 0, 0, 0]))
    block.extend(tail2)
    blk = bytes(block)
    framing = locate_body(blk)
    assert blk[framing["code_end"]:] == tail2
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AA boundary probe")
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
        print(f"# record boundary probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
