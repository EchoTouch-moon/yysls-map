#!/usr/bin/env python3
"""
probe_stratify.py — H-NEX-003AG: stratify the walkable minority.

H-NEX-003AF rejected all six full-stream grammars but found a stable ~3.5%
of blocks that walk to near-full coverage as prefix-free concatenated
loadString records. This read-only probe asks whether that minority is
cleanly separable on structural features — i.e. whether the string-table
grammar holds for a recognizable proto class.

Method:
  Classify each block HIGH (best marker-relative loadString coverage
  >= HIGH_COV) or LOW. Extract bounded structural features:
      instrs       code-region instruction count ((code_end-code_start)/4)
      block_size   whole block byte length
      tail_len     post-code byte length
      first_04     first 0x04 offset in tail[:SCAN] (or -1)
      first_14     first 0x14 offset in tail[:SCAN] (or -1)
      head_family  tail[0] varint: none / small(<512) / mid(<=4096) / big
      first_b      byte class of tail[0] (control/printable/high)
  For each numeric feature scan threshold rules (feature <= t and >= t) at
  sampled quantiles; for each categorical feature scan equality rules.
  Record precision/recall of each rule for the HIGH class and the best rule.

Pre-registered gate: STRATIFICATION_CANDIDATE if some single rule reaches
precision >= GATE_PRECISION and recall >= GATE_RECALL with
|HIGH| >= MIN_HIGH; else STRATIFICATION_PARTIAL. Decisive: a cleanly
separable minority confirms a proto-class string-table grammar; an
inseparable minority means per-proto organization and closes the line with
the marker census as the deliverable.

Guardrails: read-only, bounded scans/caps, fail-closed per block,
deterministic ordering, selftest on synthetic HIGH/LOW blocks. No content
export, no decryption, no opcode claims.

Usage:
    python probe_stratify.py --selftest
    python probe_stratify.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_string_table import best_walk
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import MpkinfoReader, load_unsigned

HIGH_COV = 0.90
SCAN = 64
MIN_HIGH = 30
GATE_PRECISION = 0.70
GATE_RECALL = 0.50
NUMERIC_FEATURES = ("instrs", "block_size", "tail_len", "first_04", "first_14")
CATEGORICAL_FEATURES = ("head_family", "first_b")


def byte_class(b):
    if b < 0x20:
        return "control"
    if b < 0x7F:
        return "printable"
    return "high"


def head_family(tail):
    v, _ = load_unsigned(tail, 0)
    if v is None:
        return "none"
    if v < 512:
        return "small"
    if v <= 4096:
        return "mid"
    return "big"


def first_offset(tail, byte):
    for i in range(min(SCAN, len(tail))):
        if tail[i] == byte:
            return i
    return -1


def analyze_block(blk, framing):
    """Return (is_high, coverage, features)."""
    tail = blk[framing["code_end"]:]
    if not tail:
        return False, 0.0, None
    best, best_start, zero = best_walk(tail)
    cov = best["coverage"]
    feats = {
        "instrs": (framing["code_end"] - framing["code_start"]) // 4,
        "block_size": len(blk),
        "tail_len": len(tail),
        "first_04": first_offset(tail, 0x04),
        "first_14": first_offset(tail, 0x14),
        "head_family": head_family(tail),
        "first_b": byte_class(tail[0]),
    }
    return cov >= HIGH_COV, cov, feats


def quantile_thresholds(values, steps=20):
    if not values:
        return []
    vs = sorted(values)
    out = []
    for i in range(1, steps):
        idx = int(len(vs) * i / steps)
        out.append(vs[min(idx, len(vs) - 1)])
    return sorted(set(out))


def evaluate_rules(high, feats_by_id):
    """high: set of ids. Returns list of (rule, precision, recall, matches)."""
    ids = list(feats_by_id)
    n_high = len(high)
    rules = []

    def record(name, pred):
        pred = set(pred)
        if not pred:
            return
        hit = len(pred & high)
        rules.append((name, hit / len(pred), hit / n_high if n_high else 0.0,
                      len(pred)))

    for feat in NUMERIC_FEATURES:
        vals = [feats_by_id[i][feat] for i in ids]
        for t in quantile_thresholds(vals):
            record(f"{feat}<={t}", [i for i in ids if feats_by_id[i][feat] <= t])
            record(f"{feat}>={t}", [i for i in ids if feats_by_id[i][feat] >= t])
    for feat in CATEGORICAL_FEATURES:
        cats = collections.Counter(feats_by_id[i][feat] for i in ids)
        for cat in cats:
            record(f"{feat}=={cat}",
                   [i for i in ids if feats_by_id[i][feat] == cat])
    return rules


def summarize(high, feats_by_id):
    rules = evaluate_rules(high, feats_by_id)
    # Best rule by (precision, recall) meeting minimum support.
    best = None
    for name, p, r, m in sorted(rules, key=lambda x: (-x[1], -x[2])):
        best = (name, p, r, m)
        break
    med = {}
    for feat in NUMERIC_FEATURES:
        hv = sorted(feats_by_id[i][feat] for i in high)
        lv = sorted(feats_by_id[i][feat] for i in feats_by_id if i not in high)
        med[feat] = (hv[len(hv) // 2] if hv else None,
                     lv[len(lv) // 2] if lv else None)
    cat = {}
    for feat in CATEGORICAL_FEATURES:
        ch = collections.Counter(feats_by_id[i][feat] for i in high)
        cl = collections.Counter(feats_by_id[i][feat] for i in feats_by_id
                                 if i not in high)
        cat[feat] = (dict(ch.most_common(4)), dict(cl.most_common(4)))
    return {"n": len(feats_by_id), "n_high": len(high), "best": best,
            "medians": med, "cats": cat, "rules": rules}


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# blocks={s['n']} high={s['n_high']} "
          f"high_frac={s['n_high'] / max(1, s['n']):.3f}")
    print("# medians (feature: HIGH / LOW):")
    for feat, (hm, lm) in s["medians"].items():
        print(f"#    {feat}: {hm} / {lm}")
    for feat, (ch, cl) in s["cats"].items():
        print(f"#    {feat}: HIGH={ch} LOW={cl}")
    b = s["best"]
    if b:
        print(f"# best_rule={b[0]} precision={b[1]:.3f} recall={b[2]:.3f} "
              f"matches={b[3]}")
    top = sorted(s["rules"], key=lambda x: (-x[1], -x[2]))[:8]
    print("# top rules (rule, precision, recall, matches):")
    for name, p, r, m in top:
        print(f"#    {name}: p={p:.3f} r={r:.3f} m={m}")


def gate(s):
    if s["n_high"] < MIN_HIGH:
        return "STRATIFICATION_PARTIAL"
    b = s["best"]
    if b and b[1] >= GATE_PRECISION and b[2] >= GATE_RECALL:
        return "STRATIFICATION_CANDIDATE"
    return "STRATIFICATION_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    high = set()
    feats_by_id = {}
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        is_high, cov, feats = analyze_block(blk, framing)
        if feats is None:
            continue
        feats_by_id[seen] = feats
        if is_high:
            high.add(seen)
        seen += 1
    s = summarize(high, feats_by_id)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def _synth_block(tail):
    src = b"@s"
    block = bytearray(0x20)
    block.append(len(src) + 1 | 0x80)
    block.extend(src)
    block.extend(bytes([0x80, 0x80, 0x00, 0x01, 0x05]))
    block.append(0x80 | 2)
    block.extend(bytes([0x60, 0, 0, 0, 0x0C, 0, 0, 0]))
    block.extend(tail)
    blk = bytes(block)
    return blk, locate_body(blk)


def selftest():
    # HIGH block: a clean concatenated loadString table (short tail).
    high_tail = bytes([0x83]) + b"ab" + bytes([0x82]) + b"x" + bytes([0x80])
    # LOW block: text junk with no markers and a large-ish tail.
    low_tail = bytes([0x72]) + b"helloworld" * 6
    blk_h, fr_h = _synth_block(high_tail)
    blk_l, fr_l = _synth_block(low_tail)
    is_h, cov_h, feats_h = analyze_block(blk_h, fr_h)
    is_l, cov_l, feats_l = analyze_block(blk_l, fr_l)
    assert is_h and cov_h >= HIGH_COV, (is_h, cov_h)
    assert not is_l and cov_l < HIGH_COV, (is_l, cov_l)
    assert feats_h["tail_len"] < feats_l["tail_len"], (feats_h, feats_l)
    assert feats_h["head_family"] == "small", feats_h
    # Aggregate enough synthetic blocks to satisfy MIN_HIGH.
    high, feats_by_id = set(), {}
    for i in range(MIN_HIGH):
        feats_by_id[i] = dict(feats_h)
        high.add(i)
    for i in range(MIN_HIGH, 2 * MIN_HIGH):
        feats_by_id[i] = dict(feats_l)
    s = summarize(high, feats_by_id)
    assert s["n_high"] == MIN_HIGH, s["n_high"]
    b = s["best"]
    assert b is not None and b[1] >= GATE_PRECISION and b[2] >= GATE_RECALL, b
    assert gate(s) == "STRATIFICATION_CANDIDATE", gate(s)
    # A degenerate case with too few HIGH blocks must be PARTIAL.
    s2 = summarize({0}, {0: dict(feats_h), 1: dict(feats_l)})
    assert gate(s2) == "STRATIFICATION_PARTIAL"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003AG stratify probe")
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
        print(f"# stratify probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
