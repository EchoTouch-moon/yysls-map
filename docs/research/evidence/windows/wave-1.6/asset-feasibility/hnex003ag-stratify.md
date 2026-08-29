# H-NEX-003AG — Stratification of the walkable minority

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_stratify.py`
> (deterministic, selftested, fail-closed per block; marker scan ≤ 64 B,
> threshold rules at 20 sampled quantiles per numeric feature).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

003AF found a stable ~3.5% of blocks whose post-code tail walks to ≥ 0.90
coverage as prefix-free concatenated loadString records. This increment tests
whether that minority is a recognizable proto class: HIGH (coverage ≥ 0.90)
vs LOW, compared on bounded structural features (code instruction count,
block size, tail length, first-marker offsets, head-varint family, first-byte
class), with single-rule threshold/equality scans and precision/recall per
rule.

Pre-registered gate: `STRATIFICATION_CANDIDATE` if some single rule reaches
precision ≥ 0.70 and recall ≥ 0.50 with ≥ 30 HIGH blocks; else
`STRATIFICATION_PARTIAL`. Pre-registered decisive outcomes: cleanly separable
→ string-table grammar confirmed for a proto class; inseparable → per-proto
organization, line closes with the marker census as its deliverable.

## Findings

### F1 — The HIGH class reproduces; it is enriched ~5× among small protos

| archive | blocks | HIGH | HIGH frac | best rule | precision | recall |
|---|---:|---:|---:|---|---:|---:|
| LT31 | 3055 | 112 | 0.037 | block_size ≤ 862 | 0.193 | 0.527 |
| LT51 | 3070 | 100 | 0.033 | tail_len ≤ 664 | 0.179 | 0.550 |
| LT71 | 2898 | 112 | 0.039 | block_size ≤ 869 | 0.216 | 0.562 |

Within the best-rule population, ~19–22% of blocks are HIGH — about **5× the
3.3–3.9% base rate**. The enrichment is real and stable across archives.

### F2 — HIGH blocks are small, but distributions overlap almost completely

Feature medians (HIGH / LOW), LT31 / LT51 / LT71:

| feature | LT31 | LT51 | LT71 |
|---|---|---|---|
| instrs | 24 / 70 | 25 / 69 | 23 / 71 |
| block_size | 849 / 2232 | 859 / 2314 | 851 / 2264 |
| tail_len | 640 / 1697 | 653 / 1744 | 638 / 1745 |
| first_04 | 8 / 7 | 8 / 7 | 8 / 7 |

HIGH blocks carry ~3× fewer instructions and ~2.6× shorter tails. But the
best single-rule precision is only **0.18–0.22**, far below the 0.70 gate:
~80% of small blocks are still LOW. `head_family` shifts (HIGH: none+small
74–83% vs LOW none+big 71–72%) without separating; first-marker offsets are
identical across classes (no discrimination).

## Gate

`RESULT: STRATIFICATION_PARTIAL` in all three archives. The pre-registered
inseparable branch is hit.

## Interpretation — closure of the post-code grammar line

The walkable minority is "small protos, enriched ~5×", **not** a distinct,
recognizable proto class. With six full-stream grammars rejected (003Y–003AF)
and the minority now shown inseparable on structure (003AG), the
pre-registered terminal conclusion holds: the post-code region's organization
is **per-proto/per-block**, not recoverable by any single static byte
grammar. The line closes with its positive deliverables:

1. **0x04 / 0x14 are string anchors** — loadString-shaped payloads follow
   them (successor parse 0.94–0.97; best walk start at marker+1 in 87% of
   blocks);
2. **bare tag vocabulary {8, 14, 17, 6, 10, …}** recurs at boundaries across
   levels; the 512+k family (0x04 as varint continuation byte) is top-level
   only;
3. **stable three-way opening census** (~36% text-led, ~34% large-varint,
   ~29% small-varint-then-text);
4. **~3.5% of blocks are fully walkable string tables**, concentrated 5×
   among small protos.

## Next justified direction (outside this line)

The grammar line is closed; two evidence-compatible directions remain open
for future authorization:

- **Nested-proto scan**: test whether tails contain additional serialized
  function bodies (signature or header-variant search within tails) — the
  003AB nesting evidence is compatible with inline child protos, which would
  re-open traversal per child rather than per byte grammar;
- **Marker-census deliverable**: package the 0x04/0x14 anchor statistics as a
  frozen evidence artifact (no content export), usable as the static basis
  for any later authorized extraction work.
