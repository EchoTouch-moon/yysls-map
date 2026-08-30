# H-NEX-006R — Route B Rebaseline Report

- **Task-ID**: H-NEX-006R
- **Status**: READY_FOR_REVIEW
- **Branch / base commit**: `research/hnex006-win-targeted` @ `39c3079bdfc8db8325d535c477653b40ff3b1ea2` (append-only; Phase 0 evidence and the BASELINE_DRIFT record preserved untouched)
- **Snapshot ID**: `WIN-HNEX006-20260820220319-e105e344c1a2`
- **Game Version**: `20260820220319` (patching_version.txt)
- **Input Manifest SHA-256**: `e105e344c1a2fa61b627d5bff1a3efbfc6157c0b087086633f633ef74a235eaa` (stable census manifest hash; identical in Census #1 and Census #2)

## Baseline censuses (requirement 3)

Two complete censuses of `E:/yysls/yysls_fast/LocalData/Patch`, 5+ minutes apart
(2026-08-30T02:47:16Z and 2026-08-30T02:53:01Z), after verifying no
game/launcher/updater/crash-reporter processes were running (none were; no
game file was touched).

- 764 files enumerated with path/size/mtime each census; 7 core toolchain
  inputs hashed with SHA-256 (patching_version.txt + LT31/LT51/LT71
  .mpk/.mpkinfo — exactly the files the frozen engine/builder read).
- Field-by-field comparison: **0 differences** (path sets, sizes, mtimes, all
  SHA-256). Baseline declared STABLE; `BASELINE_MUTATING` not triggered.
- Census artifacts: `census-1.json` (sha256
  `5cff53767694e36d5a5f990ce97764576de1947a9b05359b43adc9361473cc5c`),
  `census-2.json` (sha256
  `609c675ca0fe195fa5577a0b633710de0323862f638839c015ab04f106139c33`).

Core input SHA-256:

| file | sha256 |
|---|---|
| LT31.mpk | `b404de7775a7e18876bbc4da732ee997509b09eb26f4fe4affee961ba1abea87` |
| LT31.mpkinfo | `2d07b95700bc44e3e931b469c85e86b738c6da259b1b029b66f95f3ce2e5604b` |
| LT51.mpk | `808a7d85b0160e1bf7691af7869db09ad37e13213e1838aa03b4765b15301870` |
| LT51.mpkinfo | `013b6b83447536a58b4c5c17f0fa1c88acf68d8e91bbd46188c436e67cf3d603` |
| LT71.mpk | `74b0db1a3ca320fe03ef4ad5414b6e3d916c405f416ac274a018a26c988b3426` |
| LT71.mpkinfo | `ed5b2f2e648dda43e30e185f4b8f5982ccc8b7b0910b491acbf18b9c21a981f6` |
| patching_version.txt | `f7fc3e4fb5b46d78c24d40a107b90dbf9169d4ebe6ba639976d499b44be4da76` |

## Input archives

LT31.mpk / LT31.mpkinfo, LT51.mpk / LT51.mpkinfo, LT71.mpk / LT71.mpkinfo
(read-only, "rb" only), plus patching_version.txt. No other archives are read
by the frozen engine/builder (`ARCHIVES = ["LT71","LT51","LT31"]`).

## Frozen identities used

- Engine `204c97f0d1a6039860f49a9c4b9232c51ae8d8fa`, blob sha256
  `6be80797f44a818b44fc445380533e35de7e4d09b46d1800d55a846c2f681ba3`
- Builder `6c47256be6f42b33826341bf217469be03d4c7ab`, blob sha256
  `2c0112b8c01d42d35b914799a37c11d93a3752d41ae2e02a38fcb1d946261847`
- Holdout selector at the builder commit, blob sha256
  `46e336cef5b646a632bdb41df5c30676103ee18c8a5ace0b47529642ca2de5f9`
- All three worktree files verified byte-identical to these blobs
  (worktree sha == blob sha), so the frozen CLIs ran from the canonical repo
  paths and their internal identity checks (`verify_builder_identity`,
  `verify_extractor_blob`) resolved against real blob bytes. No frozen source
  was modified.

## Generated records (requirement 5)

Regenerated from scratch on the new snapshot; no old locator/record/manifest
was used as an input to selection or discovery (the selector's frozen
`EXCLUDED` constant is the only disjunction with prior evidence).

- `records/regression/` — 4/4 KNOWN entries re-run through the frozen engine
  (LT31[874], LT51[1178], LT71[1631], LT71[1768]).
- `records/holdout-manifest.json` — fresh frozen-selector output
  (schema `nex004c-holdout-manifest-2`), 6 storyline_data + 6 MSD_ST;
  sha256 `46e1c1b89fb78db09c81edf24e9e3b684fa3bbd61a73d5a4df6c3376c02e6498`.
- `records/holdout-json/` — 12/12 holdout records via the frozen engine.
- `records/blind/` — 30 records: byte-stable mirror of the frozen builder's
  own `discover_new()` output for this records dir (qinghe-source candidates
  + top-4 large family, existing-covered entries excluded BEFORE truncation).
- `records/records-manifest.json` — sha256
  `cd24744e000a7f8aeb270f65f565e00c651ffb371677fed7c0930448aea15a3e`.
- Failures: 0.

## Selection manifest + packet (NEX-005-compatible)

Produced by the frozen builder CLI (`qinghe_packet_builder.py <Patch>
--records-dir records --out packet --commit 204c97f… --builder-commit
6c47256…`), which fail-closed through `verify_builder_identity`,
`verify_identity`, `verify_provenance` (all records re-verified against the
current archive bytes), and `verify_extractor_blob`.

- `packet/selection-manifest.json` — 12 entries, sha256
  `ae961dedc166e11385b00a9187b41f9eb0b01c5a3fcaf73cc1412f28c4457a73`
- `packet/qinghe-evidence-packet.json` — 7 clusters (cap [5,8], each ≤5
  entries), sha256
  `d75cb284b15d482ef3da514720a42a00ea4b6b24e5c25bca30115bc24a5c5cdf`
- Packet is structural evidence only: no canonical facts, no dialogue/prose,
  locators capped at 64 bytes; `CANONICAL: NONE` warning carried.

## Determinism (requirement 7)

The full pipeline (records + packet) was run twice independently on the same
static snapshot into separate directories. Result: **all 50 files
byte-identical** (0 missing, 0 extra, 0 differing; records-manifest sha
`cd24744e…` identical in both runs). The frozen outputs contain no timestamp
fields, so no "declared non-semantic time fields" exist — exact byte equality
is the criterion and it holds. `NON_DETERMINISTIC_REBUILD` not triggered.

## Old-vs-New drift (requirement 5; old artifacts = diff inputs only)

`drift-matrix.json` (file sha256
`8ae5df25c383e474c6d92d110abf6ba22921e73dc32cd717cd683b9fb3890bb1`;
internal canonical `matrix_sha256`
`daefcf7fd9724d7b33ca4346f96e0d4cf7ec004a81bc308a7795ceb4e7e1fba5`).

- game_version: `20260829165912` (old) → `20260820220319` (new).
- 16 old records (4 regression + 12 holdout) are all reproducible on the new
  snapshot; **16/16 block_sha256 identical, 0 diverged**.
- Selection: same 12 entries, same order, same scores (all score 6).
- Cluster layout: identical 7 clusters with identical membership.
- Old blind set (8 records) is subsumed by discovery: 8 old-only record files
  (the prior blind naming set) vs 30 new blind records — the new blind set is
  a fresh `discover_new()` outcome on the new snapshot, not a reuse.
- Net: the archive bytes read by the toolchain did not change between
  snapshots; only the patching_version marker differs.

## Boundary check (requirements 1, 2, 6, 8)

- Writes confined to
  `docs/research/evidence/windows/wave-1.6/hnex006-rebaseline/WIN-HNEX006-20260820220319-e105e344c1a2/`
  plus three NEW read-only drivers under `tools/research/`
  (`hnex006r_census.py`, `hnex006r_records.py`, `hnex006r_drift.py`).
- No writes to `content/`, `schemas/`, `apps/`, `packages/`, `public/`,
  canonical surfaces, or Mac reconciliation docs; no overwrite of any
  nex004a/nex004b/nex004c/nex005/hnex006-targeted artifact.
- Frozen tool sources untouched (byte-verified above). No tracked file was
  rewritten to pass byte checks; global `core.autocrlf` unchanged. Git byte
  verification used blob bytes (`git show <commit>:<path>`), not worktree
  materialization, for all frozen-code identity claims.
- Game install opened read-only ("rb") throughout; no game file rolled back,
  deleted, replaced, or patched.

## Canonical diff

None. `git status` shows only the new evidence directory and the three new
driver scripts; no tracked file modified.

## Unresolved

- The patching_version marker moved **backwards**
  (`20260829165912` → `20260820220319`) while every archive byte read by the
  toolchain stayed identical. The cause (launcher channel metadata, reinstall,
  or rollback marker) is outside read-only observation; recorded as drift,
  not interpreted.
- Semantic roles remain unverified (packet carries the frozen
  `SEMANTIC_ROLE_UNVERIFIED` / `CANONICAL: NONE` posture).

## Next

Mac snapshot review of the new packet
(`packet/qinghe-evidence-packet.json`, sha256 `d75cb284…`). The seven
P0-1…P1-3 jobs remain unstarted until this snapshot/packet/deterministic
rerun passes the Mac gate.
