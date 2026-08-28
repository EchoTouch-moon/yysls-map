# H-NEX-003AB — Bounded recursive descent into post-code payloads

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_nested_descent.py`
> (deterministic, selftested, fail-closed per block; depth cap 3, ≤ 32 units
> per stream, ≤ 256 unit visits per block).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

H-NEX-003AA ended with the flat `[varint][v−1]` walk failing identically at
level 1 (record-2 boundary) and level 2 (one byte past the first internal
control byte, median exactly 1 further record). The pre-registered test here
applies the official varint walk recursively inside record payloads:

- **D1 depth walk** — P-shape walk at depth 0 (block tail) and inside every
  record payload, depth-capped at 3. Per (depth, entry): streams visited,
  record-count median, conditional survival (`ge1_frac` = fraction of streams
  parsing ≥ 1 record), full-consumption fraction.
- **D2 entry conventions** — each record payload spawns up to two child
  streams: **E0** from the payload start; **E1** from one byte past the first
  internal control byte (< 0x20), generalizing the 003AA T1 restart from
  first records to all records at all depths.
- **D3 tag census** — per-depth top varint values (v ≤ 4096) at record heads.

Pre-registered gate: `NESTED_DESCENT_CANDIDATE` if some depth d ∈ {1, 2} and
entry convention reaches ≥ 100 child streams with `ge1_frac` ≥ 0.30.
Pre-registered decisive outcomes: (a) smooth survival decay with depth →
nested TLV confirmed; (b) collapse at depth 1 under both entries → control
bytes are not record heads, TLV direction closed.

Blocks: LT31 3055, LT51 3070, LT71 2898.

## Findings

### F1 — The child stream starts AFTER the control byte, not at byte 0

Conditional survival `ge1_frac` at depth 1 (LT31 / LT51 / LT71):

| entry | streams | ge1_frac | full_frac |
|---|---:|---:|---:|
| E0 (payload start) | 1305 / 1292 / 1178 | 0.115 / 0.094 / 0.098 | ≤ 0.002 |
| E1 (past first control byte) | 1126 / 1121 / 1007 | **0.362 / 0.376 / 0.351** | 0.015–0.020 |

E1 survives 3.1–3.9× better than E0 in every archive. The payload is not a
record stream from its first byte; the first control byte opens a sub-unit
and the parseable stream begins after it. This confirms at census scale what
003AA observed on first records only (T1 median = 1).

### F2 — Survival decays after depth 1: nesting is real but shallow

| depth / entry | streams | ge1_frac |
|---|---:|---:|
| 0 / head | 3055 / 3070 / 2898 | 0.284 / 0.288 / 0.275 |
| 1 / E1 | 1126 / 1121 / 1007 | 0.362 / 0.376 / 0.351 |
| 2 / E1 | 474 / 411 / 359 | 0.086 / 0.127 / 0.081 |
| 2 / E0 | 659 / 599 / 512 | 0.077 / 0.058 / 0.061 |
| 3 / E1 | 65 / 55 / 32 | 0.108 / 0.091 / 0.125 |

Neither pre-registered disjunct holds exactly: survival does not collapse at
depth 1 (E1 ≈ 0.36 > gate), but it also does not decay smoothly — it drops
~4× to 0.08–0.13 at depth 2 and stays there on shrinking samples. Read
honestly: **control bytes are record openers (the TLV direction is open,
003AA outcome (b) is rejected), but the grammar is not pure recursion** — a
second, non-TLV framing element must exist between units.

### F3 — Parsed runs never consume their stream

`full_frac` ≤ 0.020 at every depth and entry in every archive: even where
records parse, residual bytes remain after each run. The walk stops on bytes
the `[varint][v−1]` rule does not model — the same control bytes that E1
skips. Byte coverage, not record count, is the metric the next test must
maximize.

### F4 — Tag vocabulary is reused across depths; plus512 is top-level only

Depth-0 head tags (all archives): 8, 520, 17, 6, 7, 0, 10, 526, 529 — the
003Y two-family census. Depth-1 E1 top tags: **8, 14, 17, 34, 21, 7, 114** —
the same small-value family; **no v ≥ 512 appears at depth ≥ 1** in any top-8
list. The 512+k family (0x04 continuation byte) is a top-level phenomenon;
nested records draw from the bare tag space. Tag 8 leads both at depth 0 and
depth 1 in two of three archives.

## Gate

`RESULT: NESTED_DESCENT_CANDIDATE` in all three archives (depth-1 E1:
streams ≥ 1007 and `ge1_frac` ≥ 0.351 ≥ 0.30). First CANDIDATE-grade gate in
the post-code chain (003W–003AA all returned PARTIAL).

## Interpretation

The post-code section is a control-byte-mediated structure: payload control
bytes open sub-units whose content begins one byte later and reuses the same
tag vocabulary. Pure recursion is rejected by the depth-2 survival drop and
near-zero full-consumption everywhere; an interleaved grammar — control bytes
alternating with varint-led records — fits all four findings.

## Next justified step

**Control-aware interleaved walk (H-NEX-003AC candidate)**: a single-level
tokenizer over the tail — at each position, byte < 0x20 is a control token,
else attempt `[varint v][v−1 bytes]`; report byte coverage, per-control-value
successor parse rate, and the dominant token/record alternation pattern.
Decisive: coverage ≥ 0.90 confirms the interleaved grammar and turns the
control-byte census into a framing table; coverage < 0.50 falsifies it and
the residual bytes become the next census target.
