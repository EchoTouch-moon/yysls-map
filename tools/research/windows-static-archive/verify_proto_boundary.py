#!/usr/bin/env python3
"""
verify_proto_boundary.py — H-NEX-003S/T: proto boundary & post-code section verifier.

Deterministic boundary parse (NO find("@"), NO token scan, NO guessed marker):
  source   : varint (official Lua 5.4 loadUnsigned, MSB-first) at block 0x20;
             source bytes = decoded - 1 at 0x21.  proto body = 0x21 + src_len.
  header   : linedefined = loadInt, lastlinedefined = loadInt,
             numparams / is_vararg / maxstacksize = 3 bytes,
             sizecode = loadInt.
  code     : sizecode * 4 bytes at code_start.
  sizek    : loadInt at code_end (attempted; raw bytes + decoded/failure reported).

The code check uses the OFFICIAL Lua 5.4 opcode enum as a compatibility
diagnostic only. A high count means the body is not standard Lua 5.4
bit-packed code; it does not by itself prove a bad boundary or corrupt data.

Guardrails: mpkinfo version/entry/size bounds, archive offset+size bounds,
seek + bounded read, Lua version==0x54, format==0, sizes 4/8/8, fail closed,
synthetic varint + opcode-validation regression tests.

Usage:
    python verify_proto_boundary.py --selftest
    python verify_proto_boundary.py <mpkinfo> <mpk> <entry_index>
"""
import argparse
import os
import struct
import sys

LUA_SIG = b"\x1bLua"
LUAC_DATA_STD = bytes([0x19, 0x93, 0x0D, 0x0A, 0x1A, 0x0A])

# Official Lua 5.4 opcode enum (lopcodes.h), NUM_OPCODES = 83 (0..82).
LUA54_OPCODES = [
    "MOVE", "LOADI", "LOADF", "LOADK", "LOADKX", "LOADFALSE", "LFALSESKIP",
    "LOADTRUE", "LOADNIL", "GETUPVAL", "SETUPVAL", "GETTABUP", "GETTABLE",
    "GETI", "GETFIELD", "SETTABUP", "SETTABLE", "SETI", "SETFIELD",
    "NEWTABLE", "SELF", "ADDI", "ADDK", "SUBK", "MULK", "MODK", "POWK",
    "DIVK", "IDIVK", "BANDK", "BORK", "BXORK", "SHRI", "SHLI", "ADD",
    "SUB", "MUL", "MOD", "POW", "DIV", "IDIV", "BAND", "BOR", "BXOR",
    "SHL", "SHR", "MMBIN", "MMBINI", "MMBINK", "UNM", "BNOT", "NOT",
    "LEN", "CONCAT", "CLOSE", "TBC", "JMP", "EQ", "LT", "LE", "EQK",
    "EQI", "LTI", "LEI", "GTI", "GEI", "TEST", "TESTSET", "CALL",
    "TAILCALL", "RETURN", "RETURN0", "RETURN1", "FORLOOP", "FORPREP",
    "TFORPREP", "TFORCALL", "TFORLOOP", "SETLIST", "CLOSURE", "VARARG",
    "VARARGPREP", "EXTRAARG",
]
NUM_OPCODES = len(LUA54_OPCODES)  # 83

VARINT_REGRESSION = [
    (bytes([0x80]), 0),
    (bytes([0xBE]), 62),
    (bytes([0x01, 0xEC]), 236),
    (bytes([0x01, 0xF5]), 245),
]


def load_unsigned(data, off):
    """Official Lua 5.4 loadUnsigned: MSB-first 7-bit groups; 0x80 on final byte."""
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
    def __init__(self, path):
        with open(path, "rb") as f:
            head = f.read(8)
        if len(head) != 8:
            raise ValueError("mpkinfo too short")
        self.version, self.count = struct.unpack("<II", head)
        if self.version != 3:
            raise ValueError(f"mpkinfo version must be 3, got {self.version}")
        expected = 8 + self.count * 20 + 16
        if os.path.getsize(path) != expected:
            raise ValueError(f"mpkinfo size mismatch (expected {expected})")
        self._path = path

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


def parse_lua_header(blk):
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


def parse_source(blk):
    """Source varint at 0x20 (official MSB-first); source_len = decoded - 1."""
    L, n = load_unsigned(blk, 0x20)
    if L is None or L < 2:
        raise ValueError("source length varint invalid at 0x20")
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen or not src.startswith(b"@"):
        raise ValueError("source does not start with '@' or is truncated")
    return src, 0x21 + slen


def parse_proto_header(blk, body):
    """Standard Lua 5.4 loadFunction fields after source."""
    ld, n = load_int(blk, body)
    if ld is None or ld > 10**7:
        return None, f"linedefined invalid @ +0x{body:04X}"
    off = body + n
    lld, n = load_int(blk, off)
    if lld is None or lld > 10**7:
        return None, f"lastlinedefined invalid @ +0x{off:04X}"
    off += n
    if off + 3 > len(blk):
        return None, "truncated numparams/is_vararg/maxstacksize"
    np_, iv, ms = blk[off], blk[off + 1], blk[off + 2]
    off += 3
    sc, n = load_int(blk, off)
    if sc is None or sc > 500000:
        return None, f"sizecode invalid @ +0x{off:04X}"
    off += n
    code_end = off + sc * 4
    if code_end > len(blk):
        return None, f"code overruns block (sc={sc} -> +0x{code_end:04X})"
    return {"linedefined": ld, "lastlinedefined": lld, "numparams": np_,
            "is_vararg": iv, "maxstacksize": ms, "sizecode": sc,
            "code_start": off, "code_end": code_end}, None


def validate_code(blk, code_start, code_end):
    """Report incompatibility with standard Lua 5.4 packed opcodes."""
    invalid = []
    for i in range(code_start, code_end, 4):
        instr = struct.unpack_from("<I", blk, i)[0]
        op = instr & 0x7F
        if op >= NUM_OPCODES:
            invalid.append((i, op))
    first = invalid[0][0] if invalid else None
    return {
        "instruction_count": (code_end - code_start) // 4,
        "invalid_opcode_count": len(invalid),
        "first_invalid_offset": first,
        "invalid_samples": invalid[:8],
    }


def attempt_sizek(blk, code_end):
    raw = blk[code_end:code_end + 32]
    nk, n = load_int(blk, code_end)
    if nk is None:
        return {"raw32": raw.hex(" "), "decoded": None,
                "reason": "varint truncated at block end"}
    if nk > 500000:
        return {"raw32": raw.hex(" "), "decoded": nk,
                "reason": f"decoded {nk} exceeds plausible sizek cap (500000)"}
    return {"raw32": raw.hex(" "), "decoded": nk, "reason": None}


def verify(mpkinfo_path, mpk_path, index):
    mp = MpkinfoReader(mpkinfo_path)
    e = mp.entry(index)
    blk = read_block(mpk_path, e)
    out = {"entry": index, "offset": e["offset"], "stored_size": e["stored_size"],
           "flags": e["flags"]}

    sig, tail = parse_lua_header(blk)
    out["lua"] = {"sig_offset": sig, "custom_tail": tail.hex(" ")}

    src, body = parse_source(blk)
    out["source"] = {
        "len": len(src), "varint_byte": hex(blk[0x20]),
        "decoded": len(src) + 1, "body_offset": body,
        "head": "".join(chr(b) if 32 <= b < 127 else "." for b in src[:60]),
    }

    hdr, err = parse_proto_header(blk, body)
    if err:
        out["proto"] = {"status": "HEADER_FAIL", "reason": err,
                        "body_offset": body,
                        "bytes_at_body": blk[body:body + 16].hex(" "),
                        "source_serialization": "PARTIAL"}
    else:
        out["proto"] = {"status": "HEADER_OK", "body_offset": body, **hdr}
        out["code"] = validate_code(blk, hdr["code_start"], hdr["code_end"])
        out["sizek"] = attempt_sizek(blk, hdr["code_end"])
        out["sizek"]["code_end"] = hdr["code_end"]

    # Phase E: candidate boundary using the FIRST 0x80 0x80 after 0x21.
    marker = blk.find(b"\x80\x80", 0x21)
    if marker >= 0:
        ch, cerr = parse_proto_header(blk, marker)
        if cerr is None:
            out["candidate"] = {"marker_offset": marker, "status": "HEADER_OK",
                                **ch}
            out["candidate"]["code"] = validate_code(blk, ch["code_start"],
                                                     ch["code_end"])
            out["candidate"]["raw32_at_code_end"] = \
                blk[ch["code_end"]:ch["code_end"] + 32].hex(" ")
        else:
            out["candidate"] = {"marker_offset": marker, "status": "HEADER_FAIL",
                                "reason": cerr}
    return out


def print_report(r):
    print(f"# entry[{r['entry']}] offset={r['offset']} stored_size={r['stored_size']} "
          f"flags={r['flags']}")
    print(f"# lua: sig@+0x{r['lua']['sig_offset']:04X} custom_tail={r['lua']['custom_tail']}")
    s = r["source"]
    print(f"# source: len={s['len']} varint@{0x20}=0x{s['varint_byte']} "
          f"decoded={s['decoded']} body=+0x{s['body_offset']:04X} head={s['head']!r}")
    p = r["proto"]
    if p["status"] == "HEADER_FAIL":
        print(f"# proto: HEADER_FAIL @ +0x{p['body_offset']:04X}: {p['reason']}")
        print(f"#   bytes@body: {p['bytes_at_body']}")
        print(f"#   SOURCE_SERIALIZATION={p['source_serialization']}")
    else:
        print(f"# proto: ld={p['linedefined']} lld={p['lastlinedefined']} "
              f"np={p['numparams']} iv={p['is_vararg']} ms={p['maxstacksize']} "
              f"sc={p['sizecode']} code=+0x{p['code_start']:04X}..+0x{p['code_end']:04X}")
        c = r["code"]
        print(f"# code: count={c['instruction_count']} "
              f"packed_lua54_invalid_ops(>=83)={c['invalid_opcode_count']} "
              f"first_invalid={'+0x%04X' % c['first_invalid_offset'] if c['first_invalid_offset'] is not None else 'None'}")
        for pos, op in c["invalid_samples"]:
            print(f"#   invalid @ +0x{pos:04X} op={op}")
        k = r["sizek"]
        print(f"# sizek@+0x{k['code_end']:04X}: raw32={k['raw32']}")
        print(f"#   decoded={k['decoded']} reason={k['reason']}")
    if "candidate" in r:
        cand = r["candidate"]
        if cand["status"] == "HEADER_OK":
            cc = cand["code"]
            print(f"# candidate(first 0x80 0x80 @ +0x{cand['marker_offset']:04X}): "
                  f"sc={cand['sizecode']} code=+0x{cand['code_start']:04X}..+0x{cand['code_end']:04X} "
                  f"packed_lua54_invalid_ops={cc['invalid_opcode_count']}")
            print(f"# candidate raw32@code_end: {cand['raw32_at_code_end']}")
        else:
            print(f"# candidate(first 0x80 0x80 @ +0x{cand['marker_offset']:04X}): "
                  f"HEADER_FAIL {cand['reason']}")


def selftest():
    for blob, expect in VARINT_REGRESSION:
        got, _ = load_unsigned(blob, 0)
        assert got == expect, (blob.hex(" "), got, expect)
    assert load_unsigned(bytes([1] * 8), 0) == (None, None)
    # opcode validation: op 78/79/82 valid; op 83 invalid
    op78 = struct.pack("<I", 0x4E)   # op 78 (SETLIST)
    op79 = struct.pack("<I", 0x4F)   # op 79 (CLOSURE)
    op82 = struct.pack("<I", 0x52)   # op 82 (EXTRAARG)
    bad = struct.pack("<I", 0x53)    # op 83 (>= NUM_OPCODES)
    blk = op78 + op79 + op82 + bad
    r = validate_code(blk, 0, 16)
    assert r["invalid_opcode_count"] == 1, r
    assert r["first_invalid_offset"] == 12, r
    assert r["instruction_count"] == 4, r
    # boundary parse selftest
    hdr = LUA_SIG + bytes([0x54, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8])
    tail11 = bytes([0x78, 0x56, 0x00, 0x01, 0x00, 0x00, 0x00, 0x28, 0x77, 0x40, 0x01])
    src = b"@synthetic/path.lua"
    body = bytes([0x80, 0x80, 0x00, 0x01, 0x03, 0x01, 0xF5])  # ld lld np iv ms sc=245
    code = bytes([0x0C, 0x00, 0x00, 0x00]) * 245  # 245 x GETTABLE (op 12)
    blk = (b"\xf2\xe8\x00\x00\xf6\x03" + hdr + tail11 + bytes([0x94]) + src + body + code)
    s, tail = parse_lua_header(blk)
    src2, body2 = parse_source(blk)
    assert src2 == src
    h, err = parse_proto_header(blk, body2)
    assert err is None and h["sizecode"] == 245 and h["numparams"] == 0
    assert h["is_vararg"] == 1 and h["maxstacksize"] == 3
    cr = validate_code(blk, h["code_start"], h["code_end"])
    assert cr["invalid_opcode_count"] == 0, cr
    # fail-closed: wrong version
    try:
        parse_lua_header(LUA_SIG + bytes([0x53, 0x00]) + LUAC_DATA_STD + bytes([4, 8, 8]))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003S/T proto boundary verifier")
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
    r = verify(args.mpkinfo, args.mpk, args.entry_index)
    print_report(r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
