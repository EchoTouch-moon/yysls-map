#!/usr/bin/env python3
"""
probe_lua54_metadata.py — H-NEX-003R: Lua 5.4 metadata reader (research-only).

Official Lua 5.4 varint (loadUnsigned): MSB-first 7-bit groups, LSB-first
accumulation, high bit 0x80 on the final byte:

    x = 0
    repeat: b = readByte(); x = (x << 7) | (b & 0x7f)
    until b & 0x80 != 0

CONFIRMED (4 frozen samples LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]):
  * source       : at block 0x21; length = (varint at 0x20) - 1 (single-byte
                   for all 4 samples; decoded == source_len + 1).
  * proto header : ld=0, lld=0 (varint 0x80), numparams=0, is_vararg=1,
                   maxstacksize=XX (bytes) — pattern 80 80 00 01 XX.
  * sizecode     : multi-byte varint `01 YY` (MSB-first) = 245/202/220/236;
                   the resulting code region is a valid instruction stream
                   (all opcodes <= 127) for all 4 samples.

UNRESOLVED (concrete failure point):
  * sizek @ code_end fails to parse as a standard Lua 5.4 varint count
    (LT31 0x439, LT71[1768] 0x390, LT71[1631] 0x3F0, LT51 0x40C).
    => post-code structure (sizek/constants/upvalues/protos) is a CUSTOM
       VARIANT; the constant-table walk cannot be completed deterministically.
  * narrative strings are byte-locatable (STRING_FRAMING_CANDIDATE), not
    constant-index-confirmed.

Guardrails: entry index bounds, archive offset/size bounds, seek + bounded
read (no whole-file read), version == 0x54, format == 0, fail closed,
synthetic multi-byte varint regression tests.

Usage:
    python probe_lua54_metadata.py --selftest
    python probe_lua54_metadata.py <mpkinfo> <mpk> <entry_index> [tokens...]
"""
import argparse
import os
import struct
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])
DEFAULT_TOKENS = ["NodeGraphData", "TextByNo", "EXPANSION_QINGHE", "70276", "江晏"]
VARINT_REGRESSION = [
    (bytes([0x80]), 0),
    (bytes([0xBE]), 62),
    (bytes([0x01, 0xEC]), 236),
    (bytes([0x01, 0xF5]), 245),
]


def load_unsigned(data, off):
    """Official Lua 5.4 loadUnsigned: MSB-first 7-bit groups."""
    x = 0
    i = 0
    while i < 8:
        if off + i >= len(data):
            return None, None
        b = data[off + i]
        x = (x << 7) | (b & 0x7F)
        i += 1
        if b & 0x80:
            return x, i
    return None, None


def load_int(data, off):
    return load_unsigned(data, off)


class MpkinfoReader:
    """Minimal .mpkinfo reader with bounds checks."""

    def __init__(self, path):
        with open(path, "rb") as f:
            head = f.read(8)
        if len(head) != 8:
            raise ValueError("mpkinfo too short")
        self.version, self.count = struct.unpack("<II", head)
        if self.version != 3:
            raise ValueError(f"mpkinfo version must be 3, got {self.version}")
        self._path = path
        self._head_len = 8 + self.count * 20 + 16
        st = os.path.getsize(path)
        if st != self._head_len:
            raise ValueError(f"mpkinfo size {st} != expected {self._head_len}")

    def entry(self, index):
        if not (0 <= index < self.count):
            raise IndexError(f"entry index {index} out of range 0..{self.count-1}")
        with open(self._path, "rb") as f:
            f.seek(8 + index * 20)
            raw = f.read(20)
        f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
        return {"f0": f0, "f1": f1, "offset": off, "stored_size": size, "flags": flags}


def read_block(archive_path, entry):
    st = os.path.getsize(archive_path)
    if entry["offset"] + entry["stored_size"] > st:
        raise ValueError("entry offset+size exceeds archive size (bounds check)")
    with open(archive_path, "rb") as f:
        f.seek(entry["offset"])
        return f.read(entry["stored_size"])


def parse_header(blk):
    sig = blk.find(LUA_SIG)
    if sig < 0:
        raise ValueError("no Lua signature")
    if blk[sig + 4] != 0x54:
        raise ValueError(f"Lua version must be 0x54, got 0x{blk[sig+4]:02X}")
    if blk[sig + 5] != 0:
        raise ValueError(f"format byte must be 0, got {blk[sig+5]}")
    if blk[sig + 6:sig + 12] != LUAC_DATA_STD:
        raise ValueError("LUAC_DATA mismatch")
    if list(blk[sig + 12:sig + 15]) != [4, 8, 8]:
        raise ValueError("size fields must be 4/8/8")
    return sig, blk[sig + 15:sig + 27]


def read_source(blk):
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        raise ValueError("source length varint invalid at 0x20")
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen or not src.startswith(b"@"):
        raise ValueError("source does not start with '@' or is truncated")
    return src, 0x21 + slen


def read_header(blk, body):
    if blk[body] != 0x80 or blk[body + 1] != 0x80:
        raise ValueError(f"ld/lld 0x80 0x80 not found @ +0x{body:04X}")
    off = body + 2
    np_, iv, ms = blk[off], blk[off + 1], blk[off + 2]
    off += 3
    sc, n = load_unsigned(blk, off)
    if sc is None or sc > 500000:
        raise ValueError(f"sizecode invalid @ +0x{off:04X}")
    return {"numparams": np_, "is_vararg": iv, "maxstacksize": ms,
            "sizecode": sc, "sc_bytes": blk[off:off + n].hex(" "),
            "code_start": off + n, "code_end": off + n + sc * 4}


def locate_tokens(blk, tokens):
    out = []
    for tok in tokens:
        kb = tok.encode("utf-8")
        p = blk.find(kb)
        if p < 0 or p < 1:
            out.append((tok, None, None, None, None))
            continue
        L, n = load_unsigned(blk, p - 1)
        ok = (L is not None and L - 1 == len(kb))
        out.append((tok, p, blk[p - 2] if ok else None, L if ok else None, bool(ok)))
    return out


def probe(mpkinfo_path, mpk_path, index, tokens):
    mp = MpkinfoReader(mpkinfo_path)
    e = mp.entry(index)
    blk = read_block(mpk_path, e)

    sig, tail = parse_header(blk)
    print(f"# block entry[{index}] offset={e['offset']} stored_size={e['stored_size']} "
          f"flags={e['flags']}")
    print(f"# header: Lua 5.4 fmt=0 size=4/8/8 sig@+0x{sig:04X} "
          f"custom_tail={tail.hex(' ')}")
    src, body = read_source(blk)
    printable = "".join(chr(b) if 32 <= b < 127 else "." for b in src)
    print(f"# source: +0x0021..+0x{0x21+len(src):04X} len={len(src)} "
          f"varint@{0x20}=0x{blk[0x20]:02X} decoded={len(src)+1}")
    print(f"#   head: {printable[:70]!r}")
    try:
        h = read_header(blk, body)
        print(f"# header @ +0x{body:04X}: np={h['numparams']} iv={h['is_vararg']} "
              f"ms={h['maxstacksize']} sizecode={h['sizecode']} "
              f"(varint {h['sc_bytes']}) code=+0x{h['code_start']:04X}..+0x{h['code_end']:04X}")
    except ValueError as ex:
        print(f"# header: {ex}")
    print("# tokens (byte offset, tag, len, len-1==toklen): [STRING_FRAMING_CANDIDATE]")
    for tok, p, tag, L, ok in locate_tokens(blk, tokens):
        if p is None:
            print(f"    {tok!r:24} NOT_FOUND")
        else:
            print(f"    {tok!r:24} @ +0x{p:04X} tag=0x{tag:02X} len={L} ok={ok}")
    return 0


def selftest():
    for blob, expect in VARINT_REGRESSION:
        got, _ = load_unsigned(blob, 0)
        assert got == expect, (blob.hex(" "), got, expect)
    assert load_unsigned(bytes([1] * 8), 0) == (None, None)
    # header parse selftest
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    src = b"@synthetic/path.lua"
    src_len_varint = 0x94  # 20 = 19+1
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03, 0x01, 0xF5])
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([src_len_varint])
           + src + body)
    s, tail = parse_header(blk)
    src2, body2 = read_source(blk)
    assert src2 == src
    h = read_header(blk, body2)
    assert h["numparams"] == 0 and h["is_vararg"] == 1 and h["maxstacksize"] == 3
    assert h["sizecode"] == 245, h
    # fail-closed: wrong version
    try:
        parse_header(LUA_SIG + bytes([0x53, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8]))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003R minimal Lua 5.4 metadata reader")
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
