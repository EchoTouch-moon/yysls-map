#!/usr/bin/env python3
"""
probe_luat_dialect.py — NEX-002: identify the bytecode dialect inside a "LuaT"
envelope block (read-only research probe, NOT a decompiler).

Result (confirmed on LT71/LT51/LT31 samples):
    The envelope wraps STANDARD Lua 5.4 bytecode:
      +0x00  u32 (custom, varies)
      +0x04  u16 = 0x03F6 (custom envelope flag)
      +0x06  "\x1bLua"  (standard Lua magic)
      +0x0A  0x54       (LUAC_VERSION = Lua 5.4)
      +0x0B  0x00       (LUAC_FORMAT = official)
      +0x0C  19 93 0D 0A 1A 0A  (LUAC_DATA, exact standard)
      +0x12  04 08 08   (sizeof int=4, size_t=8, Instruction=8 => 64-bit instr, MODIFIED)
      +0x21  "@"        (standard Lua source prefix)
      +0x22  source path string (segmented, length-delimited)

Usage:
    python probe_luat_dialect.py <mpkinfo> <mpk> <entry_index>

Guardrails: static read-only; reads one block; does NOT dump full dialogue/script.
"""
import argparse
import os
import struct
import sys
from inspect_mpkinfo import Mpkinfo

# Standard Lua 5.x signature + LUAC_DATA (integrity constant)
LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
# LUAC_VERSION values
VER = {0x51: "5.1", 0x52: "5.2", 0x53: "5.3", 0x54: "5.4"}


def probe(mpkinfo_path, mpk_path, index):
    mp = Mpkinfo(open(mpkinfo_path, "rb").read())
    e = mp.entries[index]
    off, size = e["offset"], e["stored_size"]
    blk = open(mpk_path, "rb").read()[off:off + size]

    print(f"# block: entry[{index}] offset={off} stored_size={size}")
    sig_pos = blk.find(LUA_SIG)
    if sig_pos < 0:
        print("RESULT: no standard Lua signature found")
        return 1

    print(f"# Lua signature at +0x{sig_pos:04X}")
    hdr = blk[sig_pos:sig_pos + 33]
    version = hdr[4]
    fmt = hdr[5]
    luac_data = hdr[6:12]
    sizes = hdr[12:17]

    dialect = VER.get(version, f"unknown(0x{version:02X})")
    modified = (sizes[2] != 4)  # standard Lua 5.4 sizeof(Instruction) == 4
    print(f"# version       : 0x{version:02X} => Lua {dialect}")
    print(f"# format        : 0x{fmt:02X}")
    print(f"# LUAC_DATA     : {luac_data.hex(' ')} (std: {LUAC_DATA_STD.hex(' ')}) match={luac_data == LUAC_DATA_STD}")
    print(f"# sizeof fields : {sizes.hex(' ')} (std Lua5.4: 04 08 04 08 08)")
    print(f"# sizeof(Instruction) = {sizes[2]} {'(MODIFIED: 64-bit instr)' if modified else '(standard)'}")

    # source string — observed at fixed offset sig_pos + 0x1B (0x21 block offset)
    src = sig_pos + 0x1B
    if src < len(blk) and blk[src] == 0x40:  # 0x40 = '@'
        tail = blk[src:src + 60]
        printable = "".join(chr(b) if 32 <= b < 127 else "." for b in tail)
        print(f"# source prefix '@' at +0x{src:04X}")
        print(f"# source head: {printable!r}")
    else:
        print(f"# source prefix '@' NOT at expected +0x{src:04X} (byte=0x{blk[src]:02X})")

    print(f"# envelope prefix: {blk[:sig_pos].hex(' ')}")
    verdict = f"modified Lua {dialect}" if modified else f"Lua {dialect}"
    print(f"RESULT: {verdict} bytecode inside custom envelope")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-002 LuaT dialect probe (read-only)")
    ap.add_argument("mpkinfo")
    ap.add_argument("mpk")
    ap.add_argument("entry_index", type=int)
    args = ap.parse_args(argv)
    return probe(args.mpkinfo, args.mpk, args.entry_index)


if __name__ == "__main__":
    sys.exit(main())
