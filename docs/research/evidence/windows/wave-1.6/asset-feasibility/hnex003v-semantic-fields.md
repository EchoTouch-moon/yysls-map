# H-NEX-003V — Semantic field validation of the bytewise 4-byte record layout

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or dialogue export.
> Probe: `tools/research/windows-static-archive/probe_semantic_fields.py`
> (deterministic, selftested, fail-closed per block).

## Input provenance — BASELINE DRIFT DETECTED

Before running the probe, the ledger hashes (WIN16-AF-011..016) were
re-checked: the launcher rewrote all three Patch files at
**2026-08-28T23:05 local** (all six mtimes within one 16-second window),
before this probe ran. Counts and SHA-256 no longer match the frozen
baseline:

| file | ledger count/sha (old) | current count | current sha256 |
|---|---|---:|---|
| LT71.mpkinfo | 2862 / F5F8F157… | 2907 | 7FE5B684… |
| LT51.mpkinfo | 3034 / 65A53CC… | 3083 | 013B6B83… |
| LT31.mpkinfo | 3004 / 4AE32CE… | 3061 | 2D07B957… |

Re-freeze recorded as ledger entries **WIN16-AF-017..022**. All statistics
below correspond to the post-update file set; H-NEX-003U counts
(3004/3030/2861 valid-marker blocks) correspond to the pre-update set and
are not directly comparable. Entry indices are not stable across updates:
LT31 entry[874] now has offset=718083, sizecode=227, while ledger block
WIN16-R05-004 recorded offset=1996455 for the same index pre-update.

## Tests

Five bounded, model-free validations of the `[opcode:1][A:1][B:1][C:1]`
candidate (H-NEX-003U), aggregated over every bounded LuaT block per archive:

- **T1 register-bound**: fraction of records with an operand byte below the
  proto `maxstacksize` (B/C also MSB-masked).
- **T2 MSB flags**: fraction of operand bytes with bit 7 set.
- **T3 bigram coupling**: successor distribution per opcode byte; an
  EXTRAARG-like relation would appear as P(next|prev) ≈ 1 with count ≥ 5.
- **T4 jump plausibility**: per opcode byte, interpret B|C<<8 as a signed
  16-bit (and C as signed byte) relative offset; compare the in-range rate
  against a closed-form uniform baseline; plus sign distribution
  (negative/zero/positive offsets).
- **T5 post-code framing**: remainder size buckets after `code_end`,
  first-byte histogram, official-varint decodability, bounded `0x80 0x80`
  marker scan.

Block selection: Lua 5.4 signature + version 0x54 + bounded `0x80 0x80`
proto marker + plausible np/iv/ms + bounded sizecode (fail-closed rejects
are counted, never guessed).

| archive | entries | LuaT blocks used | rejected/non-LuaT | records |
|---|---:|---:|---:|---:|
| LT31 | 3061 | 3055 | 6 | 453,448 |
| LT51 | 3083 | 3070 | 13 | 363,364 |
| LT71 | 2907 | 2898 | 9 | 348,884 |

## Findings

### F1 — Operand positions split into two stable semantic families

T4 excess (observed in-range rate minus uniform baseline, s16
interpretation), with offset sign distribution:

| op | LT31 excess | LT51 excess | LT71 excess | neg frac | zero frac | family |
|---|---:|---:|---:|---|---|---|
| 0x5E | +0.902 | +0.906 | +0.898 | 0.004–0.010 | 0.069–0.072 | forward-dominant jump |
| 0xDE | +0.833 | +0.842 | +0.895 | 0.003–0.012 | 0.146–0.155 | forward-dominant jump |
| 0x83 | +0.638 | +0.868 | +0.875 | 0.057–0.062 | 0.039–0.057 | jump-like, small operands |
| 0x03 | +0.560 | +0.723 | +0.739 | 0.068–0.085 | 0.095–0.130 | jump-like, small operands |
| 0xDC | +0.630 | +0.827 | +0.838 | 0.060–0.160 | 0.014–0.026 | **bidirectional jump** |
| 0x5D | +0.601 | +0.745 | +0.741 | 0.090–0.183 | 0.000–0.002 | **bidirectional jump** |
| 0x5C | +0.563 | +0.657 | n/a* | 0.124–0.189 | 0.008–0.014 | **bidirectional jump** |
| 0xDD | n/a* | +0.651 | +0.730 | 0.066–0.103 | 0.004–0.008 | **bidirectional jump** |
| 0x9F | n/a* | n/a* | +0.664 | 0.092 | 0.005 | bidirectional jump (LT71) |
| 0x60 | +0.753 | +0.798 | +0.784 | 0.028–0.042 | **0.753–0.798** | index/count-like |
| 0x8C | +0.706 | +0.758 | +0.754 | 0.019–0.048 | **0.707–0.756** | index/count-like |
| 0x1D | +0.684 | +0.736 | +0.726 | 0.038–0.073 | **0.555–0.607** | index/count-like |
| 0x0C | +0.621 | +0.671 | n/a* | 0.045–0.076 | **0.590–0.657** | index/count-like |
| 0x61 | +0.597 | n/a* | +0.616 | 0.026–0.039 | **0.585–0.602** | index/count-like |

\* below the count≥20 threshold or outside top-12 in that archive.

Key evidence:

- The **bidirectional family** (0x5C/0x5D/0xDC, plus 0xDD in LT51/LT71 and
  0x9F in LT71) shows 7–19% strictly negative offsets and ≈ 0% zero
  offsets. Unsigned indices cannot be negative, so these operands behave
  like relative displacements — the strongest jump-operand evidence so far.
- The **index/count-like family** (0x60/0x8C/0x1D/0x0C/0x61) shows
  55–80% zero operands and almost no negatives: operands are small
  non-negative values, consistent with indices/counts, not jumps.
- The family split is **stable across all three archive versions**,
  including opcodes shared by all three. Position semantics in the
  `[opcode,A,B,C]` layout are therefore not random per block; they are
  opcode-conditioned and version-stable.

### F2 — No EXTRAARG-like strict coupling (negative result)

T3 found zero bigram pairs with count ≥ 5 and P(next|prev) ≥ 0.9 in any of
the three archives (≈ 1.17M records total). Standard Lua 5.4's
LOADKX→EXTRAARG / NEWTABLE→EXTRAARG serialization pattern has no analog at
this record granularity. Consistent with the custom-variant conclusions of
H-NEX-003S/T.

### F3 — Register-bound and MSB-flag tests are weakly informative

T1: A/B/C below-maxstack fractions are 0.53–0.56 / 0.52–0.55 / 0.51–0.53;
MSB-masked B/C rise modestly to 0.58–0.63. T2: MSB-set fractions are
0.18–0.23 (A) vs 0.14–0.21 (B/C). Neither test isolates a single
register-operand position; operand roles remain unresolved by these two
tests alone.

### F4 — Post-code framing is non-official and string-adjacent

T5, stable across all three archives:

- remainder after `code_end` is `>256` bytes in ~97% of blocks
  (LT31: 2964/3055; LT51: 2982/3070; LT71: 2808/2898);
- the official varint decodes at `code_end` in only ~30% of blocks;
- a `0x80 0x80` marker within +64 bytes appears in only 4/7/8 blocks;
- the first-byte histogram is dominated by ASCII-like bytes
  (`0x65 'e'`, `0x6f 'o'`, `0x61 'a'`, `0x6c 'l'`, `0x72 'r'`, `0x2e '.'`,
  `0x69 'i'`, `0x75 'u'`) plus recurring `0x04`, `0x88`, `0x00`.

The post-code region therefore does not start with an official sizek
varint; in most blocks it begins with string-like content. This confirms
and sharpens the H-NEX-003R `sizek @ code_end` failure: the constant/proto
section uses a custom framing whose first visible payload is text-like.

## Gate

`SEMANTIC_FIELD_VALIDATION_PARTIAL` — returned by the probe for all three
archives.

What this adds beyond H-NEX-003U: the layout candidate now carries
opcode-conditioned, cross-version-stable operand evidence — a bidirectional
relative-displacement family (jump-like), a small non-negative family
(index/count-like), and a negative result ruling out strict EXTRAARG-style
coupling. Post-code framing is localized to `code_end` with string-like
first bytes.

Still NOT evidenced (ceiling unchanged): opcode identities, operand widths
per opcode, control-flow graph, constant/proto ownership, any Lua VM
reconstruction, any quest-graph claim.

## Next justified step

1. **Bidirectional-family target resolution**: for 0x5C/0x5D/0xDC, check
   whether `i + 1 + s16` lands on record-anchored structural features
   (e.g. specific opcode bytes or record patterns) more often than the
   already-high in-range baseline predicts; and whether backward targets
   preferentially precede forward-jump family records (loop-shape test).
2. **Post-code string framing classifier**: bounded scan from `code_end`
   for length-prefixed vs sentinel-terminated string runs; candidate
   section boundaries via recurring byte patterns; validate against the
   recurring first-byte set.
3. **Index/count family range check**: whether 0x60/0x8C/0x1D/0x0C/0x61
   operand maxima correlate with per-block section sizes (constant count
   vs proto count candidates).

## Reproduction

```bash
python tools/research/windows-static-archive/probe_semantic_fields.py --selftest
python tools/research/windows-static-archive/probe_semantic_fields.py E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk
python tools/research/windows-static-archive/probe_semantic_fields.py E:\yysls\yysls_fast\LocalData\Patch\LT51.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT51.mpk
python tools/research/windows-static-archive/probe_semantic_fields.py E:\yysls\yysls_fast\LocalData\Patch\LT71.mpkinfo E:\yysls\yysls_fast\LocalData\Patch\LT71.mpk
```
