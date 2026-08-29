#!/usr/bin/env python3
"""
probe_instruction_layout.py — H-NEX-003U: bytewise instruction-layout probe.

The LuaT envelope advertises a 4-byte Instruction width, but the bytes do not
behave like the standard Lua 5.4 bit-packed instruction (opcode in bits 0..6).
This read-only probe compares that compatibility interpretation with the
stable field layout observed in the frozen samples:

    [opcode:1][A:1][B:1][C:1]

The probe deliberately does not assign opcode meanings or decompile the VM.
It records reproducible structure only: marker/body boundary, sizecode,
first records, standard packed invalid count, full-byte opcode range and
operand byte statistics.  The resulting gate is a layout candidate, not a
confirmed VM opcode table.

Usage:
    python probe_instruction_layout.py --selftest
    python probe_instruction_layout.py <mpkinfo> <mpk> <entry_index>
"""
import argparse
import collections
import os
import struct
import sys

from verify_proto_boundary import LUA_SIG, MpkinfoReader, load_unsigned, read_block


def _source_len(blk):
    length, n = load_unsigned(blk, 0x20)
    if length is None or length < 2:
        raise ValueError("source length varint invalid at 0x20")
    source_len = length - 1
    end = 0x21 + source_len
    if end > len(blk):
        raise ValueError("source exceeds block")
    return source_len, end


def locate_body(blk):
    source_len, logical_body = _source_len(blk)
    marker = blk.find(b"\x80\x80", 0x21)
    if marker < 0 or marker + 5 >= len(blk):
        raise ValueError("proto marker 0x80 0x80 not found")
    np_, is_vararg, maxstack = blk[marker + 2:marker + 5]
    if is_vararg not in (0, 1) or not (2 <= maxstack <= 255):
        raise ValueError("proto marker fields are not plausible")
    sizecode, n = load_unsigned(blk, marker + 5)
    if sizecode is None or sizecode <= 0 or sizecode > 500000:
        raise ValueError("sizecode varint invalid")
    code_start = marker + 5 + n
    code_end = code_start + sizecode * 4
    if code_end > len(blk):
        raise ValueError("code region exceeds block")
    return {
        "source_len": source_len,
        "logical_body": logical_body,
        "marker": marker,
        "source_serialization": "EXACT" if marker == logical_body else "PARTIAL",
        "numparams": np_,
        "is_vararg": is_vararg,
        "maxstacksize": maxstack,
        "sizecode": sizecode,
        "code_start": code_start,
        "code_end": code_end,
    }


def inspect_records(blk, framing, sample_records=12):
    start, end = framing["code_start"], framing["code_end"]
    records = [blk[p:p + 4] for p in range(start, end, 4)]
    words = [struct.unpack("<I", rec)[0] for rec in records]
    packed_ops = [word & 0x7F for word in words]
    packed_invalid = sum(op >= 83 for op in packed_ops)
    byte_ops = [rec[0] for rec in records]
    counter = collections.Counter(byte_ops)
    operand_values = [rec[i] for rec in records for i in (1, 2, 3)]
    zero_operands = sum(v == 0 for v in operand_values)
    return {
        "instruction_count": len(records),
        "packed_lua54_invalid": packed_invalid,
        "packed_lua54_first_invalid": next(
            (start + i * 4 for i, op in enumerate(packed_ops) if op >= 83), None),
        "byte_opcode_unique": len(counter),
        "byte_opcode_min": min(byte_ops),
        "byte_opcode_max": max(byte_ops),
        "byte_opcode_top": counter.most_common(16),
        "operand_zero_fraction": zero_operands / max(1, len(operand_values)),
        "first_records": [rec.hex(" ") for rec in records[:sample_records]],
    }


def probe(mpkinfo_path, mpk_path, index):
    reader = MpkinfoReader(mpkinfo_path)
    entry = reader.entry(index)
    block = read_block(mpk_path, entry)
    sig = block.find(LUA_SIG)
    if sig < 0 or block[sig + 4:sig + 6] != b"\x54\x00":
        raise ValueError("Lua 5.4 signature not found")
    framing = locate_body(block)
    stats = inspect_records(block, framing)
    print(f"# entry[{index}] offset={entry['offset']} stored_size={entry['stored_size']} flags={entry['flags']}")
    print(f"# body marker=+0x{framing['marker']:04X} logical_body=+0x{framing['logical_body']:04X} "
          f"source_serialization={framing['source_serialization']}")
    print(f"# proto np={framing['numparams']} iv={framing['is_vararg']} ms={framing['maxstacksize']} "
          f"sizecode={framing['sizecode']} code=+0x{framing['code_start']:04X}..+0x{framing['code_end']:04X}")
    print(f"# standard Lua54 packed diagnostic: invalid_ops(>=83)={stats['packed_lua54_invalid']} "
          f"first_invalid={'+0x%04X' % stats['packed_lua54_first_invalid'] if stats['packed_lua54_first_invalid'] is not None else 'None'}")
    print(f"# bytewise [opcode,A,B,C]: opcode_unique={stats['byte_opcode_unique']} "
          f"range=0..{stats['byte_opcode_max']} operand_zero_fraction={stats['operand_zero_fraction']:.3f}")
    print(f"# opcode_top={stats['byte_opcode_top']}")
    print("# first_records:")
    for i, rec in enumerate(stats["first_records"]):
        print(f"#   {i:03d} {rec}")
    print("RESULT: BYTEWISE_4B_RECORD_LAYOUT_CANDIDATE")
    return 0


def selftest():
    # Synthetic block with two bytewise records; standard packed op 0x60 is
    # intentionally outside the official Lua 5.4 opcode enum.
    block = bytearray(0x2A)
    block[0x20] = 0x84  # source length = 3
    block[0x21:0x24] = b"@x!"
    block[0x24:0x29] = bytes([0x80, 0x80, 0, 1, 3])
    block[0x29] = 0x82  # sizecode = 2 (official terminating varint)
    block.extend(bytes([0x60, 0, 0, 0, 0x0C, 1, 2, 3]))
    f = locate_body(bytes(block))
    assert f["sizecode"] == 2 and f["source_serialization"] == "EXACT"
    s = inspect_records(bytes(block), f)
    assert s["packed_lua54_invalid"] == 1
    assert s["byte_opcode_unique"] == 2
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003U bytewise instruction-layout probe")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("mpkinfo", nargs="?")
    ap.add_argument("mpk", nargs="?")
    ap.add_argument("entry_index", nargs="?", type=int)
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not args.mpkinfo or not args.mpk or args.entry_index is None:
        ap.error("mpkinfo, mpk, entry_index required (or --selftest)")
    try:
        return probe(args.mpkinfo, args.mpk, args.entry_index)
    except (OSError, ValueError, IndexError, struct.error) as exc:
        print(f"# instruction layout probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
