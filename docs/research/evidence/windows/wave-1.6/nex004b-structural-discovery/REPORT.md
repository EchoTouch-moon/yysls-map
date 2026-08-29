# NEX-004B — Structural Discovery & Generalization Pilot

> Task-ID: NEX-004B · Status: **DONE** · Gate: **GENERALIZATION_PARTIAL**
> Base：`research/windows-evidence-tooling`（rules/manifest 冻结于 `486bea6`；limits 修正 `204c97f`；本批输出由 **`204c97f`** 生成）
> Precondition：NEX-004A = CLOSED / RAW_NORMALIZATION_PASS；RawNarrativeObservation v2 frozen；Lua VM/body research CLOSED。

---

## 0. 结论（一句话）

generic discovery engine（无 TARGETS allowlist）在 **8 个陌生 blind entries 上全部产出 bounded、可追溯、低语义化的 framed structural observations**（每 entry 8 条，均为 IDENTIFIER_TOKEN_CANDIDATE），机制层面泛化成立；但 **blind set 中特定叙事类（TASK_REF/REGION_REF/TEXT_REF/SHORT_CJK）出现次数为 0**（已用 raw scan 证实不是引擎漏检，blind 样本本身不含这些 pattern 的 standalone framed 值）。Regression 在已知 pilots 上全部符合预期，且额外泛化发现非 allowlist 实例（`3700061`→TEXT_REF、`天泉`/`费亦可`/`狂澜`→SHORT_CJK）。→ **GENERALIZATION_PARTIAL**。

## 1. Phase 0 — Freeze before reveal

```text
Commit A   486bea6  discovery_engine.py + blind_manifest.json + SCHEMA-and-rules.md + selftests
                    规则 R1-R5 冻结；blind manifest 冻结（metadata-only selection，内容未查看）
Commit A2  204c97f  limits 修正：单一共享 Collector，PER_CLASS_CAP=8 / MAX_OBSERVATIONS_PER_ENTRY=32
                    作用于 combined 输出（修正前按 method 分别计数）。规则 R1-R5 与 manifest 未变。
```

Blind manifest（冻结）：LT71 ×4 = [534, 2766, 1490, 165]；LT51 ×2 = [861, 873]；LT31 ×2 = [552, 2876]。与 excluded（1768/1631/1178/874）零重叠。

## 2. Regression（4 pilots @ 204c97f）

| 期望 | 结果 |
| --- | --- |
| dq_610900 → TASK_REF_CANDIDATE | ✓（LT71[1768]，经 SOURCE_PATH_SCAN）|
| EXPANSION_QINGHE → REGION_REF_CANDIDATE | ✓（LT71[1631]）|
| 70276 → TEXT_REF_CANDIDATE | ✓（LT31[874]）|
| NodeGraphData/TextByNo → IDENTIFIER_TOKEN_CANDIDATE（允许）| ✓ |
| 江晏 → SHORT_CJK_TERM_CANDIDATE（允许）| ✓ |
| 无语义升级 | ✓（无 CHARACTER_TOKEN/FIELD_KEY generic 赋予）|

**额外泛化发现（非 allowlist 实例，纯规则命中）**：`3700061`→TEXT_REF（LT31[874]）、`天泉`/`费亦可`/`狂澜`→SHORT_CJK_TERM（LT71[1768]）、`方外地`→SHORT_CJK_TERM（LT71[1631]）。

## 3. Blind（8 entries @ 204c97f）

| entry | n | per_class_over | specific(spec) |
| --- | --- | --- | --- |
| LT71[534] | 8 | False | 0 |
| LT71[2766] | 8 | False | 0 |
| LT71[1490] | 8 | False | 0 |
| LT71[165] | 8 | False | 0 |
| LT51[861] | 8 | False | 0 |
| LT51[873] | 8 | False | 0 |
| LT31[552] | 8 | False | 0 |
| LT31[2876] | 8 | False | 0 |

- 全部 observation 为 IDENTIFIER_TOKEN_CANDIDATE（LOW confidence generic 类）。
- 每 entry 均有完整 provenance（extractor_commit=204c97f、extractor_source_sha256、block/archive/mpkinfo hashes），无 UNKNOWN。
- limits：max_locator_bytes=64（UTF-8 bytes）、per-entry 32、per-class 8 全部生效。

## 4. 验证：blind spec=0 是真实发现（非引擎漏检）

对 8 个 blind 块做 raw printable-run 扫描（R1/R2/R3/R5 模式）：
- 6/8 无任何特定模式。
- LT71[1490] 的 `302005` 与 LT31[2876] 的 `4397` 均为**更长字符串的子串**（`302005_0_0`、`cle_4397`），非 standalone framed 值 → 引擎按冻结规则正确地不分类它们。
- 结论：blind 样本本身不含特定叙事类的 standalone framed 值，spec=0 为真实结果。

## 5. Gate

> **GENERALIZATION_PARTIAL**
> - **机制泛化：PASS** —— 8/8 陌生 entry 自动产出 bounded（8/entry）、可追溯（全 provenance）、低语义化（candidate 类）的 framed structural observations，无任何硬编码 TARGETS。
> - **特定叙事类 blind 验证：UNVALIDATED** —— blind set 中 R1/R2/R3/R5 出现 0 次（raw scan 证实），特定类泛化仅由 regression（已知 pilots）确认。
> - 非 STRUCTURAL_DISCOVERY_PASS（特定叙事类未在 blind set 被观察到）。
> - 非 DISCOVERY_TOO_NOISY（输出 bounded、全部真实 framed 字符串、provenance 完整，无垃圾洪泛）。
> - 非 PROVENANCE_INCOMPLETE。

## 6. 交付物

- Commit A `486bea6`：engine + 冻结规则 + blind manifest + SCHEMA-and-rules.md + selftests。
- Commit A2 `204c97f`：limits 修正（共享 Collector）。
- Commit B（本 commit）：`nex004b-structural-discovery/blind/`（8 JSON）+ `regression/`（4 JSON）+ 本报告。
- 无 canonical 写入；Canonical v0.1 FROZEN；未做任何 Lua VM/opcode / constant/proto ownership 工作。

## 7. 下一步（建议，待 Lead 决议）

spec=0 的原因：blind 集由 metadata 随机选取，多为 utility/UI 脚本。若希望 blind 验证特定叙事类泛化，建议下一轮：
- 采样策略改为**narrative-relevant 先验**（如含 `dq_`/`EXPANSION_` 相关 source 路径或 flags 特征的 entry），或
- 扩大 blind 集规模（5-10 → 20+），提高特定类命中概率。
之后才考虑 Windows+Mac 合并 → NEX-006 → CANONICAL_CANDIDATE。
