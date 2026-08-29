# H-NEX-003AE — Official Lua 5.4 constant-table walk at code_end

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_constant_table.py`
> (deterministic, selftested, fail-closed per block; sizek capped at 4096,
> histograms capped at 32).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

003AD rejected length framing and noted the surviving reading: the post-code
region may be the proto's **constant table** in official `loadConstant`
layout `[sizek][tag][value]`, with official dumped tags (Lua 5.4 `makevariant`):
0x00 nil, 0x01 false, 0x11 true, 0x03 float (8B), 0x13 int (8B), 0x04
short-string, 0x14 long-string; strings via official `loadString`
(varint size s, then s−1 bytes). Note the pre-existing coincidence: the 003AC
dominant framing bytes 0x04 (successor parse 0.94–0.97) and 0x14 (0.61–0.80)
are exactly the official short/long-string tags, and the "record" that
followed them had precisely the `loadString` shape `[varint][v−1]`.

Pre-registered gate: `CONSTANT_TABLE_CANDIDATE` if clean consumption
(constants_complete + full_consumed) ≥ 50% of blocks AND official-tag share
≥ 90%; else `CONSTANT_TABLE_PARTIAL`.

## Findings

### F1 — The official tagged constant table does NOT fit

Outcome census (LT31 / LT51 / LT71), fractions of 3055 / 3070 / 2898 blocks:

| outcome | LT31 | LT51 | LT71 |
|---|---:|---:|---:|
| no_sizek (no varint in 8 B) | 1107 (36.2%) | 1096 (35.7%) | 1096 (37.8%) |
| sizek_unreasonable (> 4096) | 1050 (34.4%) | 1058 (34.5%) | 974 (33.6%) |
| bad_tag (sizek ok, next byte not a tag) | 873 (28.6%) | 888 (28.9%) | 797 (27.5%) |
| truncated | 7 | 4 | 10 |
| **constants_complete / full_consumed** | **18 / 0** | **24 / 0** | **21 / 0** |

`complete_frac` = 0.006 / 0.008 / 0.007. `RESULT: CONSTANT_TABLE_PARTIAL` in
all three archives. Zero blocks fully consume the tail as `[sizek][tags]`.

### F2 — The three failure modes reproduce the 003AD partition

The census is consistent with 003AD to within a few blocks: `no_sizek`
(1107) equals 003AD's no-varint count exactly; `sizek_unreasonable` (1050)
matches the large-value overflow population (1043); the residual small-varint
blocks become `bad_tag` here because the byte after a plausible count is a
text character, not a constant tag. The opening bytes are robustly
three-way: text run (~36%), large varint (~34%), small-varint-then-text (~29%).

### F3 — Where constants parse, the dominant tag is 0x04; the rest is text

Tag-byte histogram over consumed constants (LT31 top): 0x04 ×496, then
non-official 0x72 'r' ×240, then 0x14 ×54, 0x00 ×49, 0x68 'h' ×42, 0x01 ×36,
0x61 'a' ×31. Official-tag share is only 0.436–0.460. The bad-tag census is
dominated by printable ASCII ('r','h','a','C','c','3','Z','.','b','e').
String bodies that do parse are 0.626–0.641 printable. So the region is
text/string-heavy, and 0x04 (short-string) is the single most common
official tag — but the surrounding bytes are raw text, not a tagged table.

## Gate

`RESULT: CONSTANT_TABLE_PARTIAL` in all three archives.

## Interpretation

Five structural models of the post-code region are now decisively rejected on
~9,000 blocks: flat record stream, pure recursive TLV, interleaved
control/record tokenizer, length prefix, and official tagged constant table.
The convergent positive picture is text/string content organized by a
mechanism that is NOT any of these: 0x04 and 0x14 repeatedly behave as
string markers followed by `loadString`-shaped `[varint][v−1]` payloads, the
region is text-heavy (~63% printable string bodies), and the opening bytes
split into a stable three-way census.

The single most promising surviving reading is a **string table without a
count/tag prefix**: entries are concatenated official `loadString` records
(self-delimiting by their size varint), possibly preceded by per-entry
framing. The 36% text-led blocks indicate that in many protos the first bytes
are themselves string content, so any such walk must tolerate or explain a
text opening rather than assume a count at offset 0.

## Next justified step

**Raw concatenated loadString walk (H-NEX-003AF candidate)**: without a
sizek/tag prefix, repeatedly parse `[varint size][size−1 bytes]` at the
current offset across the tail, restricting to sane sizes (e.g. ≤ 4096), and
report clean-run length, byte coverage, and the offset of the first parse
failure — run both from offset 0 and from the first 0x04/0x14 marker. If
coverage concentrates high from a marker offset, the region is a string table
and the marker census becomes the framing table; if it collapses everywhere,
string-table framing is rejected and the residual three-way census is the
terminal description of the region.
