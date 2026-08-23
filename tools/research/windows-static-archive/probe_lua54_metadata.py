#!/usr/bin/env python3
"""
probe_lua54_metadata.py — H-NEX-003: Lua 5.4 metadata reader (research-only).

CONFIRMED encodings (from >=4 frozen samples):
  * source       : at block 0x21 (after 12-byte custom header tail); length =
                   (convB varint at 0x20) - 1.  convB = high bit SET = final
                   byte (7 bits/byte, LSB-first).
  * proto header : ld = 0x80 (=0), lld = 0x80 (=0) [convB]; then numparams,
                   is_vararg, maxstacksize as 1-byte fields. Observed across
                   samples as pattern: 80 80 00 01 XX 01 (ld=0 lld=0 np=0 iv=1
                   ms=XX).
  * string consts: [tag byte][convB varint len][len-1 bytes].  Tags seen:
                   04,05,06,07,08,14,15,16,...

NOT fully resolved (documented in H-NEX-003 report):
  * the sizecode / code / upvalues / nested-proto walk between the header and
    the first constant table (custom layout; sizecode byte after maxstacksize
    is ambiguous).  Therefore "constant index" and "owning proto" are NOT
    reported; byte offsets + tag + length + value ARE reported.

Usage:
    python probe_lua54_metadata.py --selftest
    python probe_lua54_metadata.py <mpkinfo> <mpk> <entry_index> [tokens...]
"""
import argparse
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
VER = {0x54: "Lua 5.4"}
DEFAULT_TOKENS = ["NodeGraphData", "TextByNo", "EXPANSION_QINGHE", "70276", "江晏"]


def varint_b(data, off):
    """convB varint: 7 bits/byte LSB-first, high bit SET = final byte."""
    x = 0
    shift = 0
    n = 0
    while n < 8:
        if off + n >= len(data):
            return None, None
        b = data[off + n]
        x |= (b & 0x7F) << (7 * shift)
        n += 1
        if b >= 0x80:
            return x, n
        shift += 1
    return x, n


def parse_header(blk):
    """Standard Lua 5.4 header through the 3 size fields; then 12-byte custom tail."""
    sig = blk.find(LUA_SIG)
    if sig < 0:
        raise ValueError("no Lua signature")
    if blk[sig + 4] not in VER:
        raise ValueError(f"unsupported Lua version 0x{blk[sig+4]:02X} (must be 0x54)")
    if blk[sig + 5] != 0:
        raise ValueError(f"format byte must be 0, got {blk[sig+5]}")
    if blk[sig + 6:sig + 12] != LUAC_DATA_STD:
        raise ValueError("LUAC_DATA mismatch")
    sizes = list(blk[sig + 12:sig + 15])
    if sizes != [4, 8, 8]:
        raise ValueError(f"size fields must be 4/8/8, got {sizes}")
    tail = blk[sig + 15:sig + 27]  # custom 12-byte tail (not standard LUAC_INT/NUM)
    return sig, tail


def read_source(blk):
    """Source at 0x21; length = (convB varint at 0x20) - 1."""
    L, n = varint_b(blk, 0x20)
    if L is None or L < 2:
        raise ValueError("source length varint invalid at 0x20")
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen or not src.startswith(b"@"):
        raise ValueError("source does not start with '@' or is truncated")
    return src, 0x21 + slen


def read_header_fields(blk, body_off):
    """ld/lld = 0x80 (convB 0); np/iv/ms = 3 bytes; return the sizecode candidate."""
    if blk[body_off] != 0x80 or blk[body_off + 1] != 0x80:
        raise ValueError(f"ld/lld marker 0x80 0x80 not found @ +0x{body_off:04X}")
    ld, n = varint_b(blk, body_off)
    off = body_off + n
    lld, n = varint_b(blk, off)
    off += n
    np_, iv, ms = blk[off], blk[off + 1], blk[off + 2]
    off += 3
    sc = blk[off]
    return {"ld": ld, "lld": lld, "numparams": np_, "is_vararg": iv,
            "maxstacksize": ms, "sizecode_byte": sc, "sc_pos": off}


def locate_tokens(blk, tokens):
    out = []
    for tok in tokens:
        kb = tok.encode("utf-8")
        p = blk.find(kb)
        if p < 0 or p < 1:
            out.append((tok, None, None, None, None))
            continue
        L, n = varint_b(blk, p - 1)
        ok = (L is not None and L - 1 == len(kb))
        if ok:
            out.append((tok, p, blk[p - 2], L, True))
        else:
            out.append((tok, p, None, None, False))
    return out


def probe(mpkinfo_path, mpk_path, index, tokens):
    from inspect_mpkinfo import Mpkinfo
    mp = Mpkinfo(open(mpkinfo_path, "rb").read())
    e = mp.entries[index]
    blk = open(mpk_path, "rb").read()[e["offset"]:e["offset"] + e["stored_size"]]

    sig, tail = parse_header(blk)
    print(f"# block entry[{index}] offset={e['offset']} stored_size={e['stored_size']}")
    print(f"# header: {VER[blk[sig+4]]} fmt={blk[sig+5]} size=4/8/8 sig@+0x{sig:04X}")
    print(f"# custom tail (12B, non-standard): {tail.hex(' ')}")

    src, body = read_source(blk)
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in src)
    print(f"# source: +0x0021..+0x{0x21+len(src):04X} len={len(src)} "
          f"varint@{0x20}=0x{blk[0x20]:02X}({blk[0x20]&0x7F}+0x80) -> len+1={len(src)+1}")
    print(f"#   head: {printable[:70]!r}")

    try:
        h = read_header_fields(blk, body)
        print(f"# header variant @ +0x{body:04X}: ld={h['ld']} lld={h['lld']} "
              f"np={h['numparams']} iv={h['is_vararg']} ms={h['maxstacksize']} "
              f"sizecode_candidate=0x{h['sizecode_byte']:02X}@{h['sc_pos']:#06x} (unresolved)")
    except ValueError as ex:
        print(f"# header variant: {ex}")

    print("# tokens (byte offset, tag, len, len-1==toklen):")
    for tok, p, tag, L, ok in locate_tokens(blk, tokens):
        if p is None:
            print(f"    {tok!r:24} NOT_FOUND")
        else:
            print(f"    {tok!r:24} @ +0x{p:04X} tag=0x{tag:02X} len={L} ok={ok}")
    return 0


def selftest():
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    src = b"@synthetic/path.lua"
    # source len varint (convB) at 0x20: len(src)+1 = 20 -> 0x94
    src_len_varint = 0x94
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03, 0x01, 0xF5, 0x60])
    const = bytes([0x04, 0x8E]) + b"NodeGraphData"
    # 0x00-0x05 envelope, 0x06-0x14 hdr, 0x15-0x1F tail11, 0x20 varint, 0x21+ src
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([src_len_varint])
           + src + body + const)
    s, tail2 = parse_header(blk)
    src2, body2 = read_source(blk)
    assert src2 == src, (src2, src)
    h = read_header_fields(blk, body2)
    assert h["ld"] == 0 and h["lld"] == 0 and h["numparams"] == 0 and h["is_vararg"] == 1
    assert h["maxstacksize"] == 3
    # fail-closed: wrong version
    try:
        parse_header(LUA_SIG + bytes([0x53, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8]))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003 minimal Lua 5.4 metadata reader")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("mpkinfo", nargs="?")
    ap.add_argument("mpk", nargs="?")
    ap.add_argument("entry_index", nargs="?", type=int)
    ap.add_argument("--tokens", default=None)
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
