# H-NEX-003U — LuaT 4-byte instruction layout probe

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or dialogue export.

## Finding

The four frozen samples continue to share a 4-byte record width, but their
records do not use the standard Lua 5.4 bit-packed opcode layout. The stable
candidate is a bytewise record:

```text
[opcode:1][A:1][B:1][C:1]
```

This is a layout candidate only. Opcode meanings, operand widths, control-flow
semantics, constant ownership, and nested proto ownership remain unconfirmed.

## Reproduction

```text
python tools/research/windows-static-archive/probe_instruction_layout.py --selftest
python tools/research/windows-static-archive/probe_instruction_layout.py E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk 874
```

Observed frozen samples:

| sample | body | source boundary | sizecode | packed Lua 5.4 invalid | byte-op range | unique byte-ops |
|---|---:|---|---:|---:|---:|---:|
| LT31[874] | `0x5e` | EXACT | 245 | 46 | 0..192 | 57 |
| LT71[1768] | `0x61` | PARTIAL | 202 | 43 | 0..247 | 61 |
| LT71[1631] | `0x79` | PARTIAL | 220 | 17 | 0..241 | 58 |
| LT51[1178] | `0x55` | PARTIAL | 236 | 30 | 0..248 | 54 |

The first records recur across versions, for example:

```text
60 00 00 00
1d 00 00 00
61 00 00 00
8c 00 00 00
03 81 00 00
d2 00 02 02
0c 01 00 00
83 01 01 00
52 01 02 02
```

Across all valid-marker LuaT blocks in the three archives, the probe found
3004/3004 LT31, 3030/3034 LT51, and 2861/2862 LT71 blocks with a bounded marker
and sizecode region. The first-byte field spans the full 0..255 range, so the
old `op >= 83` check is a compatibility diagnostic rather than a custom-opcode
table. A full standard Lua 5.4 decompiler is therefore still unjustified.

## Revised boundary

The framing probe now accepts segmented entries and reports
`source_serialization=PARTIAL` instead of terminating with a traceback. The
logical source-length boundary is exact only for LT31[874]; in the other three
samples the first `0x80 0x80` marker precedes the logical boundary and is used
only as a candidate body.

## Gate

`BYTEWISE_4B_RECORD_LAYOUT_CANDIDATE` plus `BOUNDARY_PARTIAL`.

The reverse-engineering ceiling moves one layer deeper: field layout and
cross-version opcode-byte recurrence are now evidenced. The next justified
step is semantic validation of candidate fields (jump targets, return/extra
argument relations, and post-code table framing) against many samples. It is
not yet justified to claim a recovered Lua VM or fully decoded quest graph.
