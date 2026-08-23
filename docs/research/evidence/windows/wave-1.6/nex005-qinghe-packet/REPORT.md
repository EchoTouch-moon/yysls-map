# NEX-005 — Qinghe Structural Evidence Packet

> Task-ID: NEX-005 · Status: **DONE** · Gate: **QINGHE_EVIDENCE_PACKET_PASS**
> Base：`research/windows-evidence-tooling` · Frozen observation engine：**`204c97f`**
> Builder（P0 系列）：`5d5986e → fa594bd → 2f96d59 → 11f1a77 → 9c0f72d`（**最终 builder_commit = `9c0f72d`**）
> Commits：P0 冻结 builder+policy → P1 本 commit（manifest + evidence clusters + REPORT only）

---

## 0. 结论（一句话）

使用冻结 engine `204c97f` 与冻结选择政策（qinghe/叙事候选信号仅作优先级，**不作 canonical 事实**），构建了 **12 entries / 8 evidence clusters**（全部 ≤5 entries/cluster）的 Qinghe native structural evidence packet，provenance 完整（builder `9c0f72d` + engine `204c97f` + game_version + per-entry block_sha256），unresolved 语义显式保留，**零 canonical 写入**。

> **QINGHE_EVIDENCE_PACKET_PASS**

## 1. 两阶段 freeze / commit flow

```text
P0   5d5986e   qinghe_packet_builder.py + packet-policy.md（冻结政策）
P0'  fa594bd   records-dir 可重复（加载 regression/ + holdout-json/）
P0'' 2f96d59   新候选 engine runs 收敛到政策池（qinghe 全部 + 大文件 top-4）
P0'''11f1a77   §3a 聚类 caps（sub-split / fallback / merge）
P0''''9c0f72d  SELECT_N=12 + 清洗 sub-split key + merge 修复（最终 builder）
     （以上均为 pre-run 修正，policy 语义未变；packet 未产出前完成）
clean run @ 9c0f72d
P1   （本 commit）selection-manifest.json + qinghe-evidence-packet.json + REPORT only
```

## 2. 选择（12 entries，scope 12-20 ✓）

| entry | score | 主要 selection reasons |
| --- | --- | --- |
| LT71[1768] | 9 | dq_610900 TASK_REF、NodeGraphData、江晏/天泉/费亦可、MSD_ST、≥8KB |
| LT71[1631] | 7 | EXPANSION_QINGHE、方外地、≥8KB |
| LT71[1068] | 6 | NodeGraphData、赵铁、MSD_ST、≥8KB |
| LT71[493] LT51[2553] LT71[311] LT51[85] LT51[318] LT31[2369] LT71[2048] 等 9 个 | 6 | qinghe source 信号 + NodeGraphData |

## 3. Evidence clusters（8 clusters，全部 ≤5 entries ✓）

| cluster_id | n | 内容 |
| --- | --- | --- |
| QH_EXPANSION | 1 | LT71[1631]：EXPANSION_QINGHE + 2 specific obs |
| QH_SOURCE/guanqia/qinghe_end_task | 5 | 清河终章任务脚本族（_200443/_200453/_200451/_200464/_bxx）|
| QH_SOURCE/guanqia/qinghe_end_boss_fight | 1 | LT71[1886] |
| QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx | 1 | LT51[2194] |
| QH_SOURCE/task | 1 | LT51[1909]：qinghefenwei_yexiuluo |
| QH_SOURCE/task/lizehao | 1 | LT31[954]：qinghejianzhang_moonlight |
| TASK_DQ | 1 | LT71[1768]：dq_610900 + 5 specific obs |
| NODE_GRAPH | 1 | LT71[1068]：NodeGraphData + 赵铁 |

- specific observations 合计 8（R1/R2/R3/R5；R4 IDENTIFIER 不计）。
- 每 cluster：cluster_id / selection_reasons / source_families / entries（archive, entry_index, entry_offset, stored_size, block_sha256）/ source_observations / structural_observations（raw_value, byte_offset, pattern_kind, discovery_rule_id, discovery_method, confidence）/ provenance / warnings / unresolved。

## 4. Provenance

```text
builder_commit        = 9c0f72d（可 checkout 复现 builder）
extractor_commit      = 204c97f（frozen observation engine）
game_version          = 20260820220319
per-entry             = archive / entry_index / entry_offset / stored_size / block_sha256
```

## 5. 边界（copyright / scope）确认

```text
12-20 entries ✓（12）
5-8 clusters ✓（8）
max 3-5 entries/cluster ✓（全部 ≤5）
MAX_LOCATOR_BYTES=64 ✓
无 canonical 映射 / 无 confirmed character identity / 无 quest title 分配 ✓
无 owning proto / constant index / opcode/VM 工作 ✓
无 dialogue/prose dump / 无 scripts/assets 提交 ✓
```

## 6. Gate

> **QINGHE_EVIDENCE_PACKET_PASS**
> - ≥5 useful evidence clusters：**8** ✓
> - provenance complete：builder + engine + game_version + per-entry hashes ✓
> - 至少部分 Qinghe/叙事结构信号：EXPANSION_QINGHE、dq_610900、江晏/赵铁、qinghe 源族 ✓
> - unresolved 语义显式保留：unresolved[] + SEMANTIC_ROLE_UNVERIFIED warnings ✓
> - 零 canonical 写入 ✓
> - 非 EVIDENCE_TOO_SPARSE / 非 PROVENANCE_INCOMPLETE

## 7. 交付物

- P0 系列 commits：`qinghe_packet_builder.py` + `packet-policy.md`（冻结）。
- P1（本 commit）：`nex005-qinghe-packet/out/selection-manifest.json` + `out/qinghe-evidence-packet.json` + `REPORT.md`。
- 供 NEX-006 Mac reconciliation 使用；无 canonical 写入；Canonical v0.1 FROZEN。

## 8. 下一步（待 Lead 决议）

将本 packet（Windows native structural evidence）与 Mac 侧 narrative research 合并 → **NEX-006 reconciliation** → CANONICAL_CANDIDATE 讨论。
