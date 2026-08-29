# H-NEX-003X — Post-code segment split on delimiter candidates

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_segment_split.py`
> (deterministic, selftested, bounded 256-byte scan window per block).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Purpose

H-NEX-003W found that 0x04 terminates 42–44% of the longest printable runs
after `code_end` in all three archives, and named it the leading
delimiter/tag candidate. This increment tests whether splitting the tail on
0x04 (alone and with the next three run terminators) yields a deterministic
segment grammar: pure-printable identifier segments, stable lengths, and
recurring tag bytes between text runs.

## Tests

Bounded delimiter hypotheses (all taken from the H-NEX-003W run-terminator
histogram, nothing else):

- **D0** = {0x04}
- **D1** = {0x04, 0x00}
- **D2** = {0x04, 0x00, 0x12, 0x09}

Per hypothesis and per block tail (first 256 bytes after `code_end`):

- **X1 segment purity**: fraction of segments that are 100% printable ASCII
  ("pure") and ≥ 90% printable with length ≥ 3 ("ident");
- **X2 segment length**: capped (≤ 32) length histogram and median;
- **X3 segment leading bytes**: for non-pure segments, first-byte histogram
  and (first, second) bigrams — tag/grammar detector;
- **X4 intra-segment bytes**: byte-value histogram of non-printable bytes
  inside non-pure segments — further delimiter detector;
- **X5 tail start**: fraction of blocks whose tail begins with a delimiter
  byte (leading-marker hypothesis).

Blocks used (same bounded selection as H-NEX-003V/W): LT31 3055 of 3061
entries, LT51 3070 of 3083, LT71 2898 of 2907.

## Findings

### F1 — The strong delimiter hypothesis is rejected

Gate threshold for SEGMENTATION_RULE_CANDIDATE was set in advance: ≥ 1000
total segments and ≥ 70% pure segments under some hypothesis. Observed:

| archive | hypothesis | segments | pure | ident | other | len median |
|---|---|---:|---:|---:|---:|---:|
| LT31 | D0 | 39236 | 0.029 | 0.102 | 0.869 | 14 |
| LT31 | D1 | 111902 | 0.098 | 0.067 | 0.835 | 3 |
| LT31 | D2 | 114975 | 0.127 | 0.069 | 0.804 | 3 |
| LT51 | D0 | 38879 | 0.029 | 0.100 | 0.870 | 14 |
| LT51 | D1 | 113035 | 0.100 | 0.066 | 0.833 | 3 |
| LT51 | D2 | 116031 | 0.131 | 0.068 | 0.801 | 3 |
| LT71 | D0 | 36626 | 0.030 | 0.100 | 0.870 | 14 |
| LT71 | D1 | 106595 | 0.101 | 0.066 | 0.833 | 3 |
| LT71 | D2 | 109562 | 0.131 | 0.068 | 0.801 | 3 |

Even the most permissive split (D2) leaves ~80% of segments non-printable;
0x04 does not delimit identifier text. All numbers agree across archives to
±0.004 — the texture is structural, not sample noise. Gate:
**SEGMENTATION_PARTIAL** for all three archives.

### F2 — Non-pure segments start with high-bit varint-terminal bytes

Under D0, the top-8 leading bytes of non-pure segments are **all** in the
MSB-set range 0x85–0x91, with near-uniform counts:

| archive | top leading bytes (byte: count) |
|---|---|
| LT31 | 8E:1641 86:1527 91:1488 85:1417 8F:1404 88:1269 90:1210 87:1204 |
| LT51 | 8E:1592 86:1558 91:1531 8F:1447 85:1330 88:1258 90:1228 87:1172 |
| LT71 | 8E:1539 91:1425 86:1413 8F:1351 85:1271 88:1179 87:1143 90:1141 |

In the official Lua 5.4 loadUnsigned varint, a byte with the MSB set is the
**terminal** byte of an integer. Segments beginning with 0x8X therefore look
like they begin at a varint tail, not at a record head — i.e. the split
points (0x04 bytes) frequently fall **inside** multi-byte varints. Candidate
observation (not yet validated): `04 8X` pairs may be two-byte varints with
value 512 + (0x8X & 0x7F), and 0x04 is a varint continuation byte rather
than a delimiter.

### F3 — Stable leading bigram families

Top (first, second) bigrams of non-pure D0 segments, all three archives:

| bigram | LT31 | LT51 | LT71 | second byte |
|---|---:|---:|---:|---|
| 83 01 | 943 | 889 | 814 | 0x01 (non-printable) |
| 8E 61 | 536 | 528 | 540 | 'a' |
| 91 61 | 439 | 518 | 456 | 'a' |
| 85 54 | 539 | 480 | 456 | 'T' |
| 82 01 | 501 | 503 | 462 | 0x01 |
| 88 72 | 454 | 436 | 410 | 'r' |
| 86 63 | — | 461 | 415 | 'c' |
| 86 41 | 448 | — | 395 | 'A' |
| 84 01 | 446 | 434 | — | 0x01 |

Two families: (a) terminal varint byte + printable ASCII (`8E 61`, `85 54`,
`88 72`, `86 63`, `91 61`) — consistent with loadString-style size followed
by string content; (b) small terminal varint + 0x01 (`83 01`, `82 01`,
`84 01`), the single most common bigram everywhere. The split between the
two families is a payload-shape hypothesis for the next increment, not a
confirmed grammar.

### F4 — Intra-segment small-integer spectrum

Non-printable bytes inside non-pure D0 segments (LT31; LT51/LT71 proportional):

| byte | count | note |
|---|---:|---|
| 0x00 | 80863 | dominates — padding/terminator or high-ASCII-free zone |
| 0x01 | 28624 | |
| 0x02 | 13203 | ≈ 0x01 count × 0.46 |
| 0x03 | 9035 | ≈ 0x02 count × 0.68 |
| 0x12 | 8465 | |
| 0x81 | 5367 | varint terminal, value 1 |
| 0x11 | 4637 | |
| 0x80 | 4615 | varint terminal, value 0 |

The geometric decay 0x01 > 0x02 > 0x03 and the presence of 0x80/0x81
terminals are consistent with small varint-encoded integers (counts/flags)
interleaved with text, matching the H-NEX-003W identifier-texture picture.

### F5 — Tails rarely start with a delimiter byte

X5 shares: D0 0.075–0.093, D1 0.108–0.123, D2 0.116–0.133 across the three
archives. Combined with H-NEX-003W F1 (first printable run at offset 0 in
43–46% of blocks), the tail opens directly with content in the large
majority of blocks — there is no leading section marker.

## Gate

**SEGMENTATION_PARTIAL** (all three archives). Pre-registered gate criteria
were not met by any hypothesis; the 0x04-as-delimiter interpretation is
falsified in its strong form. The falsification itself is the increment's
stable result, together with the varint-terminal leading-byte structure (F2,
F3) that replaces it as the working hypothesis.

## Next justified step

**Varint-led record walk at code_end** (H-NEX-003Y candidate): from each
segment start identified here (and from `code_end` itself), attempt a walk
of `[loadUnsigned varint v][payload]` records with two bounded payload
shapes: (a) loadString-style — v == 0 empty, else v−1 bytes; (b) small
integer/tag record — v < 32 with a bounded fixed payload. Measure the median
number of records consumed before failure per block and the share of blocks
whose walk covers the whole 256-byte window. This directly tests the F2/F3
reinterpretation of 0x04 as a varint continuation byte.

## Reproduction

```bash
python tools/research/windows-static-archive/probe_segment_split.py --selftest
python tools/research/windows-static-archive/probe_segment_split.py \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk
# repeat with LT51.* and LT71.*
```
