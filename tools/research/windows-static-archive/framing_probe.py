#!/usr/bin/env python3
"""
framing_probe.py — H-NEX-003T: LuaT instruction framing & sizecode boundary probe.

The original control is LT31[874]. Segmented LT51/LT71 entries are also
accepted when their logical source-length boundary does not contain the proto
header: the first bounded ``0x80 0x80`` marker is reported as a candidate body
and the source serialization is explicitly marked PARTIAL.
Deterministic Phase A fields: source length, candidate body start,
numparams, is_vararg, and maxstacksize. LT31[874] remains the control sample;
segmented samples are explicitly marked PARTIAL.
Then records the raw 32 bytes after maxstacksize (no field naming).

Phase B tests only a bounded set of framing hypotheses:

  H0 : sizecode = loadInt (official MSB-first) at maxstacksize+1; code begins
       immediately after the sizecode varint; little-endian 32-bit instructions.
  H1 : same sizecode + 0/1/2/3-byte alignment adjustment before first instruction.
  H2 : same candidate boundaries as H0/H1, but instructions interpreted
       big-endian (opcode = low 7 bits of the big-endian word).
  H3 : one bounded custom field (1 byte) before the sizecode/code.

For each hypothesis, outputs:
  candidate_sizecode, code_start, instruction_count,
  invalid_opcode_count (>=83), first_invalid_offset, first 8 decoded opcodes.

Phase C (only if invalid_opcode_count == 0): lightweight Lua 5.4 invariants
  LOADKX(4) -> next EXTRAARG(82); NEWTABLE(19) with extra-arg -> next EXTRAARG;
  records presence of RETURN(70)/RETURN0(71)/RETURN1(72)/VARARGPREP(81)
  (presence is recorded, not used as a gate).

Phase D: stop condition — if no hypothesis yields a trusted standard Lua 5.4
instruction stream, the honest gate is INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED.

NO opcode semantics / CFG / decompiler. NO token-based winner selection.
Guardrails: bounds checks, seek+bounded read, fail closed, synthetic selftest.

Usage:
    python framing_probe.py --selftest
    python framing_probe.py <mpkinfo> <mpk> <entry_index>
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


class MpkinfoReader:
    def __init__(self, path):
        with open(path, "rb") as f:
            head = f.read(8)
        if len(head) != 8:
            raise ValueError("mpkinfo too short")
        self.version, self.count = struct.unpack("<II", head)
        if self.version != 3:
            raise ValueError(f"mpkinfo version must be 3, got {self.version}")
        if os.path.getsize(path) != 8 + self.count * 20 + 16:
            raise ValueError("mpkinfo size mismatch")
        self._path = path

    def entry(self, index):
        if not (0 <= index < self.count):
            raise IndexError(f"entry index {index} out of range 0..{self.count-1}")
        with open(self._path, "rb") as f:
            f.seek(8 + index * 20)
            raw = f.read(20)
        f0, f1, off, size, flags = struct.unpack("<IIIII", raw)
        return {"offset": off, "stored_size": size, "flags": flags}


def read_block(archive_path, entry):
    st = os.path.getsize(archive_path)
    if entry["offset"] + entry["stored_size"] > st:
        raise ValueError("entry offset+size exceeds archive size (bounds check)")
    with open(archive_path, "rb") as f:
        f.seek(entry["offset"])
        return f.read(entry["stored_size"])


def frozen_proto(blk):
    """Read the common proto marker and classify source/body agreement."""
    sig = blk.find(LUA_SIG)
    if sig < 0 or blk[sig + 4] != 0x54 or blk[sig + 5] != 0:
        raise ValueError("not Lua 5.4 fmt 0")
    if list(blk[sig + 12:sig + 15]) != [4, 8, 8]:
        raise ValueError("sizes != 4/8/8")
    L, n = load_unsigned(blk, 0x20)
    slen = L - 1
    src = blk[0x21:0x21 + slen]
    if len(src) != slen:
        raise ValueError("source truncated")
    logical_body = 0x21 + slen
    marker = blk.find(b"\x80\x80", 0x21)
    if marker < 0:
        raise ValueError("ld/lld marker missing after source")
    body = logical_body if marker == logical_body else marker
    source_serialization = "EXACT" if marker == logical_body else "PARTIAL"
    if body + 4 >= len(blk):
        raise ValueError("proto marker truncated")
    np_, iv, ms = blk[body + 2], blk[body + 3], blk[body + 4]
    if (np_, iv) != (0, 1) or not (2 <= ms <= 255):
        raise ValueError(f"unexpected np/iv/ms ({np_},{iv},{ms})")
    tail32 = blk[body + 5:body + 5 + 32]
    return {"src_len": slen, "logical_body": logical_body, "body": body,
            "marker": marker, "source_serialization": source_serialization,
            "np": np_, "iv": iv, "ms": ms, "after_ms32": tail32.hex(" ")}


# Backward-compatible name used by earlier notebooks.
frozen_lt31 = frozen_proto


def decode_ops(blk, code_start, count, big_endian=False):
    ops = []
    for i in range(code_start, code_start + count * 4, 4):
        if big_endian:
            v = struct.unpack_from(">I", blk, i)[0]
        else:
            v = struct.unpack_from("<I", blk, i)[0]
        ops.append(v & 0x7F)
    return ops


def hypothesis_result(blk, code_start, count, big_endian=False):
    ops = decode_ops(blk, code_start, count, big_endian)
    invalid = [op for op in ops if op >= NUM_OPCODES]
    first = None
    for idx, op in enumerate(ops):
        if op >= NUM_OPCODES:
            first = code_start + idx * 4
            break
    return {
        "code_start": code_start,
        "instruction_count": count,
        "invalid_opcode_count": len(invalid),
        "first_invalid_offset": first,
        "first8_ops": ops[:8],
    }


def structural_sanity(blk, code_start, count):
    """Phase C lightweight invariants (only meaningful if 0 invalid)."""
    ops = decode_ops(blk, code_start, count)
    out = {"extraarg_after_loadkx": 0, "extraarg_after_newtable": 0,
           "ret_family": 0, "varargprep": 0}
    for i in range(count):
        op = ops[i]
        if op in (70, 71, 72):
            out["ret_family"] += 1
        if op == 81:
            out["varargprep"] += 1
        if op == 4 and i + 1 < count and ops[i + 1] == 82:
            out["extraarg_after_loadkx"] += 1
        if op == 19 and i + 1 < count and ops[i + 1] == 82:
            out["extraarg_after_newtable"] += 1
    return out


def probe(mpkinfo_path, mpk_path, index):
    mp = MpkinfoReader(mpkinfo_path)
    e = mp.entry(index)
    blk = read_block(mpk_path, e)
    f = frozen_proto(blk)
    print(f"# proto framing: src_len={f['src_len']} logical_body=+0x{f['logical_body']:04X} "
          f"body=+0x{f['body']:04X} marker=+0x{f['marker']:04X} "
          f"source_serialization={f['source_serialization']} "
          f"np={f['np']} iv={f['iv']} ms={f['ms']}")
    print(f"# after maxstacksize 32B (raw): {f['after_ms32']}")
    after = f["body"] + 5  # first byte after maxstacksize

    # H0: sizecode = loadInt(after) = `01 F5` = 245; code immediately after.
    sc0, n0 = load_unsigned(blk, after)
    print(f"\n# H0: sizecode=loadInt(+0x{after:04X}) = {sc0} ({blk[after:after+n0].hex(' ')})")
    for adj in range(4):
        cs = after + n0 + adj
        ce = cs + sc0 * 4
        if ce > len(blk):
            continue
        r = hypothesis_result(blk, cs, sc0)
        print(f"   H1(adj={adj}) cs=+0x{cs:04X} sc={sc0} count={r['instruction_count']} "
              f"invalid={r['invalid_opcode_count']} first_invalid="
              f"{'+0x%04X' % r['first_invalid_offset'] if r['first_invalid_offset'] else 'None'} "
              f"ops8={r['first8_ops']}")
        if r["invalid_opcode_count"] == 0:
            print(f"   H1(adj={adj}) structural: {structural_sanity(blk, cs, sc0)}")
    # H2: big-endian interpretation of the same boundaries.
    for adj in range(4):
        cs = after + n0 + adj
        ce = cs + sc0 * 4
        if ce > len(blk):
            continue
        r = hypothesis_result(blk, cs, sc0, big_endian=True)
        print(f"   H2(BE,adj={adj}) cs=+0x{cs:04X} sc={sc0} invalid={r['invalid_opcode_count']} "
              f"first_invalid="
              f"{'+0x%04X' % r['first_invalid_offset'] if r['first_invalid_offset'] else 'None'} "
              f"ops8={r['first8_ops']}")
    # H3: one bounded custom field before sizecode/code (custom = the 0x01 byte).
    cf = after                      # custom field byte
    sc3, n3 = load_unsigned(blk, cf + 1)
    if sc3 is not None and sc3 <= 200000:
        cs = cf + 1 + n3
        ce = cs + sc3 * 4
        if ce <= len(blk):
            r = hypothesis_result(blk, cs, sc3)
            print(f"\n# H3: custom_field=0x{blk[cf]:02X}@{cf:#06x} sizecode={sc3} "
                  f"cs=+0x{cs:04X} count={r['instruction_count']} "
                  f"invalid={r['invalid_opcode_count']} "
                  f"first_invalid="
                  f"{'+0x%04X' % r['first_invalid_offset'] if r['first_invalid_offset'] else 'None'} "
                  f"ops8={r['first8_ops']}")
            if r["invalid_opcode_count"] == 0:
                print(f"   H3 structural: {structural_sanity(blk, cs, sc3)}")
    return 0


def selftest():
    for blob, expect in VARINT_REGRESSION:
        got, _ = load_unsigned(blob, 0)
        assert got == expect, (blob.hex(" "), got, expect)
    assert load_unsigned(bytes([1] * 8), 0) == (None, None)
    # opcode decode: LE vs BE
    blk = struct.pack("<I", 0x0C) + struct.pack(">I", 0x0C)
    ops_le = decode_ops(blk, 0, 1)
    ops_be = decode_ops(blk, 4, 1, big_endian=True)
    assert ops_le == [12] and ops_be == [12], (ops_le, ops_be)
    # invalid detection: op 83 invalid
    blk2 = struct.pack("<I", 0x53)  # op 83
    r = hypothesis_result(blk2, 0, 1)
    assert r["invalid_opcode_count"] == 1 and r["first_invalid_offset"] == 0
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="H-NEX-003T LT31 framing probe")
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
        print(f"# framing probe unavailable: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
