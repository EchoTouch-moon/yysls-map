# H-NEX-003Y — Varint-led record walk at code_end

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_varint_walk.py`
> (deterministic, selftested, bounded 256-byte scan window per block,
> ≤ 64 records per walk).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Purpose

H-NEX-003X found that non-pure segments after `code_end` start with MSB-set
bytes (0x85–0x91, varint terminal signature) and conjectured that 0x04 is a
varint continuation byte rather than a delimiter. This increment tests
whether the tail parses as a stream of `[loadUnsigned varint][payload]`
records.

## Tests

Three bounded payload shapes × nine start offsets (code_end + 0..8):

- **S** loadString-style: v == 0 empty record, else v−1 payload bytes, all
  printable ASCII;
- **P** permissive: v == 0 empty, else v−1 payload bytes, bounds only;
- **I** integer stream: record is the varint alone.

Per (shape, start): median records before failure (cap 64), fraction of
blocks whose walk consumes the whole 256-byte window, stop-reason
distribution. Separately: the varint decoded at offset +0 per block
("head value").

Blocks used: LT31 3055, LT51 3070, LT71 2898 (same bounded selection as
H-NEX-003V/W/X).

## Findings

### F1 — Naive record walks fail at or near the first record

Median records per walk is **0–1 for every (shape, start) combination** in
all three archives; full-window coverage is ~0. Stop reasons at start +0
(LT31; LT51/LT71 proportional):

| shape | payload_truncated | varint_truncated | payload_nonprintable |
|---|---:|---:|---:|
| I | — | 3052/3055 (99.9%) | — |
| P | 1825 (59.7%) | 1230 (40.3%) | — |
| S | 1493 (48.9%) | 1117 (36.6%) | 445 (14.6%) |

Two causes are conflated and cannot be separated inside a 256-byte window:
(a) ~40% of blocks begin with bytes that do not parse as a varint at all
(consistent with H-NEX-003X F5: tails usually open directly with text), and
(b) the 512+k head values below imply payloads of ≥ 512 bytes — longer than
the window itself — so `payload_truncated` for those blocks is a probe
artifact, not evidence against the grammar. Gate: **VARINT_WALK_PARTIAL**
(all three archives; pre-registered thresholds were not met).

### F2 — Head varint values form a stable two-family structure

Varint decoded at tail offset +0 (top values, count; same set in all three
archives):

| archive | top head values |
|---|---|
| LT31 | 520:141, 8:127, 6:31, 7:28, 542:28, 17:27, 13:24, 10:20, 529:18, 11:18 |
| LT51 | 520:120, 8:118, 17:42, 6:33, 10:31, 9:29, 30:24, 542:23, 5:20, 13:19 |
| LT71 | 8:120, 520:104, 17:40, 7:29, 10:24, 6:21, 5:17, 30:17, 542:17, 13:16 |

Structure:

- **small family** — one-byte terminal varints with values in {5..13, 17,
  30}; values 8 and 17 lead everywhere;
- **512+k family** — two-byte varints with continuation byte 0x04:
  520 = 512+8, 529 = 512+17, 542 = 512+30. Each k value mirrors a member of
  the small family (8, 17, 30 all also appear as bare values).

This is direct quantitative confirmation of the H-NEX-003X F2 candidate
observation: 0x04 bytes in the tail are varint continuation bytes, not
delimiters. The pairing of identical constants in bare and 0x04-prefixed
form suggests these values are **tags/type IDs** rather than string lengths
(a length grammar would not reuse the same constants across both encodings),
but that is a hypothesis for the next increment, not a validated grammar.

### F3 — Rare fully-walkable tails exist

3 blocks in LT31 (at P@+3..+8) and 1 block in LT71 parse ≥ 64 consecutive
varints within the window (`record_cap`). They are a tiny minority class
(≤ 0.1%) but prove that varint-dense tails exist; they are candidate
controls for the tag-grammar walk in the next increment.

## Gate

**VARINT_WALK_PARTIAL** (all three archives). The walk falsifies the naive
"[varint][v−1 payload] from code_end" model within the window, and delivers
a stable positive structure (the two value families, F2) that constrains the
next model.

## Next justified step

**Tag-grammar walk on the full block tail** (H-NEX-003Z candidate): rerun
the walk with the tail extended to the whole block remainder (removing the
window artifact of F1b) and with record shape `[varint tag][payload]` where
the tag value set is the union of the two families observed here. Two
bounded payload hypotheses per tag: (a) loadString-style s−1 printable
bytes; (b) a second varint followed by that many bytes. Discriminator: do v
and v+512 share the same payload-shape success profile? Also inspect the
≤ 0.1% fully-walkable blocks (F3) as controls.

## Reproduction

```bash
python tools/research/windows-static-archive/probe_varint_walk.py --selftest
python tools/research/windows-static-archive/probe_varint_walk.py \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpkinfo \
    E:\yysls\yysls_fast\LocalData\Patch\LT31.mpk
# repeat with LT51.* and LT71.*
```
