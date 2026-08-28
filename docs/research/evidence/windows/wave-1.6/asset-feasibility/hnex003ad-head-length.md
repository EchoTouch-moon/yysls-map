# H-NEX-003AD — Head varint vs tail length census

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_head_length.py`
> (deterministic, selftested, fail-closed per block; bounded 64-byte MSB scan,
> histograms capped at 32).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

H-NEX-003AC falsified the full-stream interleaved grammar and split the
opening bytes into two populations: text-led tails (~48%, varint never
terminates) and overflow heads (~50%, `v−1` exceeds the tail). One reading of
the overflow population remained open: the head varint might be a **length
field** for the post-code section rather than a tag. This increment classifies
the relation between the head varint value `v` and the available tail length.
Recall `load_unsigned` reads at most 8 bytes and returns `None` if no MSB-set
byte appears in that window.

Classes for a parsed head (n varint bytes, tail length L, need = v−1):
**exact** (need == L−n), **overflow** (need > L−n, excess `delta`),
**underflow** (need < L−n, leftover `residual`). Overflow is split at the
003Y tag bound (v ≤ 4096 = known tag family vs v > 4096 = large-value
population).

Pre-registered gate: `HEAD_LENGTH_CANDIDATE` if exact + off-by-≤2 covers
≥ 50% of parsed-head blocks; else `HEAD_LENGTH_PARTIAL`.

## Findings

### F1 — The head varint is NOT a section length

`near_len_frac` (exact + overflow delta ≤ 2 + underflow residual ≤ 2) over
parsed-head blocks:

| archive | blocks | parsed_frac | exact | near_len_frac |
|---|---:|---:|---:|---:|
| LT31 | 3055 | 0.638 | 0 | 0.000 |
| LT51 | 3070 | 0.643 | 0 | 0.000 |
| LT71 | 2898 | 0.622 | 0 | 0.001 |

Zero blocks have `v−1` exactly matching the remaining length; essentially zero
are within 2 bytes of it. The length-field branch of the 003AC overflow
population is closed. `RESULT: HEAD_LENGTH_PARTIAL` in all three archives.

### F2 — Overflow is dominated by a large-value population, not tags

Overflow split (LT31 / LT51 / LT71):

| archive | overflow | tag-family (v≤4096) | big (v>4096) | delta mode (cap 32) |
|---|---:|---:|---:|---|
| LT31 | 1081 | 38 | 1043 | 32 ×1077 |
| LT51 | 1089 | 40 | 1049 | 32 ×1086 |
| LT71 | 1006 | 38 | 968 | 32 ×1005 |

~97% of overflows are large values (v > 4096) whose `v−1` exceeds the tail by
≥ 32 bytes (histogram saturated at the cap). These are not 003Y tags and not
lengths: the opening bytes in these blocks decode to large numbers but do not
frame the section.

### F3 — Underflow leaves a large residual; opening text runs sit just past the varint window

Underflow `residual_hist` is also saturated at the 32 cap (LT31: 859/867;
LT51: 879/885; LT71: 790/796) — where a small tag-like value parses, its
`v−1` payload consumes only a short prefix and ≥ 32 bytes remain. The
record-end byte class is mixed (LT31 control 354 / printable 370 / high 143),
not a clean boundary marker.

For the ~36% no-varint blocks, the first MSB-set byte concentrates at offset
**8, 9, 10** — just beyond the 8-byte varint reader window (LT31 top:
8×241, 9×184, 10×159). The opening run is ~8–10 low (text) bytes followed by
a high byte: a stable-width texture, not a self-delimiting length.

## Gate

`RESULT: HEAD_LENGTH_PARTIAL` in all three archives.

## Interpretation

Three full-stream models of the post-code section are now decisively rejected
on ~9,000 blocks: flat `[varint][v−1]` record stream (003Y/003Z/003AA),
pure recursive TLV (003AB), interleaved control/record tokenizer (003AC), and
length-prefixed framing (003AD). What survives is local: 0x04-mediated
boundaries with a bare tag vocabulary (003AC-F2/F4) and control-byte sub-unit
openers (003AB). The opening bytes are not self-delimiting.

This is consistent with the region being the proto's **constant / upvalue /
nested-proto tables** rather than an independent record stream: in official
Lua 5.4 those follow `code` and are organized as `[count][items]` where each
string item is `[tag][loadString]`. H-NEX-003R's `sizek @ code_end` failure
rejected only the naive "varint at offset 0 is sizek" reading, not a tagged
constant table whose first item is a string or nil. (Note: this probe's
direct census measures no-varint-at-offset-0 at ~36%, refining 003AC's ~48%
`varint_truncated` stop share, which also counted walk deaths at later
positions.)

## Next justified step

**Constant-table walk (H-NEX-003AE candidate)**: apply the official Lua 5.4
`loadConstant` grammar at `code_end` — `[varint sizek][sizek constants]`,
each constant `[tag byte][value]` with tag ∈ {nil, boolean, float, int,
short-string, long-string} and strings via official `loadString`. Report the
fraction of blocks where a bounded constant walk consumes a prefix cleanly,
the tag-value histogram, and whether it explains the 0x04/bare-tag texture.
Decisive: a stable tag histogram plus clean prefix consumption in a large
block fraction re-opens proto-tree traversal; a diffuse tag census closes the
constant-table reading too.
