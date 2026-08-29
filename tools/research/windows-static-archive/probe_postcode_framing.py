#!/usr/bin/env python3
"""
probe_postcode_framing.py — H-NEX-003W: post-code section framing classifier.

H-NEX-003V showed the region after code_end is non-official: ~97% of blocks
carry >256 trailing bytes, the official sizek varint decodes in only ~30%,
and the first bytes look string-like. This read-only probe classifies that
framing without decoding game content:

  W1 printable-run structure : offset of the first printable ASCII run
      (length >= 4) from code_end, printable byte fraction of the first
      TAIL_SCAN bytes, and run count. A stable first-run offset implies a
      fixed-width header before the first string content.
  W2 leading-byte position histograms : per-position byte value counters for
      the first 16 trailing bytes, to detect fixed header bytes.
  W3 string framing hypotheses at candidate starts (offsets 0..16):
      H-official : official loadString varint (size s; s==0 empty, else s-1
                   printable bytes);
      H-u8       : one-byte length n followed by n printable bytes;
      H-u8s      : one-byte length n, n-1 printable bytes (Lua-style size);
      H-u16      : little-endian two-byte length followed by printable bytes.
  W4 small-integer scan : count of u32-LE values below 1000 in the first 64
      trailing bytes (count-field candidates).
  W5 run texture : longest-run terminator byte histogram and run character
      mix (space vs underscore/dot fractions) — identifier-style vs
      sentence-style text discrimination.

Guardrails: read-only, bounded scan window, fail-closed per block,
deterministic ordering, selftest on a synthetic block. No content export,
no decryption, no opcode claims.

Usage:
    python probe_postcode_framing.py --selftest
    python probe_postcode_framing.py <mpkinfo> <mpk> [--limit N]
"""
import argparse
import collections
import struct
import sys

from probe_instruction_layout import locate_body
from probe_semantic_fields import enumerate_luat_blocks
from verify_proto_boundary import LUA_SIG, MpkinfoReader, load_unsigned

TAIL_SCAN = 256
RUN_MIN = 4
CANDIDATE_STARTS = range(0, 17)
HEADER_HISTOGRAM_WIDTH = 16


def is_printable(b):
    return 32 <= b < 127


def printable_runs(tail):
    """Yield (start, length) of maximal printable runs in tail."""
    start = None
    for i, b in enumerate(tail):
        if is_printable(b):
            if start is None:
                start = i
        elif start is not None:
            yield start, i - start
            start = None
    if start is not None:
        yield start, len(tail) - start


def try_official_string(tail, off):
    """Official loadString shape at off: varint size; s==0 or s-1 printable."""
    s, n = load_unsigned(tail, off)
    if s is None:
        return False, 0
    if s == 0:
        return True, n
    need = s - 1
    if off + n + need > len(tail) or need > TAIL_SCAN:
        return False, 0
    body = tail[off + n:off + n + need]
    if need >= 1 and all(is_printable(b) for b in body):
        return True, n + need
    return False, 0


def try_fixed_len(tail, off, width, lua_style=False):
    """Fixed-width LE length prefix followed by printable bytes."""
    if off + width > len(tail):
        return False, 0
    length = int.from_bytes(tail[off:off + width], "little")
    if lua_style:
        if length == 0:
            return False, 0
        length -= 1
    if length == 0 or length > TAIL_SCAN:
        return False, 0
    if off + width + length > len(tail):
        return False, 0
    body = tail[off + width:off + width + length]
    if all(is_printable(b) for b in body):
        return True, width + length
    return False, 0


class Accumulator:
    def __init__(self):
        self.blocks = 0
        self.no_tail = 0
        self.first_run_offset = collections.Counter()
        self.first_run_len = []
        self.printable_fraction_sum = 0.0
        self.run_count = collections.Counter()
        self.header_bytes = [collections.Counter()
                             for _ in range(HEADER_HISTOGRAM_WIDTH)]
        self.hyp_hits = {name: collections.Counter()
                         for name in ("official", "u8", "u8s", "u16")}
        self.small_u32_count = []
        self.run_terminator = collections.Counter()
        self.run_space_bytes = 0
        self.run_ident_bytes = 0
        self.run_total_bytes = 0

    def add_block(self, blk, framing):
        code_end = framing["code_end"]
        tail = blk[code_end:code_end + TAIL_SCAN]
        if not tail:
            self.no_tail += 1
            return
        self.blocks += 1
        runs = list(printable_runs(tail))
        self.run_count[min(len(runs), 12)] += 1
        first = next(((s, l) for s, l in runs if l >= RUN_MIN), None)
        if first is not None:
            self.first_run_offset[min(first[0], 64)] += 1
            self.first_run_len.append(min(first[1], TAIL_SCAN))
        if runs:
            longest_start, longest_len = max(runs, key=lambda r: r[1])
            end = longest_start + longest_len
            self.run_terminator[tail[end] if end < len(tail) else 0x100] += 1
            for s, l in runs:
                body = tail[s:s + l]
                self.run_total_bytes += l
                self.run_space_bytes += sum(1 for b in body if b == 0x20)
                self.run_ident_bytes += sum(1 for b in body if b in (0x5F, 0x2E))
        self.printable_fraction_sum += sum(1 for b in tail if is_printable(b)) / len(tail)
        for i in range(min(HEADER_HISTOGRAM_WIDTH, len(tail))):
            self.header_bytes[i][tail[i]] += 1
        for start in CANDIDATE_STARTS:
            if start >= len(tail):
                break
            ok, _ = try_official_string(tail, start)
            if ok:
                self.hyp_hits["official"][start] += 1
            ok, _ = try_fixed_len(tail, start, 1)
            if ok:
                self.hyp_hits["u8"][start] += 1
            ok, _ = try_fixed_len(tail, start, 1, lua_style=True)
            if ok:
                self.hyp_hits["u8s"][start] += 1
            ok, _ = try_fixed_len(tail, start, 2)
            if ok:
                self.hyp_hits["u16"][start] += 1
        small = 0
        for i in range(0, min(61, len(tail) - 3)):
            v = struct.unpack_from("<I", tail, i)[0]
            if 0 < v < 1000:
                small += 1
        self.small_u32_count.append(small)


def summarize(acc):
    n = max(1, acc.blocks)
    out = {"blocks": acc.blocks, "no_tail": acc.no_tail}
    out["printable_fraction"] = acc.printable_fraction_sum / n
    out["first_run_offset_top"] = acc.first_run_offset.most_common(8)
    lens = sorted(acc.first_run_len)
    out["first_run_len_median"] = lens[len(lens) // 2] if lens else 0
    out["run_count_hist"] = dict(sorted(acc.run_count.items()))
    header_summary = []
    for i, counter in enumerate(acc.header_bytes):
        top = counter.most_common(3)
        concentration = top[0][1] / n if top else 0.0
        header_summary.append((i, [(hex(b), c) for b, c in top],
                               round(concentration, 3)))
    out["header_bytes"] = header_summary
    out["hyp_hits"] = {
        name: counter.most_common(5) for name, counter in acc.hyp_hits.items()
    }
    smalls = sorted(acc.small_u32_count)
    out["small_u32_median"] = smalls[len(smalls) // 2] if smalls else 0
    out["run_terminator_top"] = [
        ("EOF" if b == 0x100 else hex(b), c)
        for b, c in acc.run_terminator.most_common(8)
    ]
    total = max(1, acc.run_total_bytes)
    out["run_space_fraction"] = acc.run_space_bytes / total
    out["run_ident_fraction"] = acc.run_ident_bytes / total
    return out


def print_summary(name, s):
    print(f"# === {name} ===")
    print(f"# blocks_with_tail={s['blocks']} no_tail={s['no_tail']} "
          f"printable_fraction(first {TAIL_SCAN}B)={s['printable_fraction']:.3f}")
    print(f"# W1 first printable run (len>={RUN_MIN}) offset top: "
          f"{s['first_run_offset_top']}")
    print(f"#    run length median={s['first_run_len_median']} "
          f"run_count_hist={s['run_count_hist']}")
    print("# W2 leading-byte position concentration (pos, top3, share):")
    for pos, top, share in s["header_bytes"]:
        flag = " <-- concentrated" if share >= 0.5 else ""
        print(f"#    +{pos:02d}: {top} share={share:.3f}{flag}")
    print("# W3 string-framing hypothesis hits by start offset:")
    for hyp in ("official", "u8", "u8s", "u16"):
        print(f"#    {hyp}: {s['hyp_hits'][hyp]}")
    print(f"# W4 small u32-LE (<1000) count in first 64B: median={s['small_u32_median']}")
    print(f"# W5 longest-run terminator top: {s['run_terminator_top']}")
    print(f"#    run char mix: space_fraction={s['run_space_fraction']:.3f} "
          f"underscore+dot_fraction={s['run_ident_fraction']:.3f}")


def gate(s):
    concentrated = [pos for pos, _, share in s["header_bytes"] if share >= 0.5]
    stable_first_run = any(c / max(1, s["blocks"]) >= 0.5
                           for _, c in s["first_run_offset_top"][:1])
    if concentrated or stable_first_run:
        return "POSTCODE_FRAMING_CLASSIFIED"
    return "POSTCODE_FRAMING_PARTIAL"


def probe(mpkinfo_path, mpk_path, limit=None):
    acc = Accumulator()
    reader = MpkinfoReader(mpkinfo_path)
    total = reader.count
    seen = 0
    for index, blk, framing in enumerate_luat_blocks(mpkinfo_path, mpk_path, limit):
        acc.add_block(blk, framing)
        seen += 1
    s = summarize(acc)
    print(f"# archive entries={total} luat_blocks_used={seen}"
          + (f" (limit={limit})" if limit is not None else ""))
    print_summary(mpkinfo_path, s)
    g = gate(s)
    print(f"RESULT: {g}")
    return 0


def selftest():
    # Synthetic block: 6-instruction code region followed by a 3-byte fixed
    # header and a printable run starting at offset 3.
    src = b"@s"
    block = bytearray(0x20)
    block.append(len(src) + 1 | 0x80)
    block.extend(src)
    block.extend(bytes([0x80, 0x80, 0x00, 0x01, 0x05]))
    block.append(0x80 | 2)                     # sizecode = 2
    block.extend(bytes([0x60, 0, 0, 0, 0x0C, 0, 0, 0]))
    block.extend(bytes([0x04, 0x88, 0x00]))    # fixed 3-byte header
    block.extend(b"hello.world")
    blk = bytes(block)
    framing = locate_body(blk)
    acc = Accumulator()
    acc.add_block(blk, framing)
    s = summarize(acc)
    assert s["blocks"] == 1, s
    assert s["first_run_offset_top"][0][0] == 3, s["first_run_offset_top"]
    header = {pos: share for pos, _, share in s["header_bytes"]}
    assert header[0] == 1.0 and header[1] == 1.0 and header[2] == 1.0, s["header_bytes"]
    assert gate(s) == "POSTCODE_FRAMING_CLASSIFIED", gate(s)
    # official loadString hypothesis on crafted tails
    tail = blk[framing["code_end"]:]
    ok, consumed = try_official_string(bytes([0x80]) + b"x", 0)
    assert ok and consumed == 1, (ok, consumed)          # varint 0 = empty string
    ok, consumed = try_official_string(bytes([0x83]) + b"ab.", 0)
    assert ok and consumed == 3, (ok, consumed)          # size 3 -> 2 printable bytes
    ok, _ = try_official_string(bytes([0x83]) + b"a\xff.", 0)
    assert not ok, "non-printable body must reject"
    ok, consumed = try_fixed_len(tail, 3, 1)
    assert not ok, "length 0x68='h' should overrun printable window check"
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003W post-code framing probe")
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
        print(f"# post-code framing probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
