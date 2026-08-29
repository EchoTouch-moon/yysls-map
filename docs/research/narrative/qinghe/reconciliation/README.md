# NEX-006 reconciliation index

> Task-ID: NEX-006 · Scope: Native Evidence × Narrative Research Reconciliation
>
> Status: READY_FOR_REVIEW（local only；未 push / 未开 PR / 未 merge）
>
> Canonical: **FROZEN — no write, no promotion**

## 1. 输入与提交

| role | ref / commit | locator |
| --- | --- | --- |
| base / starting HEAD | `3c99afe530c277a72243c1bf89cf913719faffb9` | merged PR #1, `origin/codex/mvp-platform` |
| Mac narrative input head | `cd50bd24779fd47b808bc270a12c617cd9977be9` | read-only `origin/research/wave-1.6-mac-narrative` |
| Windows packet builder | `6c47256be6f42b33826341bf217469be03d4c7ab` | packet/manifest `builder_commit` |
| Windows extractor | `204c97f0d1a6039860f49a9c4b9232c51ae8d8fa` | packet/manifest `extractor_commit` |
| Windows game version | `20260829165912` | packet/manifest `game_version` |

Mac 输入相对 base 的审计结果：只新增 `docs/research/narrative/qinghe/` 下 7 个 Markdown 文件，
共 532 行；没有 canonical、schema、UI 或代码差异。本分支选择性纳入这 7 份研究输入，未做
wholesale merge/cherry-pick。父级 `README.md` 仅追加 NEX-006 索引；`hidden-story-inventory.md`
仅清理一处空白行的 trailing spaces；其余 5 份研究正文与 Mac input SHA 逐字节一致，原研究结论保持不变。

## 2. 关键文件 identity

下表 SHA-256 对应输入 commit / 当前冻结文件内容；可作为复审 locator。

| file | SHA-256 |
| --- | --- |
| Mac input `README.md` @ `cd50bd2` | `8777b06d5e242bc57bd26ae56cba5343f7e17142b40e30134e3cfce557a60900` |
| Mac input `source-ledger.md` | `e390756eb0022dffbc5877d95433661abbea6942553b7ac1746c55b118ac56a8` |
| Mac input `main-story-inventory.md` | `560b498c81d90b444578a99ee75c036bfb8b2915376a56cdd05be92184df26ec` |
| Mac input `hidden-story-inventory.md` | `e70150adfd94da9d3ddfdfe98080ec6bbf7649e9c70edad87e81d3de9a3ee4e0` |
| Mac input `unresolved-questions.md` | `9356def3d9bdc390f4bdbc29fff2a69669d67e3a07273b5195fa71cf1c6a9629` |
| Mac input `character-aliases.md` | `3f9c7d0e22854073ccfe0adbe1d248e0bfcfabb2ad5edaf152594c873a7465aa` |
| Mac input `interpretation/part-1-you-jian-xin-lai-yan.md` | `e01b51fbccafd2d301da3fa50993b1270f7c58756f25fd21cafd890967fa0cc8` |
| [Windows evidence packet](../../../evidence/windows/wave-1.6/nex005-qinghe-packet/out/qinghe-evidence-packet.json) | `8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7` |
| [Windows selection manifest](../../../evidence/windows/wave-1.6/nex005-qinghe-packet/out/selection-manifest.json) | `4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c` |
| [canonical v0.1](../../../../../content/yysls-qinghe-canonical-v0.1.json) | `4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec` |
| [canonical inventory](../../../qinghe-canonical-story-inventory.md) | `c9314c9a8ed6e21ff6228ecc77b479a881a7c3d6080dd033fb110bfde487d53b` |
| [current-to-canonical mapping](../../../qinghe-current-to-canonical-mapping.md) | `6034d1b5bc44363a83c354d1a49917d16a2aa8421244c46b2179ba6d810f1fa6` |

## 3. 交付物

- [qinghe-part1-evidence-map.md](qinghe-part1-evidence-map.md)：10 条原子 claim、四态统计、7-cluster 完整去向、evidence-role 能力边界。
- [windows-followup-evidence-list.md](windows-followup-evidence-list.md)：按 P0/P1 排序的定向补证任务，逐项写明输入、成功/失败判据与人工 fallback 门。
- [mac-validation-report.md](mac-validation-report.md)：H-NEX-006 Mac 确定性检查与公开来源 replay，明确 Mac scope 已穷尽及 Windows native evidence 边界。
- [Windows handoff](../../../../execution/H-NEX-006_WINDOWS_HANDOFF.md)：可直接交给 Windows 的 baseline gate、依赖图、7-job 执行约束与回传契约。

## 4. 冻结与解释规则

- `source_locator` 只证明字节中出现了候选路径；路径名里的 `qinghe` / `end_task` / `boss_fight` 不等于剧情含义。
- `IDENTIFIER_TOKEN_CANDIDATE`、`SHORT_CJK_TERM_CANDIDATE`、numeric `TEXT_REF_CANDIDATE` 与 cluster 邻近关系均不直接构成语义证明。
- 多个公开页面若同 lineage，不计独立 corroboration；来源多数一致不能消除 native/gameplay 冲突。
- `EXTRACTED` 不等于 `CANONICAL VERIFIED`。本轮没有修改 canonical JSON、schema、UI/CSS，也没有提交原始资产、完整对白或脚本。

## 5. Verification evidence

- Repo JSON parse: `47/47 PASS` (`jq empty`)。
- Reconciliation local Markdown links: `33/33 PASS`；claim 中全部 canonical keys 可在 canonical v0.1 解析。
- Packet refs: 全部引用 archive/entry 与 18 个 representative observations 可在 packet 解析；7 个 cluster IDs 逐项覆盖。
- Status rows: `10/10 PASS`；`SUPPORTED=0`, `PARTIALLY_SUPPORTED=5`, `CONFLICT=1`, `UNRESOLVED=4`。
- Follow-up schema: `7/7 PASS`；每项均有 target、required evidence、candidate surface、success/failure criterion、manual fallback。
- Canonical freeze: SHA-256 仍为 `4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec`，相对 base `git diff` 为空。
- Repository gate: `npm run verify` exit `0`；lint PASS，typecheck PASS，web tests `47/47`，API tests `59 passed / 19 skipped`，web/api-client build PASS。环境安装时 Node `23.11.0` 对项目声明的 Node `>=24 <25` 产生 engine warning，但实际 gate 完整通过。
