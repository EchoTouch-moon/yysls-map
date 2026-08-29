# H-NEX-003AF — Raw concatenated loadString walk (string table)

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_string_table.py`
> (deterministic, selftested, fail-closed per block; marker scan ≤ 64 B,
> ≤ 12 candidate starts, ≤ 512 records, size ≤ 4096).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

003AE rejected the tagged constant table but confirmed 0x04/0x14 act as
string markers with loadString-shaped payloads. The last registered reading is
a **string table with no count/tag prefix**: concatenated official
`loadString` records `[varint size][size−1 bytes]`, self-delimiting. For each
block the probe walks from a bounded candidate-start set — offset 0 plus
`i+1` for every 0x04/0x14 marker `i` in the first 64 bytes — and reports the
best candidate's byte coverage and record count.

Pre-registered gate: `STRING_TABLE_CANDIDATE` if ≥ 30% of blocks reach best
coverage ≥ 0.90 and median best record count ≥ 3; else
`STRING_TABLE_PARTIAL`. Pre-registered: a collapse here is the terminal
description of the region.

## Findings

### F1 — Prefix-free concatenated loadString does NOT span the region

Best-candidate results (LT31 / LT51 / LT71):

| metric | LT31 | LT51 | LT71 |
|---|---:|---:|---:|
| best coverage median | 0.132 | 0.123 | 0.109 |
| high-coverage (≥ 0.90) fraction | 0.037 | 0.033 | 0.039 |
| best record-count median | 2 | 2 | 2 |
| offset-0 coverage median | 0.000 | 0.000 | 0.000 |
| consumed-body printable fraction | 0.415 | 0.419 | 0.419 |

`RESULT: STRING_TABLE_PARTIAL` in all three archives. Even from the best
marker-relative start, a concatenated loadString walk explains only ~11–13% of
the trailing bytes and parses a median of 2 records before failing. The
sixth full-stream model is rejected.

### F2 — Markers are confirmed as local anchors; a stable minority fully walks

Two positive signals survive the collapse:

- **marker_best_frac = 0.862–0.872**: in ~87% of blocks the best start is
  marker-derived (`i+1` after a 0x04/0x14), not offset 0. This independently
  confirms the 003AC-F2 result (0x04 successor parse 0.94–0.97) — the markers
  are real string anchors, not noise.
- **high-coverage fraction = 0.033–0.039**: a stable ~3.5% of blocks DO walk
  to near-full coverage as prefix-free concatenated strings. These are
  plausibly leaf protos whose post-code region is a pure string table.

### F3 — Offset 0 remains dead

Offset-0 coverage median is 0.000 in every archive — consistent with 003AD's
three-way census (text-led, large-varint, small-varint-then-text). The region
never opens with a parseable string size at byte 0.

## Gate

`RESULT: STRING_TABLE_PARTIAL` in all three archives.

## Interpretation — terminal description of the full-stream search

Six structural models of the post-code region are now decisively rejected on
~9,000 blocks each:

1. flat `[varint][v−1]` record stream (003Y/003Z/003AA)
2. pure recursive TLV (003AB)
3. interleaved control/record tokenizer (003AC)
4. length-prefixed framing (003AD)
5. official tagged constant table `[sizek][tag][value]` (003AE)
6. prefix-free concatenated `loadString` (003AF)

The convergent positive evidence is:
- 0x04 / 0x14 are **string markers** (0.94–0.97 successor parse; 87% of
  blocks walk best from marker+1), followed by loadString-shaped payloads;
- a bare tag vocabulary {8, 14, 17, 6, 10, …} recurs at boundaries across
  levels, never with v ≥ 512 at nested positions;
- the opening bytes split into a stable three-way census (~36% text-led,
  ~34% large-varint, ~29% small-varint-then-text);
- a stable ~3.5% minority of blocks fully walk as a pure string table.

The pattern — no single full-stream grammar fits, yet local markers and a
walkable minority are robust — indicates the region is **heterogeneous**: its
organization is block-conditional (likely proto-conditional), not a uniform
byte grammar. Top-down walking has reached its limit.

## Next justified step

**Stratify the walkable minority (H-NEX-003AG candidate)**: characterize what
distinguishes the ~3.5% high-coverage blocks from the rest — code length,
total block size, leading tag, opcode count, archive — and use them as a
clean reference grammar. Decisive: if the minority is cleanly separable on
structural features, the string-table grammar is confirmed for a proto class
and the remainder can be characterized by contrast; if not, the region's
organization is per-proto data (not recoverable by any static grammar) and
the post-code line closes with the marker census as its deliverable.
