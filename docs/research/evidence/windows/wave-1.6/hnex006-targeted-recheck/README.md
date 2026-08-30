# H-NEX-006 — Windows targeted recheck (hnex006-targeted-recheck)

- Task-ID: `H-NEX-006-WIN`
- Branch: `research/hnex006-win-targeted`（基于 merged `codex/mvp-platform` @ `db9413428189e1a32b11af6547facb8d8e4dc0f7`）
- Handoff: `docs/execution/H-NEX-006_WINDOWS_HANDOFF.md`（content freeze `8d81422bb4bfcd0655d243ed2e1c66c36fdaaad9` 已确认为 HEAD 祖先）

## 当前状态：`REVIEW_REQUIRED` — Phase 0 Gate `BASELINE_DRIFT`

2026-08-30 的 Phase 0 baseline preflight 判定当前游戏安装目录已偏离冻结快照
`20260829165912`。按交接包 §3，全部 7 个旧 locator 任务停止，任何旧
entry index / negative result 不得继续使用。详见 [run-manifest.md](run-manifest.md)
与 [results/phase-0-preflight.md](results/phase-0-preflight.md)。

七个 `WIN-HNEX006-*` job 均未开始，`results/` 下暂无其结果文件。

## 恢复条件（由 Mac Lead 决定）

1. 游戏安装恢复到可对应冻结快照的状态，或明确接受新快照；
2. 若接受新快照：按 frozen engine + policy 重建 nex004b/nex004c records 与
   NEX-005 packet，由 Mac 复审新 snapshot 与全部旧 `NONE`/negative 结论；
3. 新基线通过后再重启本目录的七个 job。

## 边界声明

本目录仅包含只读静态检查产生的 bounded observation 与结论；不含原始资产、
完整对白或脚本。Windows 未修改 canonical/schema/产品 UI，未触碰
`content/`、`schemas/`、`apps/`、`packages/`、`public/`。
