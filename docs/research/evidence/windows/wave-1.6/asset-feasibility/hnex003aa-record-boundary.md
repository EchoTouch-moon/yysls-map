# H-NEX-003AA — First-record boundary test (length vs terminator)

> Static, read-only verification on the local Windows archive. No decryption,
> key handling, runtime injection, client modification, or content export.
> Probe: `tools/research/windows-static-archive/probe_record_boundary.py`
> (deterministic, selftested, fail-closed per block; tail bounded by block
> size, continuation walk capped at 64 records).
> Inputs: the WIN16-AF-017..022 re-frozen file set (see hnex003v report for
> the 2026-08-28 baseline drift).

## Question

H-NEX-003Z established that the first `[varint v][v−1 payload]` unit after
`code_end` consumes in ~91% of blocks (tag 520 first_ok), but the flat walk
dies at the record-2 boundary. H-NEX-003Z-F3 showed payloads carry internal
control bytes (t < v−1 in 75.7% bare / 100% plus512). This increment tests
where record 2 actually begins:

- **B1 terminator agreement** — offset `t` of the first control byte
  (< 0x20) after the payload start, compared with `v−1` and `v`
  (`t == v−1` = official loadString length with explicit terminator).
- **B2 record-2 byte class** — classify the byte at `L1 = n+(v−1)` and
  `L2 = n+v` (control / printable / MSB-set) and try an official varint
  parse there.
- **B3 continuation walk** — restart a permissive `[varint][m−1]` walk at L1
  and L2; gate = ≥ 3 records in ≥ 30% of blocks with a parsed head varint.
- **B4 terminator restart** — when `t < v−1`, also restart the walk at
  `T0 = n+t` (the internal control byte) and `T1 = n+t+1`.

Head tags restricted to v ≤ 4096; families split at v ≥ 512 (the
0x04-continuation family). Blocks: LT31 3055, LT51 3070, LT71 2898; head
varint parsed in 898 / 916 / 828 blocks.

## Findings

### F1 — Boundary census: terminator rarely agrees with length

B1 fractions per family (LT31 / LT51 / LT71):

| family | blocks | t==v−1 | t<v−1 | t==v | t>v | none |
|---|---:|---:|---:|---:|---:|---:|
| bare | 593 / 643 / 586 | 0.221 / 0.210 / 0.227 | 0.757 / 0.762 / 0.749 | 0.002 | ≤ 0.026 | 0.000 |
| plus512 | 305 / 273 / 242 | 0.000 | **1.000** | 0.000 | 0.000 | 0.000 |

Every payload in both families contains a control byte within the
`v + 16` window (`none` = 0.000 everywhere). Only ~22% of bare tags carry a
string-shaped payload whose terminator lands exactly at `v−1`; the other ~76%
have control bytes strictly inside the nominal payload. All plus512 payloads
do. This is a quantitative boundary census, not a sample: the official
loadString length interpretation holds for a minority of records.

### F2 — Neither length convention locates a walkable record-2 stream

B2/B3 at L1 (`n+v−1`) and L2 (`n+v`):

| family | varint_ok L1 / L2 | cont ge3_frac L1 / L2 | cont median |
|---|---|---|---|
| bare | 0.825 / 0.811 (LT31); 0.782 / 0.773 (LT51); 0.817 / 0.802 (LT71) | 0.042 / 0.044; 0.044 / 0.040; 0.048 / 0.036 | 0 |
| plus512 | 0.711 / 0.705; 0.689 / 0.692; 0.678 / 0.694 | 0.062 / 0.066; 0.059 / 0.059; 0.025 / 0.054 | 0 |

Official varints parse at both candidate positions in 68–83% of blocks — the
boundary is not an alignment accident — but the permissive walk collapses to
median 0 records in every archive and family (ge3 ≤ 0.066, far below the
pre-registered 0.30 gate). The bytes after the first unit are not a
homogeneous `[varint][m−1]` record stream under either length convention.

### F3 — Terminator restarts walk one record further, then stop

B4 continuation from the internal control byte:

| family | T0 ge3_frac | T1 ge3_frac | T1 cont median |
|---|---|---|---|
| bare | 0.056 / 0.058 / 0.051 | 0.108 / 0.103 / 0.104 | 1 |
| plus512 | 0.059 / 0.059 / 0.037 | 0.079 / 0.095 / 0.037 | 1 |

Restarting AT the control byte (T0) gains nothing over L1/L2. Restarting one
byte past it (T1) yields the best continuation of any convention tested in
this chain: the median block parses exactly **one** further record before the
walk stops (ge3 up to 0.108). The internal control byte therefore behaves
like a sub-record opener that is itself consumed by the walk, but the flat
`[varint][m−1]` rule then fails at the next boundary too.

## Gate

`RESULT: RECORD_BOUNDARY_PARTIAL` in all three archives. No convention
(L1, L2, T0, T1) reaches ≥ 3 continuation records in ≥ 30% of blocks.

## Interpretation

Combined with H-NEX-003Z, the evidence is now inconsistent with any flat
record grammar of the post-code section and consistent with a **nested,
recursive TLV-style grammar**: head tags behave as type IDs, payloads carry
internal control bytes at deterministic positions, and each control byte
opens at least one further varint-led unit before a rule the flat walk does
not model takes over. The walk failing identically at level 1 (L1/L2) and at
level 2 (T1) is the signature of recursion, not of a wrong length convention.

## Next justified step

**Bounded recursive descent (H-NEX-003AB candidate)**: apply the official
varint walk recursively inside the first unit's payload (depth-capped, e.g.
4 levels), and report per-level survival (records parsed at depth d given a
walkable parent). Decisive outcomes: (a) survival decays smoothly with depth
→ nested TLV confirmed, and the tag vocabulary per level becomes the next
census; (b) survival collapses at depth 1 everywhere → the control bytes are
not record heads and the payload is a non-TLV encoding (bitfield / opcode
stream), closing the TLV direction.
