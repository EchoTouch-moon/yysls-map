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

## 9. Addendum（2026-08-29）：PR #1 review 修复后重建（drift + hardened provenance）

触发原因：

1. **PR #1 review（3×P1 + 1×P2）**——builder 侧修复：
   - `verify_provenance`：对每条入选记录**基于当前归档目录重新验证**（不再只查字段形状）：mpkinfo 版本/尺寸不变量、streaming 重算 `mpkinfo_sha256` / `archive_sha256`、entry 元数据三元组 `(offset, stored_size, flags)` 逐条比对、重读块并重算 `block_sha256`、`game_version` 一致性；任一不符 → fail closed（不写文件）。
   - `verify_extractor_blob`：`extractor_source_sha256` 必须等于 `git show <extractor_commit>:discovery_engine.py` 的 blob sha256（本次 = `6be80797…`）。
   - **cluster 5 条上限改为硬保证**：超限组按序分块（`#2`、`#3`…），写文件前对全部集群断言 `≤ 5`，否则 fail closed。reviewer 复现的 `[6,1,1,1,1]` 输入在 selftest 中断言通过（分成 5+1）。
   - `discover_new` 改为**从 `ENGINE_COMMIT` 的 git blob 逐字节装载冻结引擎**（临时文件保持 `extractor_source_sha256` = blob sha 恒定），并跳过已有记录覆盖的条目，杜绝重复入选。
2. **第二次 baseline drift**（`patching_version.txt` → `20260829165912`）：全部 24 条输入记录（4 regression + 8 blind + 12 holdout）用冻结引擎 `204c97f` 对当前归档重新生成；holdout manifest 同步重新冻结（schema v2，详见 nex004c REPORT §9）。

**重建结果（确定性重跑，冻结选择政策未变）**：

| cluster | 条目 |
| --- | --- |
| QH_SOURCE/guanqia/qinghe_end_task | LT71[502], LT51[2597], LT71[318], LT51[86], LT51[322] |
| QH_SOURCE/guanqia/qinghe_end_task#2 | LT31[2415]（6 条组按新硬上限分块） |
| QH_SOURCE/guanqia/qinghe_end_boss_fight | LT71[1919] |
| QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx | LT51[2232] |
| QH_SOURCE/task | LT51[1943] |
| QH_SOURCE/task/lizehao | LT31[972] |
| NODE_GRAPH | LT71[1248], LT31[566]（holdout 集中的 MSD_ST 数据脚本，兼有 SHORT_CJK） |

与旧快照的差异均为 drift 后果：入选集合/成员变化源于归档字节变化后的确定性重跑；旧 §4-§6 的逐条对照对应 20260820220319 快照，保留为历史。

```text
builder_commit          = 3a43aa8（hardened builder；verify_builder_identity 对照通过）
builder_source_sha256   = SHA256(qinghe_packet_builder.py @ 3a43aa8)
extractor_commit        = 204c97f（输入记录一致 + blob 校验）
extractor_source_sha256 = 6be80797…（= git blob sha，verify_extractor_blob 通过）
game_version            = 20260829165912（当前 patching_version.txt）
per-entry               = archive / entry_index / entry_offset / stored_size / block_sha256（对当前归档重算吻合）
```

**Gate 复评**：入选 12 条、7 clusters（∈[5,8]）、每 cluster ≤5、provenance 全链对当前归档实测吻合、零 canonical 写入 → **维持 QINGHE_EVIDENCE_PACKET_PASS**。原 §6 中"与先前运行逐项一致"的核对对象已因 drift 作废；本 addendum 的核对对象 = 当前冻结工件集 ↔ 当前归档状态。

## 10. Addendum（2026-08-30）：复审新 P1 修复——候选去重先于 top-4 截断

复审指出 `discover_new` 先执行 `large_only[:4]` 再排除已有记录覆盖的条目，与冻结政策 §1.c（"排除 a/b 已含"**先于**"取前 4"）顺序相反；当已有记录进入原始 top-4 时，会吞掉新大文件候选名额。

**修复**（`6c47256`）：提取纯函数 `select_candidates(new, existing_keys)`——先在全候选池上过滤 `existing_keys`，再拆分 Qinghe-source / large-family 并取 top-4。selftest 补入评审复现用例（`[100(existing),90,80,70,60]` → `[90,80,70,60]`，而非旧实现的 `[90,80,70]`）及 Qinghe 候选去重用例。

**实际影响评估**（对当前归档重新扫描，`game_version=20260829165912`）：

- 候选池：26 Qinghe-source + 107 large-family；已记录条目 16 个（4 regression + 12 holdout）。
- 原始 large top-4 = LT31[75]（54354B）、LT51[2682]（53975B）、LT71[2419]（45917B）、LT71[1990]（39054B）——**均不在已记录集合中**（已记录的最大条目仅 8248B）；因此本次运行旧实现并未吞掉名额，修复前后 `to_run` 完全相同（各 30 条），**入选 12 条与 7 clusters 逐位一致**。修复属消除潜在违规 + selftest 回归覆盖；若未来 drift 使已记录条目进入 top-4，正确顺序即生效。
- 工件按新 `builder_commit` 重建（provenance 完整性要求）；除 `builder_commit` / `builder_source_sha256` 字段外无字节差异。

```text
builder_commit          = 6c47256be6f42b33826341bf217469be03d4c7ab
builder_source_sha256   = 2c0112b8c01d42d35b914799a37c11d93a3752d41ae2e02a38fcb1d946261847
extractor_commit        = 204c97f（不变；输入记录一致 + blob 校验）
extractor_source_sha256 = 6be80797…（不变）
game_version            = 20260829165912（不变）
```

**Gate 复评**：选择集不变、7 clusters（∈[5,8]）、每 cluster ≤5、provenance 全链实测吻合、零 canonical 写入 → **维持 QINGHE_EVIDENCE_PACKET_PASS**。§9 中 `builder_commit = 3a43aa8` 的 provenance 块由本节取代。
