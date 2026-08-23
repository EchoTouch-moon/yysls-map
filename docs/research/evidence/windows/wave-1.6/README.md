# Windows Static Archive Research — Wave 1.6

> Owner: Windows Research Station · Direction: `docs/execution/WAVE_1_6_WINDOWS_STATIC_ARCHIVE_TASKS.md`
> 边界：static-only、read-only。不解密、不注入、不反作弊、不改客户端。
> 本目录是研究结论（可提交 Git）；原始 `.mpk` / `.mpkinfo` / 全量 hex dump 不进 Git（存于 `tools/research/windows-static-archive/samples/`，gitignored）。

## 目录

```text
docs/research/evidence/windows/wave-1.6/
├── README.md
├── evidence-ledger.csv
└── asset-feasibility/
    ├── research-baseline.md              ← W-R00 Baseline Freeze
    ├── mpkinfo-structure.md              ← W-R01 MPKINFO Structural Inspection
    ├── archive-linkage.md                ← W-R03 Index→Archive Linkage
    ├── block-container-classification.md ← W-R03.5 Block & Container Classification
    ├── resource-catalog-summary.md       ← W-R04 Archive Candidate Discovery
    ├── narrative-metadata-probe.md       ← W-R05 Narrative Metadata Schema Probe
    ├── static-extraction-decision.md     ← W-R06 Static Extraction Decision
    ├── luat-dialect-identification.md    ← NEX-002 LuaT Dialect Identification
    └── nex003-minimal-proto-reader.md    ← NEX-003 Minimal Lua 5.4 Proto/Constant Reader
    └── hnex003-varint-proto-reparse.md   ← H-NEX-003 Varint/Proto Reparse
    └── hnex003r-official-varint-walk.md  ← H-NEX-003R Official Lua 5.4 Varint/Proto Walk
    └── hnex003s-proto-boundary-validation.md ← H-NEX-003S Proto Boundary & Post-Code Validation
    └── hnex003t-lt31-framing.md ← H-NEX-003T LT31 Instruction Framing & Sizecode Boundary
    └── nex004a-raw-normalizer.md ← NEX-004A Raw Narrative Observation Normalizer
    └── nex004a-raw-observations/ ← 4 条 RawNarrativeObservation 记录（JSON）
```

## 当前状态（R00→R06 已闭环）

| Task | Status | Gate |
| --- | --- | --- |
| W-R00 Baseline Freeze | DONE | — |
| W-R01 MPKINFO Structural Inspection | DONE | R1 = **PASS** |
| W-R02 Deterministic Index Parser | DONE | R2 = **PASS** |
| W-R03 Index→Archive Linkage | DONE | **STATIC_EXTRACTION_PARTIAL** |
| W-R03.5 Block & Container Classification | DONE | **CONTENT_CLASSIFICATION_READY** |
| W-R04 Archive Candidate Discovery | DONE | **NARRATIVE_CANDIDATES_FOUND** |
| W-R05 Narrative Metadata Schema Probe | DONE | **R5_SCHEMA_AND_JOIN_FOUND** |
| W-R06 Static Extraction Decision | DONE | **MINIMAL_EXTRACTOR_GO** |
| J-02R Lead Asset Research Decision | **CLOSED** | **MINIMAL_EXTRACTOR_GO** |

## 核心结论

`.mpkinfo`（version=3）是**结构确定、可静态解析**的资源索引；通过「index → absolute offset → LZMA/raw block → `LuaT` 容器 → 编译后 Lua」的静态链路，`LT*.mpk` 中**确实存在可确定性定位的剧情结构信息**（`EXPANSION_QINGHE` / `storyline_data` / `MSD_ST` / `NodeGraphData` / `dq_610900` / `TextByNo` / 江晏 / 清河），且 stable ref 可跨 entry 重现。

> 保护/加密相关结论仅为 **NOT_OBSERVED_IN_TESTED_SCOPE**：只在已测试样本范围内未观察到，不据此推断所有 archive 无保护。

> 里程碑已提交并推送：`research/windows-evidence-tooling` @ `4ce57e2`（研究证据 + 脚本）与 `34bc72a`（NEX-001）。
