#!/usr/bin/env python3
"""
probe_lua54_metadata.py — NEX-003: minimal Lua 5.4 metadata reader (research-only).

What it does (bounded, read-only, fail-closed):
  - Parse the Lua 5.4 header (signature/version/format/LUAC_DATA + 3 size bytes).
  - Locate the source string (empirical: starts with '@' after the 12-byte custom
    header tail; terminated by the 0x80 0x80 marker).
  - Locate narrative tokens by plaintext scan and report their byte offsets.

What it does NOT do (honest limits, see NEX-003 report):
  - It does NOT deterministically parse the function Prototype (linedefined, code,
    loadConstants) because the post-size header tail and the source length encoding
    are CUSTOM (first divergence from official Lua 5.4 stream = absolute 0x18).
  - It does NOT perform opcode semantics or a full decompiler.

Usage:
    python probe_lua54_metadata.py <mpkinfo> <mpk> <entry_index> [tokens...]
"""
import argparse
import sys
from inspect_mpkinfo import Mpkinfo

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
VER = {0x51: "5.1", 0x52: "5.2", 0x53: "5.3", 0x54: "5.4"}
SOURCE_TERM = b"\x80\x80"  # observed end-of-source marker (empirical)

DEFAULT_TOKENS = ["NodeGraphData", "TextByNo", "EXPANSION_QINGHE", "70276", "江晏"]


def read_block(mp, mpk_path, index):
    e = mp.entries[index]
    return e, open(mpk_path, "rb").read()[e["offset"]:e["offset"] + e["stored_size"]]


def parse_header(blk):
    sig = blk.find(LUA_SIG)
    if sig < 0:
        raise ValueError("no Lua signature found")
    version = blk[sig + 4]
    if version not in VER:
        raise ValueError(f"unsupported Lua version 0x{version:02X}")
    fmt = blk[sig + 5]
    luac = blk[sig + 6:sig + 12]
    if luac != LUAC_DATA_STD:
        raise ValueError(f"LUAC_DATA mismatch: {luac.hex(' ')}")
    sizes = blk[sig + 12:sig + 15]
    if list(sizes) != [4, 8, 8]:
        raise ValueError(f"unexpected size bytes: {sizes.hex(' ')}")
    return sig, version, fmt, sizes


def locate_source(blk, sig):
    # empirical: source '@' follows the 12-byte custom tail (sig+0x1B .. sig+0x20)
    src = sig + 0x1B
    if src >= len(blk) or blk[src] != 0x40:  # 0x40 = '@'
        raise ValueError(f"source '@' not at expected offset +0x{src:04X}")
    end = blk.find(SOURCE_TERM, src)
    if end < 0:
        raise ValueError("source terminator 0x80 0x80 not found")
    return src, end, blk[src:end]


def locate_tokens(blk, tokens):
    out = []
    for tok in tokens:
        kb = tok.encode("utf-8")
        pos = blk.find(kb)
        out.append((tok, pos, kb if pos >= 0 else None))
    return out


def probe(mpkinfo_path, mpk_path, index, tokens):
    mp = Mpkinfo(open(mpkinfo_path, "rb").read())
    e, blk = read_block(mp, mpk_path, index)
    print(f"# block: entry[{index}] offset={e['offset']} stored_size={e['stored_size']}")

    sig, version, fmt, sizes = parse_header(blk)
    print(f"# header: Lua {VER[version]} format={fmt} size(Instr/Int/Num)={sizes[0]}/{sizes[1]}/{sizes[2]}")
    print(f"# custom tail: sig+0x0F..sig+0x1A = {blk[sig+15:sig+27].hex(' ')} (NOT standard LUAC_INT/NUM)")

    src, end, source = locate_source(blk, sig)
    print(f"# source @ +0x{src:04X}..+0x{end:04X} (len={len(source)} bytes)")
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in source)
    print(f"# source head: {printable[:80]!r}")

    print("# tokens (byte offset in block, plaintext scan):")
    for tok, pos, kb in locate_tokens(blk, tokens):
        if pos >= 0:
            ctx = blk[max(0, pos-4):pos+len(kb)+4]
            ctxs = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
            print(f"    {tok!r:24} @ +0x{pos:04X}  ctx={ctxs!r}")
        else:
            print(f"    {tok!r:24} NOT_FOUND")
    return 0


def selftest():
    # synthetic minimal header (standard through size bytes) + custom tail + source + terminator
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail = b"\x78\x56\x00\x01\x00\x00\x00\x28\x77\x40\x01\x00"
    src = b"@synthetic/path.lua"
    blk = hdr + tail + src + SOURCE_TERM + b"\x00\x00\x00\x00"
    sig, version, fmt, sizes = parse_header(blk)
    assert version == 0x54 and fmt == 0 and list(sizes) == [4, 8, 8]
    s, e, source = locate_source(blk, sig)
    assert source == src, (source, src)
    # fail-closed: bad size bytes
    bad = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([8, 8, 8])
    try:
        parse_header(bad)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="NEX-003 minimal Lua 5.4 metadata reader")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("mpkinfo", nargs="?")
    ap.add_argument("mpk", nargs="?")
    ap.add_argument("entry_index", nargs="?", type=int)
    ap.add_argument("--tokens", default=None, help="comma-separated tokens to locate")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        print("selftest PASS")
        return 0
    if not args.mpkinfo or not args.mpk or args.entry_index is None:
        ap.error("mpkinfo, mpk, entry_index required (or --selftest)")
    tokens = args.tokens.split(",") if args.tokens else DEFAULT_TOKENS
    return probe(args.mpkinfo, args.mpk, args.entry_index, tokens)


if __name__ == "__main__":
    sys.exit(main())
