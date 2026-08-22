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
    ├── research-baseline.md      ← W-R00 Baseline Freeze
    ├── mpkinfo-structure.md      ← W-R01 MPKINFO Structural Inspection
    ├── archive-linkage.md        ← W-R03（未执行）
    ├── resource-catalog-summary.md ← W-R04（未执行）
    ├── narrative-metadata-probe.md ← W-R05（未执行）
    └── static-extraction-decision.md ← W-R06（未执行）
```

## 当前状态（第一轮）

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
| W-R05 Narrative Metadata Probe | WAITING | 未执行 |
| W-R06 Decision Packet | WAITING | 未执行 |

## 核心结论一句话

> `.mpkinfo`（version=3）是一个**结构确定、可静态解析**的资源索引（8B header + N×20B entry + 16B trailer），能稳定枚举 entry 并识别 `offset/stored_size/flags` 与 `hash`；但 `name` 字段是**片段/哈希而非完整路径**，无法从索引直接得到 quest/task/localization 等叙事资源的语义名称。
