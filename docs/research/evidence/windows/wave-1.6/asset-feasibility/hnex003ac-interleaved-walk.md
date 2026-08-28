# H-NEX-003AC — Control-aware interleaved walk

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_interleaved_walk.py`
> (deterministic, selftested, fail-closed per block; ≤ 4096 tokens per
> block).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

H-NEX-003AB confirmed control bytes open sub-units but rejected pure
recursion (full-consumption ≈ 0 at every depth). This increment tests the
remaining grammar candidate as a **full-stream tokenizer**: at each
position, byte < 0x20 is a control token, else an official
`[varint v][v−1 payload]` record is attempted. Metrics: byte coverage,
stop-reason census, control-byte census, per-control successor parse rate,
token-type transitions, record-tag census.

Pre-registered gate: `INTERLEAVED_WALK_CANDIDATE` if median byte coverage
≥ 0.90 and ≥ 30% of blocks fully consumed. Pre-registered decisive
outcomes: coverage ≥ 0.90 confirms the interleaved grammar; coverage < 0.50
falsifies it. Blocks: LT31 3055, LT51 3070, LT71 2898.

## Findings

### F1 — Full-stream interleaved grammar falsified

| archive | coverage median | full_frac | stop reasons |
|---|---:|---:|---|
| LT31 | 0.000 | 0.001 | payload_truncated 1599, varint_truncated 1452, stream_end 4 |
| LT51 | 0.000 | 0.002 | payload_truncated 1578, varint_truncated 1486, stream_end 6 |
| LT71 | 0.000 | 0.001 | payload_truncated 1464, varint_truncated 1430, stream_end 4 |

`RESULT: INTERLEAVED_WALK_PARTIAL` everywhere; the coverage < 0.50
falsification branch of the pre-registration is hit. The walk dies at the
first token in ~98% of blocks (token-count median = 0), in two near-equal
populations: **~48% varint_truncated** — the tail opens with a run of bytes
that never terminates an official varint (matches 003W-F1: the first
printable run starts at offset 0 in 43–46% of blocks); **~50%
payload_truncated** — the head varint parses but its `v−1` payload exceeds
the whole tail.

### F2 — Framing is concentrated in very few control values

Per-control successor parse rate (record parses immediately after the
control token), LT31 / LT51 / LT71:

| control | occurrences | successor rate |
|---|---:|---:|
| 0x04 | 890 / 834 / 668 | **0.958 / 0.942 / 0.966** |
| 0x14 | 65 / 54 / 64 | 0.800 / 0.704 / 0.609 |
| 0x03 | 67 / 58 / 57 | 0.313 / 0.276 / 0.193 |
| 0x00 | 469 / 505 / 458 | 0.296 / 0.279 / 0.260 |
| 0x02 | 110 / 102 / 93 | 0.191 / 0.196 / 0.237 |
| 0x01 | 262 / 221 / 205 | 0.214 / 0.195 / 0.224 |
| 0x12 | 113 / 120 / 124 | 0.097 / 0.075 / 0.089 |
| 0x11 | 51 / 50 / 47 | 0.020 / 0.060 / 0.085 |

Only counts at token-boundary positions are included (0x04 consumed inside a
varint is not counted), so this is a framing-role census, not a byte census.
0x04 is the dominant framing candidate with the largest sample and a ~95%
successor rate in all three archives; 0x14 is a weaker second. All other
control values sit at ≤ 0.31 — chance-adjacent — and are most plausibly
payload-internal bytes reached by the walk before it died.

### F3 — Where the walk survives, alternation is the dominant texture

Transition counts (LT31): control→record 1240, record→control 1012,
control→control 749, record→record 355 (start→control 618, start→record
545). Same ordering in LT51/LT71. Record-to-record adjacency is the rarest
transition: boundaries are mediated by control bytes, consistent with 003AB.

### F4 — Boundary records reuse the bare tag vocabulary

Record tags under this walk: 8, 14, 17, 6, 10, 13, 18, 5, 30, 7 (LT31
ordering; LT51/LT71 same family, 8 leading all three). Identical to the
003AB depth-1 vocabulary; no v ≥ 512 appears at a boundary position.

## Gate

`RESULT: INTERLEAVED_WALK_PARTIAL` in all three archives.

## Interpretation

The interleaved grammar is falsified **as a full-stream tokenizer starting
at `code_end`**, but not as a local boundary mechanism: where the walk
survives, 0x04-mediated alternation and the bare tag vocabulary hold. The
open question moves to the opening bytes of the tail, which split into two
testable populations:

1. **text-led tails** (~48%): no varint terminates in the opening run —
   the section may open with raw string content, not a record head;
2. **overflow heads** (~50%): the head varint parses to a value whose
   `v−1` exceeds the tail — either a section **length field** (possibly
   counting bytes beyond this block) or a non-length garbage decode.

## Next justified step

**Head value vs tail length census (H-NEX-003AD)**: classify each parsed
head as exact / overflow / underflow relative to `len(tail) − n`, histogram
the excess/residual, and split overflows by the 003Y tag bound (v ≤ 4096 =
known tag with a short tail vs new large-value population). Decisive: if
exact + off-by-≤2 covers ≥ 50% of parsed heads, the head varint is a length
field; else it is not, and the large-value population becomes the next
census target.
