#!/usr/bin/env python3
"""
probe_luat_dialect.py — NEX-002 (H-NEX-002 corrected): identify the bytecode
dialect inside a "LuaT" envelope block. Read-only research probe, NOT a decompiler.

Corrected finding (verified on LT71/LT51/LT31 samples):
    The envelope wraps a STANDARD Lua 5.4 binary chunk (32-bit Instruction):
      +0x00  u32 (custom, varies)
      +0x04  u16 = 0x03F6 (custom envelope flag)
      +0x06  "\x1bLua"        standard Lua magic
      +0x0A  0x54             Lua 5.4
      +0x0B  0x00             format = official
      +0x0C  19 93 0D 0A 1A 0A  LUAC_DATA (exact)
      +0x12  04               sizeof(Instruction) = 4  (32-bit, standard)
      +0x13  08               sizeof(lua_Integer) = 8
      +0x14  08               sizeof(lua_Number) = 8
      +0x15  ...              MODIFIED header tail (LUAC_INT/LUAC_NUM diverge)
      +0x21  "@"              source prefix (encoding not confirmed standard)

Usage:
    python probe_luat_dialect.py <mpkinfo> <mpk> <entry_index>
"""
import argparse
import struct
import sys
from inspect_mpkinfo import Mpkinfo

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
VER = {0x51: "5.1", 0x52: "5.2", 0x53: "5.3", 0x54: "5.4"}
LUAC_INT_STD = 0x5678
LUAC_NUM_STD = 370.5


def probe(mpkinfo_path, mpk_path, index):
    mp = Mpkinfo(open(mpkinfo_path, "rb").read())
    e = mp.entries[index]
    blk = open(mpk_path, "rb").read()[e["offset"]:e["offset"] + e["stored_size"]]

    print(f"# block: entry[{index}] offset={e['offset']} stored_size={e['stored_size']}")
    sig = blk.find(LUA_SIG)
    if sig < 0:
        print("RESULT: no standard Lua signature found")
        return 1

    print(f"# Lua signature at +0x{sig:04X}")
    version = blk[sig + 4]
    fmt = blk[sig + 5]
    luac = blk[sig + 6:sig + 12]
    sizes = blk[sig + 12:sig + 15]          # Lua 5.4: 3 size bytes (I/I/N)
    luac_int = blk[sig + 15:sig + 23]       # 8 bytes (expected)
    luac_num = blk[sig + 23:sig + 31]       # 8 bytes (expected)

    dialect = VER.get(version, f"unknown(0x{version:02X})")
    print(f"# version       : 0x{version:02X} => Lua {dialect}")
    print(f"# format        : 0x{fmt:02X}")
    print(f"# LUAC_DATA     : {luac.hex(' ')} match={luac == LUAC_DATA_STD}")
    print(f"# sizeof(Instr/Int/Num) = {sizes[0]}/{sizes[1]}/{sizes[2]}  (std 4/8/8)")
    instr_std = (sizes[0] == 4)
    print(f"# Instruction width = {sizes[0]} bytes  {'(standard 32-bit)' if instr_std else '(NON-STANDARD)'}")

    iv = int.from_bytes(luac_int, "little")
    nv = struct.unpack("<d", luac_num)[0]
    print(f"# LUAC_INT @ +0x{sig+15:04X} = 0x{iv:016X}  match_std={iv == LUAC_INT_STD}")
    print(f"# LUAC_NUM @ +0x{sig+23:04X} = {nv!r}  match_std={nv == LUAC_NUM_STD}")

    # first divergence vs standard Lua 5.4 header
    std_hdr = (LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
               + LUAC_INT_STD.to_bytes(8, "little") + struct.pack("<d", LUAC_NUM_STD))
    div = next((sig + i for i in range(len(std_hdr)) if blk[sig + i] != std_hdr[i]), None)
    if div is None:
        print("# header FULLY matches standard Lua 5.4")
    else:
        print(f"# first header divergence @ +0x{div:04X}")

    at = blk.find(b"@")
    if at >= 0:
        tail = blk[at:at + 48]
        printable = "".join(chr(b) if 32 <= b < 127 else "." for b in tail)
        print(f"# '@' @ +0x{at:04X}, tail: {printable!r}")

    print(f"# envelope prefix: {blk[:sig].hex(' ')}")
    print(f"RESULT: Lua {dialect} chunk (32-bit Instruction) + custom envelope; "
          f"header tail {'standard' if div is None else 'MODIFIED'}")
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
