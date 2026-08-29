#!/usr/bin/env python3
"""
probe_semantic_fields.py — H-NEX-003V: semantic field validation for the
bytewise [opcode:1][A:1][B:1][C:1] 4-byte record layout candidate.

The layout candidate (H-NEX-003U) says records are 4 bytes wide with the
opcode in byte 0. It does NOT say what the operands mean. This read-only
probe validates candidate semantics without assigning opcode meanings:

  T1 register-bound : fraction of records whose operand byte (positions
                      A/B/C; B and C also with the MSB masked) is below the
                      proto's maxstacksize. A strong position asymmetry is
                      evidence the positions are not interchangeable.
  T2 high-bit flags : fraction of B/C values with the MSB set (flagged
                      constant-index candidate, mirroring Lua 5.4 VRB/VRC).
  T3 bigram coupling: conditional successor distribution per opcode byte.
                      A pair (p -> n) with P(n|p) ~= 1 and n rare elsewhere
                      is an EXTRAARG-like relation candidate.
  T4 jump plausibility: per opcode byte, interpret C as signed byte, B as
                      unsigned byte, and B|C<<8 as signed 16-bit relative
                      offsets; compare in-range rate with the analytical
                      uniform baseline. Persistent excess marks JMP-like
                      candidates. No semantics assumed for other opcodes.
  T5 post-code framing: classify the bytes at code_end across blocks
                      (remainder buckets, first-byte histogram, official
                      varint decodability, bounded 0x80 0x80 marker scan).

Guardrails: read-only, bounded reads, fail-closed per block (rejected blocks
are counted, never guessed), deterministic output ordering, selftest on a
synthetic block. No decryption, no runtime state, no opcode table claims.

Usage:
    python probe_semantic_fields.py --selftest
    python probe_semantic_fields.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from verify_proto_boundary import LUA_SIG, MpkinfoReader, load_unsigned

JUMP_MIN_COUNT = 20
BIGRAM_MIN_COUNT = 5
BIGRAM_MIN_PROB = 0.9
MARKER_WINDOW = 64


def enumerate_luat_blocks(mpkinfo_path, mpk_path, limit=None):
    """Yield (index, block, framing) for every bounded LuaT block."""
    reader = MpkinfoReader(mpkinfo_path)
    with open(reader._path, "rb") as f:
        raw = f.read()
    entries = []
    for i in range(reader.count):
        f0, f1, off, size, flags = struct.unpack_from("<IIIII", raw, 8 + i * 20)
        entries.append({"index": i, "offset": off, "stored_size": size,
                        "flags": flags})
    archive_size = _file_size(mpk_path)
    used = 0
    with open(mpk_path, "rb") as f:
        for e in entries:
            if limit is not None and used >= limit:
                break
            if e["stored_size"] == 0:
                continue
            if e["offset"] + e["stored_size"] > archive_size:
                continue
            f.seek(e["offset"])
            blk = f.read(e["stored_size"])
            sig = blk.find(LUA_SIG)
            if sig < 0 or blk[sig + 4:sig + 6] != b"\x54\x00":
                continue
            try:
                framing = locate_body(blk)
            except (ValueError, IndexError, struct.error):
                continue
            used += 1
            yield e["index"], blk, framing


def _file_size(path):
    import os
    return os.path.getsize(path)


def records_of(blk, framing):
    start, end = framing["code_start"], framing["code_end"]
    return [blk[p:p + 4] for p in range(start, end, 4)]


def jump_inrange_windows(i, n):
    """Closed-form counts of offsets landing in [0, n) for each interpretation."""
    lo_sc = max(-128, -(i + 1))
    hi_sc = min(127, n - 2 - i)
    sc_ok = max(0, hi_sc - lo_sc + 1)
    hi_ub = min(255, n - 2 - i)
    ub_ok = max(0, hi_ub + 1)
    lo, hi = -32768, 32767
    first = max(lo, -(i + 1))
    last = min(hi, n - 1 - (i + 1))
    s16_ok = max(0, last - first + 1)
    return sc_ok, ub_ok, s16_ok


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.records = 0
        # T1: [count_below_ms] per position interpretation
        self.t1_total = 0
        self.t1_a = 0
        self.t1_b = 0
        self.t1_c = 0
        self.t1_b_masked = 0
        self.t1_c_masked = 0
        # T2: MSB flags
        self.t2_a_hi = 0
        self.t2_b_hi = 0
        self.t2_c_hi = 0
        # T3: bigrams
        self.bigram = collections.Counter()
        self.op_count = collections.Counter()
        # T4: per-opcode jump stats
        self.jump = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self.jump_sign = collections.defaultdict(lambda: [0, 0, 0])
        # T5: post-code
        self.remainder_buckets = collections.Counter()
        self.post_first_byte = collections.Counter()
        self.post_varint_ok = 0
        self.post_marker_found = 0
        self.post_blocks = 0

    def add_block(self, blk, framing):
        recs = records_of(blk, framing)
        n = len(recs)
        ms = framing["maxstacksize"]
        self.blocks += 1
        self.records += n
        self.t1_total += n
        prev_op = None
        for i, rec in enumerate(recs):
            op, a, b, c = rec[0], rec[1], rec[2], rec[3]
            self.op_count[op] += 1
            if a < ms:
                self.t1_a += 1
            if b < ms:
                self.t1_b += 1
            if c < ms:
                self.t1_c += 1
            if (b & 0x7F) < ms:
                self.t1_b_masked += 1
            if (c & 0x7F) < ms:
                self.t1_c_masked += 1
            self.t2_a_hi += a >= 0x80
            self.t2_b_hi += b >= 0x80
            self.t2_c_hi += c >= 0x80
            if prev_op is not None:
                self.bigram[(prev_op, op)] += 1
            prev_op = op
            sc_w, ub_w, s16_w = jump_inrange_windows(i, n)
            j = self.jump[op]
            j[0] += 1
            target_sc = i + 1 + (c if c < 128 else c - 256)
            j[1] += 0 <= target_sc < n
            target_ub = i + 1 + b
            j[2] += 0 <= target_ub < n
            s16 = b | (c << 8)
            if s16 >= 32768:
                s16 -= 65536
            j[3] += 0 <= i + 1 + s16 < n
            j[4] += sc_w / 256
            j[5] += ub_w / 256
            j[6] += s16_w / 65536
            sign = self.jump_sign[op]
            if s16 < 0:
                sign[0] += 1
            elif s16 == 0:
                sign[1] += 1
            else:
                sign[2] += 1
        self.add_post_code(blk, framing)

    def add_post_code(self, blk, framing):
        code_end = framing["code_end"]
        remainder = len(blk) - code_end
        self.post_blocks += 1
        if remainder == 0:
            self.remainder_buckets["0"] += 1
        elif remainder <= 8:
            self.remainder_buckets["1-8"] += 1
        elif remainder <= 32:
            self.remainder_buckets["9-32"] += 1
        elif remainder <= 256:
            self.remainder_buckets["33-256"] += 1
        else:
            self.remainder_buckets[">256"] += 1
        if remainder > 0:
            self.post_first_byte[blk[code_end]] += 1
            val, _ = load_unsigned(blk, code_end)
            if val is not None and val <= 100000:
                self.post_varint_ok += 1
            if blk.find(b"\x80\x80", code_end, code_end + MARKER_WINDOW) >= 0:
                self.post_marker_found += 1


def fraction(num, den):
    return num / den if den else 0.0


def summarize(acc, jump_min_count=JUMP_MIN_COUNT,
              bigram_min_count=BIGRAM_MIN_COUNT,
              bigram_min_prob=BIGRAM_MIN_PROB):
    out = {
        "blocks": acc.blocks,
        "records": acc.records,
        "t1": {
            "A<ms": fraction(acc.t1_a, acc.t1_total),
            "B<ms": fraction(acc.t1_b, acc.t1_total),
            "C<ms": fraction(acc.t1_c, acc.t1_total),
            "(B&7F)<ms": fraction(acc.t1_b_masked, acc.t1_total),
            "(C&7F)<ms": fraction(acc.t1_c_masked, acc.t1_total),
        },
        "t2": {
            "A_hi": fraction(acc.t2_a_hi, acc.records),
            "B_hi": fraction(acc.t2_b_hi, acc.records),
            "C_hi": fraction(acc.t2_c_hi, acc.records),
        },
    }
    pairs = []
    for (p, nx), cnt in acc.bigram.items():
        total = acc.op_count[p]
        prob = cnt / total
        if cnt >= bigram_min_count and prob >= bigram_min_prob:
            nxt_anywhere = acc.op_count[nx]
            pairs.append((cnt, prob, p, nx, nxt_anywhere))
    pairs.sort(key=lambda t: (-t[0], t[2], t[3]))
    out["t3_coupled_pairs"] = pairs[:20]
    jumps = []
    for op, j in acc.jump.items():
        cnt = j[0]
        if cnt < jump_min_count:
            continue
        sc_rate, ub_rate, s16_rate = j[1] / cnt, j[2] / cnt, j[3] / cnt
        sc_base, ub_base, s16_base = j[4] / cnt, j[5] / cnt, j[6] / cnt
        neg, zero, pos = acc.jump_sign[op]
        jumps.append({
            "op": op, "count": cnt,
            "sC": (sc_rate, sc_base), "uB": (ub_rate, ub_base),
            "s16": (s16_rate, s16_base),
            "excess_s16": s16_rate - s16_base,
            "excess_sC": sc_rate - sc_base,
            "neg_frac": neg / cnt, "zero_frac": zero / cnt,
        })
    jumps.sort(key=lambda d: (-d["excess_s16"], d["op"]))
    out["t4_jump_candidates_s16"] = jumps[:12]
    jumps_sc = sorted(jumps, key=lambda d: (-d["excess_sC"], d["op"]))
    out["t4_jump_candidates_sC"] = jumps_sc[:12]
    out["t5"] = {
        "blocks": acc.post_blocks,
        "remainder_buckets": dict(acc.remainder_buckets),
        "first_byte_top": acc.post_first_byte.most_common(10),
        "varint_decodable": acc.post_varint_ok,
        "marker_within_window": acc.post_marker_found,
        "window": MARKER_WINDOW,
    }
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# blocks={s['blocks']} records={s['records']}")
    t1 = s["t1"]
    print(f"# T1 register-bound fraction (< maxstacksize): A={t1['A<ms']:.3f} "
          f"B={t1['B<ms']:.3f} C={t1['C<ms']:.3f} "
          f"B&7F={t1['(B&7F)<ms']:.3f} C&7F={t1['(C&7F)<ms']:.3f}")
    t2 = s["t2"]
    print(f"# T2 MSB-set fraction: A={t2['A_hi']:.3f} B={t2['B_hi']:.3f} C={t2['C_hi']:.3f}")
    print(f"# T3 coupled bigrams (count>={BIGRAM_MIN_COUNT}, P>={BIGRAM_MIN_PROB}):")
    for cnt, prob, p, nx, total_n in s["t3_coupled_pairs"]:
        print(f"#   op 0x{p:02X} -> 0x{nx:02X}: count={cnt} P={prob:.3f} "
              f"(0x{nx:02X} total occurrences={total_n})")
    print("# T4 jump candidates by s16(B|C<<8) excess (count"
          f">={JUMP_MIN_COUNT}):")
    for j in s["t4_jump_candidates_s16"]:
        r, b = j["s16"]
        print(f"#   op 0x{j['op']:02X} n={j['count']} s16_inrange={r:.3f} "
              f"baseline={b:.3f} excess={j['excess_s16']:+.3f} "
              f"neg={j['neg_frac']:.3f} zero={j['zero_frac']:.3f}")
    print("# T4 jump candidates by sC excess:")
    for j in s["t4_jump_candidates_sC"][:6]:
        r, b = j["sC"]
        print(f"#   op 0x{j['op']:02X} n={j['count']} sC_inrange={r:.3f} "
              f"baseline={b:.3f} excess={j['excess_sC']:+.3f}")
    t5 = s["t5"]
    print(f"# T5 post-code: blocks={t5['blocks']} remainder={t5['remainder_buckets']}")
    print(f"#   varint_decodable={t5['varint_decodable']} "
          f"marker(0x80 0x80) within +{t5['window']}B={t5['marker_within_window']}")
    print(f"#   first_byte_top={[(hex(b), c) for b, c in t5['first_byte_top']]}")


def gate(s):
    coupled = len(s["t3_coupled_pairs"]) > 0
    asym = abs(s["t1"]["A<ms"] - s["t1"]["B<ms"]) > 0.05 or \
        abs(s["t1"]["A<ms"] - s["t1"]["C<ms"]) > 0.05
    jump = any(j["excess_s16"] > 0.25 for j in s["t4_jump_candidates_s16"])
    if coupled or asym or jump:
        return "SEMANTIC_FIELD_VALIDATION_PARTIAL"
    return "SEMANTIC_FIELD_VALIDATION_NULL"


def probe(mpkinfo_path, mpk_path, limit=None):
    acc = Accumulator()
    rejected = 0
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        acc.add_block(blk, framing)
        seen += 1
    rejected = total - seen if limit is None else 0
    s = summarize(acc)
    print(f"# archive entries={total} luat_blocks_used={s['blocks']} "
          f"non_luat_or_rejected={rejected}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Synthetic LuaT block: source "@s" (len 2 -> varint 3), marker,
    # maxstacksize=5, sizecode=6, six bytewise records, post-code varint 0.
    src = b"@s"
    block = bytearray(0x20)
    block.append(len(src) + 1 | 0x80)          # varint 3, MSB-terminated
    block.extend(src)
    block.extend(bytes([0x80, 0x80, 0x00, 0x01, 0x05]))  # marker np iv ms
    block.append(0x80 | 6)                     # sizecode = 6
    recs = [
        bytes([0x44, 0x00, 0x00, 0x00]),       # sC jump: target 1
        bytes([0x44, 0x00, 0x00, 0x01]),       # sC jump: target 3
        bytes([0x77, 0x01, 0x80, 0x00]),       # B MSB set
        bytes([0xEE, 0x00, 0x00, 0x00]),       # always after 0x77
        bytes([0x77, 0x02, 0x80, 0x00]),
        bytes([0xEE, 0x00, 0x00, 0x00]),
    ]
    block.extend(b"".join(recs))
    block.append(0x80)                         # post-code varint = 0
    blk = bytes(block)
    framing = locate_body(blk)
    assert framing["sizecode"] == 6 and framing["maxstacksize"] == 5
    acc = Accumulator()
    acc.add_block(blk, framing)
    s = summarize(acc, jump_min_count=2, bigram_min_count=2)
    # T1: A values (0,0,1,0,2,0) all below ms=5
    assert s["t1"]["A<ms"] == 1.0, s["t1"]
    # T2: B MSB set in 2/6 records
    assert abs(s["t2"]["B_hi"] - 2 / 6) < 1e-9, s["t2"]
    # T3: coupled pair 0x77 -> 0xEE with P=1.0
    pairs = {(p, nx): (cnt, prob) for cnt, prob, p, nx, _ in s["t3_coupled_pairs"]}
    assert (0x77, 0xEE) in pairs and pairs[(0x77, 0xEE)] == (2, 1.0), s["t3_coupled_pairs"]
    # T4: op 0x44 has sC in-range rate 1.0 (targets 1 and 3 inside n=6)
    j44 = [j for j in s["t4_jump_candidates_sC"] if j["op"] == 0x44]
    assert j44 and j44[0]["sC"][0] == 1.0, s["t4_jump_candidates_sC"]
    # T5: post-code first byte 0x80, varint decodable, remainder bucket 1-8
    assert s["t5"]["first_byte_top"][0] == (0x80, 1), s["t5"]
    assert s["t5"]["varint_decodable"] == 1, s["t5"]
    assert s["t5"]["remainder_buckets"].get("1-8") == 1, s["t5"]
    assert gate(s) in ("SEMANTIC_FIELD_VALIDATION_PARTIAL",)
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003V semantic field probe")
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
        print(f"# semantic field probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
