# NEX-004A / H-NEX-004A — Raw Narrative Observation Normalizer

> Task-ID: NEX-004A + H-NEX-004A · Status: **DONE** · Gate: **RAW_NORMALIZATION_PASS**
> Extractors：
> - NEX-004A 原始 pilot：commit `1eeec82`（Gate 被远端降级为 PROVENANCE_INCOMPLETE）
> - **H-NEX-004A hardened extractor（EXTRACTOR_SHA）：commit `bfd610a`**（本记录由它生成）
> Base：`research/windows-evidence-tooling`
> Precondition：H-NEX-003T = INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED（Lua VM/body research CLOSED）
> Committed tool：`tools/research/windows-static-archive/nex004a_normalizer.py`（selftest PASS）

---

## 0. 结论（一句话）

H-NEX-004A hardening 完成：schema v2、**两阶段 provenance freeze**（`bfd610a` 冻结 extractor → 干净 worktree 重生成 → 记录指向 `bfd610a`）、工具自身 UTF-8 输出 + round-trip 校验（**`江晏` 完整无损**）、byte cap（UTF-8 bytes）、taxonomy 修正、fail-closed 全部落实。4/4 记录重生成，哈希全部与 frozen ledger 吻合。

> **NEX-004A → CLOSED / RAW_NORMALIZATION_PASS**（按 H-NEX-004A Gate 条件全部满足）

## 1. 两阶段 provenance freeze

```text
Commit A  bfd610a  fix(nex004a): harden raw observation provenance and encoding
                   包含: nex004a_normalizer.py + SCHEMA-v2.md + selftests + README
                   EXTRACTOR_SHA = bfd610a

干净 worktree @ bfd610a 运行 extractor
   ↓ 生成
Commit B  （本 commit）只提交 4 条 regenerated observations + 本报告
```

每条记录：

```text
extractor_commit          = bfd610a（可 checkout 复现 extractor）
extractor_source_sha256   = <nex004a_normalizer.py 的 SHA-256>（双保险）
```

## 2. 修复清单（H1-H6 全落实）

| 项 | 修复 | 验证 |
| --- | --- | --- |
| H1 provenance | 两阶段 freeze；`extractor_commit=bfd610a` 可复现；`extractor_source_sha256` | 4/4 commit=True, src_hash=True |
| H2 UTF-8 | `--output` 工具自写 UTF-8（ensure_ascii=False, LF）；round-trip 校验 | `江晏` 在 JSON 中完整；selftest 含 CJK |
| H3 taxonomy | dq→TASK_REF / EXPANSION→REGION_REF / TextByNo→TEXT_LOOKUP_KEY / 70276→TEXT_REF 修正 | 8/8 符合证据语义 |
| H4 source v2 | `source_locator`（lossy candidate）+ `source_segments[]` + `source_reconstruction` + `source_truncated` | SEGMENTED_PARTIAL 不再伪装 exact path |
| H5 byte cap | `MAX_LOCATOR_BYTES=64` 按 UTF-8 **bytes**（helper 修剪 dangling codepoint）| ASCII/CJK/边界 regression |
| H6 fail-closed | game_version/commit 缺失 → 非零退出；mpkinfo 精确 size、entry 20B、LUAC_DATA、4/8/8 | `--game-version UNKNOWN` → exit 1 |

## 3. Pilot 结果（4/4 regenerated @ bfd610a）

| entry | source_status | source_reconstruction | 恢复的目标（pattern_kind）|
| --- | --- | --- | --- |
| LT71[1768] | SEGMENTED_PARTIAL | PRINTABLE_RUN_JOIN | dq_610900(TASK_REF)、storyline_data(SCRIPT_FAMILY)、MSD_ST(SCRIPT_FAMILY)、NodeGraphData(FIELD_KEY)、**江晏(CHARACTER_TOKEN)** |
| LT71[1631] | SEGMENTED_PARTIAL | PRINTABLE_RUN_JOIN | EXPANSION_QINGHE(REGION_REF)、TextByNo(TEXT_LOOKUP_KEY) |
| LT31[874] | **EXACT** | — | 70276(TEXT_REF) |
| LT51[1178] | SEGMENTED_PARTIAL | PRINTABLE_RUN_JOIN | （7 目标均不存在）|

- 江晏：`"raw_value": "江晏"` 完整（UTF-8），@+0x06D4，tag=6，len=7，vlen=6，FRAMED_PLAINTEXT。
- confidence：MEDIUM 仅当 framing 完全匹配（tag + len == vlen+1）。
- 全部保留 `SEMANTIC_ROLE_UNVERIFIED`。

## 4. Hash 交叉验证（frozen ledger，全部吻合）

| entry | block_sha256 |
| --- | --- |
| LT71[1768] | ✓ `3504BD0C...` |
| LT71[1631] | ✓ `D3C2930D...` |
| LT31[874] | ✓ `DA4DCE48...` |
| LT51[1178] | ✓ `8AE24367...` |

archive / mpkinfo SHA-256 亦与 ledger 一致（LT71.mpk `42C9D328...` 等）。

## 5. Gate

> **RAW_NORMALIZATION_PASS**（H-NEX-004A 条件全满足）
> - 4/4 regenerated ✓ · 全部哈希匹配 ✓ · extractor commit 可复现（bfd610a）✓
> - extractor source hash 记录 ✓ · 江晏 UTF-8 完整 ✓ · taxonomy 修正 ✓
> - 无 UNKNOWN provenance ✓ · byte cap 强制执行 ✓
> - **STRUCTURAL_NORMALIZATION_PASS 未声明**（allowlist recovery 不证明泛化发现）

## 6. 交付物

- Commit A `bfd610a`：`nex004a_normalizer.py`（v2 hardened）+ `SCHEMA-v2.md` + selftests + README。
- Commit B（本 commit）：4 条 regenerated JSON（`docs/.../nex004a-raw-observations/`）+ 本报告。
- 无 canonical 写入；Canonical v0.1 保持 FROZEN。

## 7. 下一步（待 Lead 决议）

**NEX-004B — Structural Discovery & Generalization Pilot**：脱离 8 个硬编码 TARGETS，从 5-10 个未参与构造的陌生 entry 自动发现结构 observation（framed candidate → ≤64B bounded value → classifier：`dq_\d+` / `EXPANSION_[A-Z0-9_]+` / identifier-like key / numeric text ref / short CJK token），blind validation。PASS 后才考虑 Windows+Mac 合并 → NEX-006 reconciliation → CANONICAL_CANDIDATE。
