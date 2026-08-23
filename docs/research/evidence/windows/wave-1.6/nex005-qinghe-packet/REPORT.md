# NEX-005 / H-NEX-005 — Qinghe Structural Evidence Packet

> Task-ID: NEX-005 + H-NEX-005 · Status: **DONE** · Gate: **QINGHE_EVIDENCE_PACKET_PASS**
> Base：`research/windows-evidence-tooling` · Frozen observation engine：**`204c97f`**
> Builder（P0 系列 + H0）：`5d5986e → fa594bd → 2f96d59 → 11f1a77 → 9c0f72d → 1464a17 → 3159afd`
> **最终 builder_commit = `3159afd`**（H-NEX-005 hardening 后）
> Commits：P0 冻结 builder+policy → **H0 `3159afd` 冻结 hardened builder** → H1 本 commit（manifest + packet + REPORT only）

---

## 0. 结论（一句话）

使用冻结 engine `204c97f` 与冻结选择政策，构建了 **12 entries / 8 evidence clusters**（全部 ≤5 entries/cluster）的 Qinghe native structural evidence packet。**H-NEX-005 硬化后**：provenance identity 彻底分离（`builder_commit/builder_source_sha256` vs `extractor_commit/extractor_source_sha256`，后者从输入 records 继承并 fail-closed 校验），UTF-8 byte cap 生效，**与上一版 packet 零 ARTIFACT_DRIFT**（同 12 entries、同 8 cluster 成员、同 structural observations、同 block hashes）。

> **QINGHE_EVIDENCE_PACKET_PASS**

## 1. 两阶段 freeze / commit flow

```text
P0   5d5986e   qinghe_packet_builder.py + packet-policy.md（冻结政策）
P0'  fa594bd   records-dir 可重复（加载 regression/ + holdout-json/）
P0'' 2f96d59   新候选 engine runs 收敛到政策池（qinghe 全部 + 大文件 top-4）
P0'''11f1a77   §3a 聚类 caps（sub-split / fallback / merge）
P0''''9c0f72d  SELECT_N=12 + 清洗 sub-split key + merge 修复
H0   1464a17    provenance identity 分离（builder vs extractor）+ selftest
H0'  3159afd    identity unpacking 修复（最终 builder，selftest PASS）
     （以上均为 pre-run 修正，packet 产出前完成；policy 语义未变）
clean run @ 3159afd
H1   （本 commit）selection-manifest.json + qinghe-evidence-packet.json + REPORT only
```

## 2. H-NEX-005 hardening 清单

| 项 | 修复 | 验证 |
| --- | --- | --- |
| H1 provenance identity | `builder_source_sha256 = SHA256(builder.py)`；`extractor_commit/extractor_source_sha256` 从输入 records 继承；强制所有 selected records 同一 `extractor_commit == 204c97f`、同一 `extractor_source_sha256`，否则 FAIL CLOSED | ✓ 分离成功（两 hash 不同）、consistency check PASS |
| H2 per-entry consistency | 每 entry 的 archive/index/block_sha256 直接取自 source record（不做聚合信任）；archive ∈ {LT71,LT51,LT31}、block_sha256 长度校验 | ✓ |
| H3 byte cap | `source_locator` 用 UTF-8-safe byte cap（复用 NEX-004A helper），输出 `source_truncated` | ✓（全部 ASCII 路径无截断，字段存在）|
| H4 policy cleanup | §6「选中 16」→「选中 12」；§5 provenance 段更新 | ✓ |

## 3. 选择（12 entries，与上一版完全一致 —— 零 drift）

| entry | score | 主要 selection reasons |
| --- | --- | --- |
| LT71[1768] | 9 | dq_610900 TASK_REF、NodeGraphData、江晏/天泉/费亦可、MSD_ST、≥8KB |
| LT71[1631] | 7 | EXPANSION_QINGHE、方外地、≥8KB |
| LT71[1068] | 6 | NodeGraphData、赵铁、MSD_ST、≥8KB |
| 9 个 qinghe source 条目 | 6 | qinghe source 信号 + NodeGraphData |

## 4. Evidence clusters（8 clusters，全部 ≤5 entries，与上一版一致）

| cluster_id | n | 内容 |
| --- | --- | --- |
| QH_EXPANSION | 1 | LT71[1631]：EXPANSION_QINGHE + 2 specific obs |
| QH_SOURCE/guanqia/qinghe_end_task | 5 | 清河终章任务脚本族 |
| QH_SOURCE/guanqia/qinghe_end_boss_fight | 1 | LT71[1886] |
| QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx | 1 | LT51[2194] |
| QH_SOURCE/task | 1 | LT51[1909]：qinghefenwei |
| QH_SOURCE/task/lizehao | 1 | LT31[954]：qinghejianzhang |
| TASK_DQ | 1 | LT71[1768]：dq_610900 |
| NODE_GRAPH | 1 | LT71[1068]：赵铁 |

## 5. Provenance（hardened）

```text
builder_commit        = 3159afd（可 checkout 复现 builder）
builder_source_sha256 = SHA256(qinghe_packet_builder.py @ 3159afd)
extractor_commit      = 204c97f（从输入 records 校验一致）
extractor_source_sha256 = SHA256(discovery_engine.py @ 204c97f)（从输入 records 校验一致）
game_version          = 20260820220319
per-entry             = archive / entry_index / entry_offset / stored_size / block_sha256
```

## 6. Gate

> **QINGHE_EVIDENCE_PACKET_PASS**（H-NEX-005 条件全满足）
> - same 12 selected entries ✓ · same 8 cluster memberships ✓
> - same structural observations ✓ · same block hashes ✓（**ARTIFACT_DRIFT 检查 = False 差异**）
> - builder_commit resolvable ✓ · builder_source_sha256 correct ✓
> - extractor_commit = 204c97f ✓ · extractor_source_sha256 correct + 跨输入一致 ✓
> - UTF-8 byte cap enforced ✓ · 零 canonical 写入 ✓
> - 非 ARTIFACT_DRIFT / 非 PROVENANCE_INCOMPLETE

## 7. 交付物

- H0 commits：`qinghe_packet_builder.py` + `packet-policy.md`（hardened，selftest PASS）。
- H1（本 commit）：`nex005-qinghe-packet/out/selection-manifest.json` + `out/qinghe-evidence-packet.json` + `REPORT.md`。
- 供 NEX-006 Mac reconciliation 使用；无 canonical 写入；Canonical v0.1 FROZEN。

## 8. 下一步（待 Lead 决议）

**NEX-006 — Native Evidence × Narrative Research Reconciliation**：逐 claim 对照（Mac claim ↔ Windows EvidenceCluster ↔ canonical v0.1），输出 SUPPORTED / PARTIALLY_SUPPORTED / CONFLICT / UNRESOLVED，不直接写 canonical。

