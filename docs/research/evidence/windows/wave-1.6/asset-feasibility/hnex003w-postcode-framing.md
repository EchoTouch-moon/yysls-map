# H-NEX-003W — Post-code section framing classification

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_postcode_framing.py`
> (deterministic, selftested, bounded 256-byte scan window per block).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Tests

Five bounded classifications of the bytes after `code_end`:

- **W1 printable-run structure**: offset of the first printable ASCII run
  (length ≥ 4), run-length median, run count per block.
- **W2 leading-byte position histograms**: per-position byte concentration
  over the first 16 trailing bytes (fixed-header detector).
- **W3 string-framing hypotheses at starts 0..16**: official loadString
  varint (H-official), one-byte length (H-u8), Lua-style one-byte size
  (H-u8s), little-endian two-byte length (H-u16).
- **W4 small-integer scan**: u32-LE values below 1000 in the first 64 bytes
  (count-field detector).
- **W5 run texture**: longest-run terminator byte histogram; space vs
  underscore/dot character mix (identifier-style vs sentence-style).

Blocks used (same bounded selection as H-NEX-003V): LT31 3055, LT51 3070,
LT71 2898. Every block has a non-empty tail.

## Findings

### F1 — Dense interleaved texture, no fixed header

- printable byte fraction of the first 256 trailing bytes: **0.545–0.546**
  in all three archives;
- **~99% of blocks contain ≥ 12 distinct printable runs** within the first
  256 bytes (run-count mode = 12, the reporting cap); median run length 7;
- the first run starts at offset **0 in 43–46%** of blocks
  (LT31: 1352/3055; LT51: 1323/3070; LT71: 1320/2898), with the remainder
  spread over offsets 1–7;
- W2 finds **no concentrated leading byte at any position** (max share
  0.126 at position +1, LT51). There is no fixed-width section header at
  `code_end`.

### F2 — Boundary-aligned string framing fails

Hit counts are diffuse across start offsets and at chance level:

| hypothesis | best (offset, hits) LT31 / LT51 / LT71 | share |
|---|---|---:|
| H-official (loadString varint) | (2,250) / (2,274) / (2,224) | ≤ 9% |
| H-u8 (one-byte length) | (15,76) / (15,65) / (14,60) | ≤ 2.5% |
| H-u8s (Lua-style size) | (4,45) / (15,41) / (4,41) | ≤ 1.5% |
| H-u16 (two-byte length) | ≤ 2 hits everywhere | ~0% |

W4 median count of small u32-LE values (< 1000) in the first 64 bytes is
**0** for all three archives: the section does not open with plain integer
count fields either. This confirms and generalizes the H-NEX-003R
`sizek @ code_end` failure from four samples to ~9,000 blocks.

### F3 — Dominant delimiter candidate: 0x04

The longest printable run's terminator byte is strikingly stable:

| terminator | LT31 | LT51 | LT71 |
|---|---:|---:|---:|
| **0x04** | **1334 (43.7%)** | **1290 (42.0%)** | **1228 (42.4%)** |
| 0x00 | 492 (16.1%) | 546 (17.8%) | 506 (17.5%) |
| 0x12 | 405 (13.3%) | 409 (13.3%) | 414 (14.3%) |
| 0x09 | 132 (4.3%) | 157 (5.1%) | 142 (4.9%) |

Combined with the H-NEX-003V observation that `0x04` is also the most
frequent first trailing byte (284/257/218), the byte `0x04` consistently
frames string-like payloads at both ends of the section. This is a
delimiter/tag candidate, not yet a proven framing rule: `0x04` also appears
inside the binary-looking gaps, so segment boundaries are not yet
deterministic from this statistic alone.

### F4 — Trailing text is identifier-style, not prose

Character mix inside printable runs (all three archives):

- space fraction: **0.005**
- underscore + dot fraction: **0.070**

The post-code text is overwhelmingly identifier/key-shaped, not
sentence-shaped. A manual hex sample (LT31 entry[874], not committed)
shows behavior-script-like name fragments such as `…SetBlackboard`,
`…GetEntityAttr`, `…ChooseTarg…`, `…AlwaysSequence…`. Under the content
boundary rules this is structural-metadata-shaped material, not dialogue.

## Gate

`POSTCODE_FRAMING_PARTIAL` — returned by the probe for all three archives.

What this adds beyond H-NEX-003V: the post-code section is classified as a
dense interleaved serialization with identifier-style strings, no fixed
header, no boundary-aligned length-prefixed string framing, and a stable
cross-version `0x04` delimiter/tag candidate. The official sizek/sizep
walk remains unjustified.

Still NOT evidenced: the exact segment grammar, which tag values mean
string vs number vs nested record, constant/proto section boundaries,
anything about opcode semantics.

## Next justified step

1. **0x04-split segment analysis**: split tails on `0x04`; measure the
   fraction of segments that are pure printable identifiers; test whether
   inter-segment gaps follow a recurring tag/length grammar (tag frequency
   and positional bigrams), turning the delimiter candidate into a
   deterministic segmentation rule.
2. If segmentation succeeds, locate nested-proto markers within the
   segmented stream (re-opening the proto-tree traversal blocked since
   H-NEX-003R).
3. Carried from H-NEX-003V: bidirectional jump family
   (0x5C/0x5D/0xDC) target-landing analysis.

## Reproduction

```bash
python tools/research/windows-static-archive/probe_postcode_framing.py --selftest
python tools/research/windows-static-archive/probe_postcode_framing.py E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk
python tools/research/windows-static-archive/probe_postcode_framing.py E:\yysls\yysls_fast\LocalData\Patch\LT51.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT51.mpk
python tools/research/windows-static-archive/probe_postcode_framing.py E:\yysls\yysls_fast\LocalData\Patch\LT71.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT71.mpk
```
