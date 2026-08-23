# NEX-004C — Narrative-Relevant Holdout Validation

> Task-ID: NEX-004C · Status: **DONE** · Gate: **GENERALIZATION_PARTIAL**
> Base：`research/windows-evidence-tooling` · Frozen discovery engine：**`204c97f`**（R1-R5 与 observation caps 未修改）
> Commits：C0 selector+policy `158b8e2` → C1 holdout manifest `83fe095` → C2 本 commit（holdout JSON + REPORT only）

---

## 0. 结论（一句话）

按冻结政策（source family 先验 storyline_data / MSD_ST，**不使用任何 target-pattern 采样信号**）选出 12 个 unseen entries 并跑精确冻结引擎 `204c97f`。**coverage 仅 1 个 distinct specific rule family**（R5 SHORT_CJK_TERM：1 条，`赵铁` @ LT71[1068]；R1/R2/R3 为 0）。按 Gate 规则（≥2 → PASS，0-1 → PARTIAL）：

> **GENERALIZATION_PARTIAL**

## 1. Phase 0 / Commit flow

```text
C0  158b8e2  narrative_holdout_selector.py + selector-policy.md（冻结）
C1  83fe095  holdout-manifest.json（12 entries，不泄露完整 source path）
    运行 discovery_engine.py @ 204c97f（clean worktree，--commit 204c97f）
C2  （本 commit）holdout-json/ 12 条记录 + 本 REPORT
```

- 选择先验：仅 source region 中的 `storyline_data` / `MSD_ST` 子串。
- 禁止信号未使用：selector 代码中无 dq_ / EXPANSION_ / numeric / CJK / framed / 已知目标值（**SELECTOR_LEAKAGE 未发生**，已验证）。
- 排除全部历史 pilot/evidence/blind entries（manifest 与 excluded 零重叠）。

## 2. Holdout 结构与选择

| 桶 | 条目 |
| --- | --- |
| A（storyline_data, not MSD_ST）| LT31[1087], LT51[1280], LT51[1272], LT71[2471], LT71[2415], LT71[886] |
| B（MSD_ST）| LT31[1702], LT31[2382], LT31[1583], LT71[1068], LT31[659], LT71[824] |

manifest 每条仅含：archive / entry_index / entry_offset / stored_size / flags_raw / source_family / source_locator_sha256 / selection_score（**无完整路径**）。

## 3. Holdout 结果（coverage 只统计 R1/R2/R3/R5；R4 IDENTIFIER 不计）

| 样本 | n | R1 TASK_REF | R2 REGION_REF | R3 TEXT_REF | R5 SHORT_CJK |
| --- | --- | --- | --- | --- | --- |
| LT31[1087] | 8 | 0 | 0 | 0 | 0 |
| LT51[1280] | 8 | 0 | 0 | 0 | 0 |
| LT51[1272] | 8 | 0 | 0 | 0 | 0 |
| LT71[2471] | 8 | 0 | 0 | 0 | 0 |
| LT71[2415] | 8 | 0 | 0 | 0 | 0 |
| LT71[886] | 8 | 0 | 0 | 0 | 0 |
| LT31[1702] | 8 | 0 | 0 | 0 | 0 |
| LT31[2382] | 8 | 0 | 0 | 0 | 0 |
| LT31[1583] | 8 | 0 | 0 | 0 | 0 |
| LT71[1068] | 9 | 0 | 0 | 0 | **1**（`赵铁`）|
| LT31[659] | 8 | 0 | 0 | 0 | 0 |
| LT71[824] | 8 | 0 | 0 | 0 | 0 |

**Coverage：1 个 distinct specific family（R5）→ GENERALIZATION_PARTIAL。**

## 4. 验证：spec 低值是真实发现（非引擎漏检）

- 引擎与 regression 完全相同（`204c97f`），regression 在已知 pilots 上正确发现 R1/R2/R3/R5 → 引擎无 gap。
- raw scan 中 5 个 digit token 均为**子串伪影**：`200321`（来自 `_200321.lua` source 文件名）、`900740`/`1350072`（来自 `C_900740_...`/`C_1350072_...` 长标识符）、`3540024`（来自 `k_3540024.lua`）、`5628` —— 均非 standalone framed 值 → 引擎按冻结规则正确地不分类它们。
- LT71[1068] 为真实叙事脚本（source=`@hexm/client/storyline_data/.wanfa/MSD_ST/LC/LC_Room2.lua`，含 NodeGraphData / get_variables / 赵铁），引擎发现其 1 个 CJK 词条。

## 5. 关键发现（对后续有指导意义）

**source-path family 先验是叙事 payload 的弱代理**：storyline_data/MSD_ST family 下多数条目为小型代码/工具模块（923-4972B），只有少数数据脚本（如 LT71[886] 12168B、LT71[1068] 13099B）携带叙事 payload；且即使叙事脚本（LT71[1068]）也未必含 dq_/EXPANSION_ refs。blind 验证若要提高特定类命中率，需更强的**非 payload 先验**（如 size 阈值 / family 细分），或扩大 holdout 规模。

## 6. Gate

> **GENERALIZATION_PARTIAL**
> - Coverage = 1 distinct specific family（R5），满足 0-1 区间。
> - 非 NARRATIVE_GENERALIZATION_PASS（<2 families）。
> - 非 SELECTOR_LEAKAGE（先验仅 family 子串，禁止信号未使用，manifest 不泄露路径）。
> - 非 PROVENANCE_INCOMPLETE（12/12 记录 extractor_commit=204c97f + 全哈希 + source hash，无 UNKNOWN）。

## 7. 交付物

- C0 `158b8e2`：selector + 冻结政策。
- C1 `83fe095`：holdout manifest。
- C2（本 commit）：`nex004c-holdout/holdout-json/`（12 JSON）+ `REPORT.md`。
- 未修改 R1-R5 / discovery engine / observation caps；无 canonical 写入；未做 Lua VM/opcode / constant/proto ownership 工作；无语义升级。

## 8. 下一步（建议，待 Lead 决议）

1. 更强的非 payload 采样先验（如 entry size ≥ 10KB 的 storyline_data family 条目），重新做一轮 narrative-relevant holdout；或
2. 接受 PARTIAL 结论，转向 Windows+Mac 合并（NEX-006）与 CANONICAL_CANDIDATE 讨论（holdout 结果不阻塞 RAW/STRUCTURAL observations 的既有成果）。
