# NEX-005 — Qinghe Evidence Packet: Frozen Selection Policy

> Task: NEX-005 Qinghe Structural Evidence Packet
> 本政策随 `qinghe_packet_builder.py` 在 **P0** 冻结；P1 只提交 manifest + clusters + REPORT。
> Frozen observation engine：**`204c97f`**（R1-R5 与 observation caps 不修改）。
> 本任务**不是** blind benchmark —— 候选优先级可合法使用 Qinghe/叙事信号（见下），但**不解释为 canonical 事实**。

## 1. 候选池（deterministic）

```text
a. 已知 processed records：
   4 pilots   LT71[1768] LT71[1631] LT31[874] LT51[1178]（regression/）
   12 holdout holdout-json/ 全部
b. Qinghe-source 新候选：source region 含 "qinghe"/"QINGHE"/"清河"（全量扫描 LT71/LT51/LT31）
c. 大文件 family 新候选：family（storyline_data/MSD_ST）+ stored_size >= 8000
   （排除 a/b 已含），size desc，sha256("{arch}:{idx}") 平局，取前 4
```

## 2. 优先级评分（允许的信号；NOT truth）

```text
Qinghe 信号（source 含 qinghe/QINGHE/清河，或 EXPANSION_QINGHE observation）  +4
dq_* TASK_REF observation                                                    +3
NodeGraphData observation                                                    +2
SHORT_CJK_TERM observation                                                   +2
TEXT_REF (numeric) observation                                               +1
family == MSD_ST                                                             +1
stored_size >= 8000                                                          +1
```

选中 top 16（score desc → size desc → sha256 平局）。

## 3. 聚类（优先级分配，≤5 entries/cluster，目标 5-8 clusters）

```text
C1 QH_EXPANSION  含 EXPANSION_QINGHE observation
C2 QH_SOURCE     source 含 qinghe/QINGHE/清河（未入 C1）
C3 TASK_DQ       ≥1 个 dq_* TASK_REF observation（未入 C1/C2）
C4 NODE_GRAPH    含 NodeGraphData observation（未入 C1-C3）
C5 CJK_TERM      ≥1 个 SHORT_CJK_TERM observation（未入 C1-C4）
C6 NUM_REF       ≥1 个 TEXT_REF observation（未入 C1-C5）
C7 FAMILY_MSD    family == MSD_ST（未入 C1-C6）
C8 FAMILY_ST     family == storyline_data（未入 C1-C7）
```

空 cluster 丢弃；若 >8 个非空 cluster，合并最小的进入 C8。

## 4. Cluster 内容

```text
cluster_id
selection_reasons[]         逐条记录选中原因（信号/优先级）
source_families[]
entries[]                   archive, entry_index, entry_offset, stored_size, block_sha256
source_observations[]       per-entry source observation（bounded，≤64B locator）
structural_observations[]   raw_value, byte_offset, pattern_kind, discovery_rule_id,
                            discovery_method, confidence（每 cluster ≤60，字节序）
provenance                  见 §5
warnings[]
unresolved[]                显式保留未决语义（无 canonical 映射）
```

## 5. Provenance

```text
builder_commit        = P0 sha（git rev-parse HEAD，运行点）
extractor_commit      = 204c97f（frozen observation engine）
game_version          = Patch/patching_version.txt
每 entry：archive / entry_index / entry_offset / stored_size / block_sha256
```

## 6. 边界（copyright / scope）

```text
12-20 entries（选中 16）
5-8 clusters（≤5 entries/cluster）
MAX_LOCATOR_BYTES = 64
无 canonical 映射 / 无 confirmed character identity / 无 quest title 分配
无 owning proto / constant index / opcode/VM 工作
无 dialogue/prose dump / 无 scripts/assets 提交
```

## 7. Gate

```text
>=5 useful clusters + provenance complete + 至少部分 Qinghe/叙事结构信号
+ unresolved 显式保留 + 零 canonical 写入 -> QINGHE_EVIDENCE_PACKET_PASS
否则 -> EVIDENCE_TOO_SPARSE / PROVENANCE_INCOMPLETE
```
