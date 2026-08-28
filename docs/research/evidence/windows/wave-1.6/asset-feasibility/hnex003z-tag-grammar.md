# H-NEX-003Z — Tag-grammar record walk on the full block tail

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_tag_grammar.py`
> (deterministic, selftested, tail bounded by block size, ≤ 1024 records
> per walk).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Purpose

H-NEX-003Y registered two follow-ups: (1) re-run the record walk on the FULL
block remainder, because the 256-byte window was provably too short for the
512+k head-value family (v = 520 implies a 519-byte payload); (2) test the
discriminator — do v and v+512 share the same payload-shape success profile?

## Tests

Four bounded record shapes, each walked from `code_end` over the entire
block remainder:

- **S** loadString-style: v == 0 empty, else v−1 payload bytes, all printable;
- **P** permissive: v == 0 empty, else v−1 payload bytes, bounds only;
- **R** raw length: payload is v bytes (tests an off-by-one convention);
- **N** nested: `[varint tag][varint m][m payload bytes]`.

Per shape: median records, full-tail coverage fraction, stop reasons, and a
per-head-tag profile with first-record completion (`first_ok`) and full-walk
success (`full`).

Blocks used: LT31 3055, LT51 3070, LT71 2898.

## Findings

### F1 — The 256-byte window artifact is resolved for the 512+k family

Under P, first-record completion for tag 520 is **0.913–0.929** across the
three archives (LT31 131/141, LT51 110/120, LT71 95/104 blocks): the
519-byte payloads exist in the full tails. H-NEX-003Y's `payload_truncated`
dominance for that family was indeed a window artifact.

### F2 — The first `[v][payload]` unit consumes, but the stream is not homogeneous

`first_ok` under P/R is ~1.0 for every bare tag and ≥ 0.91 for the 512+k
tags. Caveat: for small v the payload (≤ 30 bytes) always fits in a
multi-KB tail, so P/R `first_ok` is weak evidence about the length itself.
The strong negative result is the full walk: **full-tail coverage ≈ 0
everywhere** (2 blocks under LT31-P, 1 each under LT51/LT71-P; median
records stays 0 because 36–44% of blocks open with non-varint text). The
bytes after the first unit do not parse as a continuation of identical
records — the record-2 boundary is the bottleneck.

### F3 — The registered discriminator answers NO: tag value predicts payload kind

First-record completion under the printable-enforcing shape S:

| head tag | LT31 | LT51 | LT71 | payload character |
|---|---:|---:|---:|---|
| 8  | 0.740 | 0.712 | 0.725 | mostly printable (string-like) |
| 17 | 0.852 | 0.738 | 0.750 | mostly printable (string-like) |
| 6  | 0.161 | 0.121 | 0.286 | mostly binary |
| 5, 7, 9, 10, 11, 13, 30 | 0.0–0.16 | 0.0–0.15 | 0.0–0.083 | binary |
| 520 / 529 / 542 | 0.0 | 0.0 | 0.0 | never fully printable |

v and v+512 do **not** share payload profiles: bare tags 8/17 carry
printable text in 71–85% of their blocks, while every 512+k payload fails
the printable check in every archive. The two families from H-NEX-003Y are
therefore not one encoding with a flag bit — they are different payload
kinds. This is the increment's main positive structure.

### F4 — Length convention and nesting

R (v bytes) vs P (v−1 bytes): no observable difference in first-record
fit; both fail the full walk identically. Shape N (nested two-varint
records) is rejected: first_ok ≤ 0.46 for all tags, full walk ≈ 0.

### F5 — Stop-reason stability

Per shape P: `varint_truncated` 1319–1357 blocks (36–44%) — tails opening
with bytes that never form a varint, matching H-NEX-003W's first-printable-
run-at-offset-0 fraction (43–46%). `payload_truncated` 1578–1718. The
two-mode texture (text-first vs varint-first tails) is stable across
archives.

### F6 — Rare full-walk controls

Blocks that walk the entire tail: LT31 P×2 + N×1, LT51 P×1 + R×1,
LT71 P×1 (≤ 0.07% each). These are candidate controls for the boundary
probe in the next increment.

## Gate

**TAG_GRAMMAR_PARTIAL** (all three archives). Pre-registered thresholds not
met by any shape. Registered questions resolved: window artifact removed
(F1); discriminator answered negatively (F3).

## Next justified step

**Record-boundary test: length vs terminator** (H-NEX-003AA candidate),
aimed at the F2 bottleneck:

1. For blocks with a parsed head varint v, locate the first control byte
   (< 0x20) after the payload start; compare its offset t with v−1 and v
   (does a terminator confirm the length?).
2. Classify the byte at the record-2 position under both conventions
   (control / printable / varint-terminal).
3. Decisive continuation test: re-start the P walk at the record-2 position
   and count records — if the stream walks from record 2, the first unit is
   a section header and the remainder is a homogeneous record stream,
   re-opening proto-tree traversal.

## Reproduction

```bash
python tools/research/windows-static-archive/probe_tag_grammar.py --selftest
python tools/research/windows-static-archive/probe_tag_grammar.py \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk
# repeat with LT51.* and LT71.*
```
