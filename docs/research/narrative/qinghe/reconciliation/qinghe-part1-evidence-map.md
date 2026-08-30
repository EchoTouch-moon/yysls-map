# NEX-006 — 清河篇一 claim-level evidence map

> Reconciliation scope: Mac reviewed/public claims × Windows NEX-005 packet × frozen canonical v0.1
>
> Status vocabulary: `SUPPORTED` / `PARTIALLY_SUPPORTED` / `CONFLICT` / `UNRESOLVED` only
>
> Snapshot: base `3c99afe530c277a72243c1bf89cf913719faffb9`; Mac input `cd50bd24779fd47b808bc270a12c617cd9977be9`; Windows builder `6c47256be6f42b33826341bf217469be03d4c7ab`

## 1. 判定口径

这里的 `reconciliation_status` 是三类冻结输入之间的对账结论，不回写任何输入 state。

- `SUPPORTED`：相关 claim 被可定位、语义角色明确且来源独立的 native observation 支持，并与 Mac/canonical 无未决冲突。
- `PARTIALLY_SUPPORTED`：Mac reviewed/public claim 与 canonical 对应一致，但 current Windows packet 没有语义可归属的直接证据，或只支持 claim 的一部分。
- `CONFLICT`：至少两个不可自动覆盖的输入对同一 claim 给出互斥值；票数不裁决冲突。
- `UNRESOLVED`：缺少能确认或否定 claim 的直接证据；候选 path/token/cluster 不作语义证明。

Windows locator 统一指向 [NEX-005 packet](../../../evidence/windows/wave-1.6/nex005-qinghe-packet/out/qinghe-evidence-packet.json)。`archive[index] @ byte_offset` 中 offset 是 entry block 内 observation offset。

## 2. 「又见新来燕」5 个 main-quest claims

### NEX006-P1-001

- **claim_text**：篇一第 1 个 main-quest 为「竹林旧居线索」：红线唤醒主角，罐中信与灵位建立寻找江叔的目标。
- **Mac source locator**：[main-story-inventory.md](../main-story-inventory.md) §2 row 1；[interpretation](../interpretation/part-1-you-jian-xin-lai-yan.md) §2 L1；`SRC-ALI213-FULL-STORY` 第 1 页步骤 1–4；repo `v5 evt-p1-awaken`。
- **source_kind / evidence_role / original confidence-state**：`walkthrough + in_repo` / `IDENTITY, ORDER, CHARACTER` / `VERIFIED（节点存在）；细节待核`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。7 clusters 均无篇一、竹林旧居、红线、江叔或该任务 ID 的 owned observation。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1:awaken`（parent `...:part-1`, sort_order `1`）。
- **reconciliation_status**：`PARTIALLY_SUPPORTED`。
- **rationale**：Mac 节点/步骤与 frozen canonical title、parent、order 对齐；Windows packet 没有直接 native 语义匹配。
- **evidence limits**：canonical 的 `verified/published` 是冻结输入状态，不可反向当作 Windows 证据；`qinghe_end_task` 路径不是篇一节点证明。
- **needs_followup**：`YES` — 原生 task title/ID/parent 与红线、江叔角色引用。

### NEX006-P1-002

- **claim_text**：篇一第 2 个 main-quest 为「断桥」：桥断后以轻功过桥。
- **Mac source locator**：[main-story-inventory.md](../main-story-inventory.md) §2 row 2；[interpretation](../interpretation/part-1-you-jian-xin-lai-yan.md) §3；`SRC-ALI213-FULL-STORY` 第 1 页步骤 5；`SRC-SOHU-MAIN-STORY` 对应桥段。
- **source_kind / evidence_role / original confidence-state**：`walkthrough` / `IDENTITY, ORDER` / `VERIFIED`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。没有 owned title/order/bridge observation。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1:bridge`（parent `...:part-1`, sort_order `2`）。
- **reconciliation_status**：`PARTIALLY_SUPPORTED`。
- **rationale**：公开步骤与 canonical 节点/顺序一致；native packet 未命中桥段。
- **evidence limits**：教学位移的叙事意义与隐藏设计仍是 interpretation/UNRESOLVED；不能由节点邻近推断。
- **needs_followup**：`YES` — task title/ID/parent/order；隐藏设计仅在出现显式 metadata 时评估。

### NEX006-P1-003

- **claim_text**：篇一第 3 个 main-quest 为「北竹林学射」：冯继升（另有「冯继生」写法）教授射术并比试。
- **Mac source locator**：[main-story-inventory.md](../main-story-inventory.md) §2 row 3；[interpretation](../interpretation/part-1-you-jian-xin-lai-yan.md) §4；`SRC-ALI213-FULL-STORY` 第 1 页步骤 8–10；`SRC-BILIBILI-MAIN-PARTS` BV1ZL6fYMEer。
- **source_kind / evidence_role / original confidence-state**：`walkthrough + player` / `CHARACTER, TITLE, ORDER` / `VERIFIED（节点）；NPC 名写法 UNRESOLVED/SOURCE_CONFLICT`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。没有冯继升/冯继生或射术节点 observation。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1:archery`（parent `...:part-1`, sort_order `3`）。
- **reconciliation_status**：`PARTIALLY_SUPPORTED`。
- **rationale**：节点功能和顺序对齐，但角色精确字符串存在公开来源冲突且无 native 裁决。
- **evidence limits**：canonical note 本身也保留 NPC 名 unresolved；不能用任一攻略多数覆盖另一写法。
- **needs_followup**：`YES` — localization/quest 表中的 NPC display name 与 owned task link。

### NEX006-P1-004

- **claim_text**：篇一第 4 个 main-quest 为「百草野遇天涯客」：天涯客给清河舆图，随后有驱熊、偷师太极步骤；「天涯客 = 官方访谈中的神秘江湖人」只是候选。
- **Mac source locator**：[main-story-inventory.md](../main-story-inventory.md) §2 row 4 与 §3；[interpretation](../interpretation/part-1-you-jian-xin-lai-yan.md) §5；`SRC-ALI213-FULL-STORY` 第 1 页步骤 11–14；`SRC-YYSLCN-NARRATIVE-INTERVIEW` 仅称「神秘的江湖人」。
- **source_kind / evidence_role / original confidence-state**：`walkthrough + official` / `IDENTITY, CHARACTER, HIDDEN_CLUE` / `VERIFIED（节点）；人物对应 HIGH-CANDIDATE/W-VERIFY`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。`NODE_GRAPH` 的 `小稞@1794` 是 unrelated `SHORT_CJK_TERM_CANDIDATE`，不得借 cluster proximity 关联天涯客。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1:wilderness`（parent `...:part-1`, sort_order `4`）。
- **reconciliation_status**：`PARTIALLY_SUPPORTED`。
- **rationale**：节点步骤与 canonical 对齐；身份/暗线对应未获 native 支持，claim 只被部分支持。
- **evidence limits**：官方访谈没有点名天涯客；相似叙事位置不是身份等同证明。
- **needs_followup**：`YES` — NPC identity/reference、task link；若没有显式关联则保持候选。

### NEX006-P1-005

- **claim_text**：篇一第 5 个 main-quest 为「将军祠擂台」：方旭/老金相关擂台与听风辨位步骤收束篇一。
- **Mac source locator**：[main-story-inventory.md](../main-story-inventory.md) §2 row 5；[interpretation](../interpretation/part-1-you-jian-xin-lai-yan.md) §6；`SRC-ALI213-FULL-STORY` 第 1 页步骤 15–19；`SRC-9GAME-YJXL` 同 lineage 页面。
- **source_kind / evidence_role / original confidence-state**：`walkthrough` / `IDENTITY, ORDER, CHARACTER` / `VERIFIED（两页面一致，但同 lineage 不计独立 corroboration）`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。没有将军祠、方旭、老金或听风辨位的 owned observation。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1:arena`（parent `...:part-1`, sort_order `5`）。
- **reconciliation_status**：`PARTIALLY_SUPPORTED`。
- **rationale**：Mac 与 canonical 的节点/顺序一致；current native packet 无直接匹配，且两个页面不是独立来源。
- **evidence limits**：编辑性「立足」解读不由静态结构证明；同 lineage 页面不能提升 native confidence。
- **needs_followup**：`YES` — 原生 task title/ID/parent/order 与角色引用。

## 3. Required unresolved claims

### NEX006-UQ-002

- **claim_text**：游戏内篇一精确标题究竟是「又见新来燕」还是「又见新燕来」。
- **Mac source locator**：[unresolved-questions.md](../unresolved-questions.md) UQ-02；[main-story-inventory.md](../main-story-inventory.md) §2 note；[source-ledger.md](../source-ledger.md) `SRC-9GAME-NAME-VARIANT`（9game 10773761 / 10756501）。
- **source_kind / evidence_role / original confidence-state**：`walkthrough + in_repo` / `TITLE` / `SOURCE_CONFLICT, W-VERIFY`；ali213/3dm/9game 10773761 与 canonical 用「又见新来燕」，v5/9game 10756501 用「又见新燕来」。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。packet 没有任一标题字符串或 localization ownership。
- **canonical_key**：`wwm:qinghe:chapter-1:part-1`（frozen title `又见新来燕`）。
- **reconciliation_status**：`CONFLICT`。
- **rationale**：canonical 选定一个展示值不消除输入中记录的游戏内精确字符串争议；没有 native 字符串可裁决。
- **evidence limits**：来源多数、页面标题与 repo 既有值都不能代替任务簿/localization；禁止自动覆盖冲突。
- **needs_followup**：`YES` — P0 native localization；静态失败且阻塞展示时才人工任务簿 fallback。

### NEX006-UQ-019

- **claim_text**：「寻心」BOSS 是否就是寒姨/寒香寻，或是其换脸身份。
- **Mac source locator**：[unresolved-questions.md](../unresolved-questions.md) UQ-19；[hidden-story-inventory.md](../hidden-story-inventory.md) HC-09/DD-03；[source-ledger.md](../source-ledger.md) `SRC-ALI213-XUNXIN`。
- **source_kind / evidence_role / original confidence-state**：`walkthrough + in_repo` / `CHARACTER, MOTIVATION, HIDDEN_CLUE` / `CANDIDATE / HIGH-VALUE; single-source; W-VERIFY`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。packet 没有寻心、寒姨、寒香寻、换脸或 character-ID observation。
- **canonical_key**：`NONE`（`...:part-2:reunion` 只提供寒姨重逢的上下文，不表达该身份等式）。
- **reconciliation_status**：`UNRESOLVED`。
- **rationale**：单一攻略 claim 与 repo 标签弱自洽，但缺少独立/native identity link，也没有直接反证。
- **evidence limits**：角色共现、多重身份叙事合理性与 source path 都不能证明 identity equality。
- **needs_followup**：`YES` — character table/localization/owned quest text；若静态无法建立等式且该 claim 阻塞 P0，允许最小过场人工 fallback。

### NEX006-UQ-020

- **claim_text**：「少东家」「寒姨」「江叔」是否作为称谓出现在官方游戏文本，而不仅是社区/攻略惯称。
- **Mac source locator**：[unresolved-questions.md](../unresolved-questions.md) UQ-20；[character-aliases.md](../character-aliases.md) first-batch rows `protagonist`, `han-xiangxun`, `jiang-yan`。
- **source_kind / evidence_role / original confidence-state**：`community + walkthrough + in_repo` / `COMMUNITY_ALIAS, CHARACTER` / `COMMUNITY_COMMON; official usage UNRESOLVED`。
- **Windows cluster_id / archive-entry / observation**：`NONE` / `NONE` / `NONE`。packet 无三个称谓的 localization/dialogue observation。
- **canonical_key**：`NONE`（canonical spine 不建模 alias/character identity）。
- **reconciliation_status**：`UNRESOLVED`。
- **rationale**：公开使用足以维持 community alias 分类，但不能提升为 official alias。
- **evidence limits**：repo 文案与社区稳定使用不等于游戏内官方文本；精确字符串需要 owned localization/dialogue locator。
- **needs_followup**：`YES` — 三个 term 分别检索并返回 owning record/context；失败不应改变 community alias state。

### NEX006-UQ-021-A

- **claim_text**：游戏内明潮/暗涌机制为：明潮由主线收集，暗涌由侠迹/镇守/万事知/偷听收集，集齐后开启地图最终动画。
- **Mac source locator**：[unresolved-questions.md](../unresolved-questions.md) UQ-21；[hidden-story-inventory.md](../hidden-story-inventory.md) §2.5；[source-ledger.md](../source-ledger.md) `SRC-3DM-MINGAN-STORY` / `SRC-CHINA-MINGAN-STORY`（同一小黑盒 origin 的双镜像）。
- **source_kind / evidence_role / original confidence-state**：`community + official` / `HIERARCHY, PREREQUISITE, HIDDEN_CLUE` / `双线存在 HIGH；具体组成 SUPPORTED/W-VERIFY`。
- **Windows cluster_id / archive-entry / observation**：candidate surface only: `QH_SOURCE/guanqia/qinghe_end_task` (`LT71[502] NodeGraphData@941`, `LT51[2597] NodeGraphData@526`, `LT71[318] NodeGraphData@412`, `LT51[86] NodeGraphData@337`, `LT51[322] NodeGraphData@315`); `...end_task#2` (`LT31[2415] NodeGraphData@370`); `...end_boss_fight` (`LT71[1919] NodeGraphData@501`); `...end_boss_fight/bxx` (`LT51[2232] NodeGraphData@541`)。
- **canonical_key**：`NONE`（canonical v0.1 仅含 main spine）。
- **reconciliation_status**：`UNRESOLVED`。
- **rationale**：paths 表明存在 Qinghe end-task/boss-fight 候选结构，`NodeGraphData` 表明图结构候选；没有明潮/暗涌字符串、collection membership、prerequisite edge 或 owning proto，不能确认机制。
- **evidence limits**：`end_task` 不能直接解释为「集齐明潮/暗涌后的最终动画」；同 origin 双镜像只计一条 community claim。
- **needs_followup**：`YES` — 优先深挖这 8 个 entries 的 owned constants/refs，再扩展 localization/catalog 搜索。

### NEX006-UQ-021-B

- **claim_text**：清河暗涌内容结构包含燕北盟（王清/河东八骏）、活人医馆换脸术（寒姨/天不收）、佛子妙善与田英刺契丹使者。
- **Mac source locator**：[unresolved-questions.md](../unresolved-questions.md) UQ-21；[hidden-story-inventory.md](../hidden-story-inventory.md) HL-04/05/06 与 §2.5；[source-ledger.md](../source-ledger.md) `SRC-3DM-MINGAN-STORY` / `SRC-CHINA-MINGAN-STORY`。
- **source_kind / evidence_role / original confidence-state**：`community + official + in_repo` / `HIDDEN_CLUE, CHARACTER, MOTIVATION` / `HIGH-CANDIDATE/W-VERIFY`；田英/清风驿有 official anchor，但三组 native 命名/归属未确认。
- **Windows cluster_id / archive-entry / observation**：broad candidate surface only: `QH_SOURCE/task` (`LT51[1943] NodeGraphData@538`, source `.../task/qinghefenwei_yexiuluo.lua`); `QH_SOURCE/task/lizehao` (`LT31[972] NodeGraphData@346`, `nodeID@496`, `is_only_once@574`, source `.../qinghejianzhang_moonli...`)；其余 end-task clusters 见 UQ-021-A。没有目标人物/组织/术语的 observation。
- **canonical_key**：`NONE`。
- **reconciliation_status**：`UNRESOLVED`。
- **rationale**：packet 给出若干清河 task 结构入口，但没有燕北盟、换脸、妙善、田英等 owned semantic strings；official 清风驿 anchor 也不能自动证明完整三组结构。
- **evidence limits**：文件 locator 中的 `qinghe` 只定位区域候选；`NodeGraphData/nodeID/is_only_once` 是结构 token，不提供 hidden-clue semantics。
- **needs_followup**：`YES` — 目标术语/人物 ID 的 localization、story-collection membership 与 task/story refs。

## 4. Status 统计

| reconciliation_status | count |
| --- | ---: |
| `SUPPORTED` | 0 |
| `PARTIALLY_SUPPORTED` | 5 |
| `CONFLICT` | 1 |
| `UNRESOLVED` | 4 |
| **total claims** | **10** |

补充口径：`UNRESOLVED` claim 数 = **4**；仍开放的 required UQ ID 数 = **4**（UQ-02/19/20/21，其中 UQ-21 拆成 2 个原子 claim）；`needs_followup=YES` = **10**。这不改变 frozen canonical 的 verification state。

## 5. Evidence roles：Windows 静态证据能/不能证明什么

| evidence_role | current packet 能证明 | current packet 不能证明 | 关闭该 role 所需最小证据 |
| --- | --- | --- | --- |
| `TITLE` | 精确 byte 中存在某字符串（若提取到）及其 locator | 当前没有篇一标题；path/攻略标题不能证明 UI/native title | owned localization/task-title field + task identity；UI 精确呈现仍可需截图 |
| `HIERARCHY` | 某 entries 含 `NodeGraphData`/`nodeID` 候选 | token 共现不证明 parent-child、明潮/暗涌 collection membership | owning proto/table + typed parent/collection edge + 两端 IDs |
| `ORDER` / `PREREQUISITE` | entry/byte 顺序与 cluster membership | byte offset、entry index、文件邻近均不等于剧情顺序或 prerequisite | typed sequence/prerequisite fields，或游戏内任务接续记录 |
| `CHARACTER` | 精确字符串/ID 的存在（当前目标词未命中） | `SHORT_CJK`、共现或角色名相似不能证明身份等式/说话人 | character ID ↔ display name ↔ owned quest/dialogue ref |
| `HIDDEN_CLUE` | 明确 story-collection/task refs 若能提取 | `qinghe_end_task`、`boss_fight` 路径和 cluster proximity 不证明暗涌机制/含义 | 明潮/暗涌 resource identity + membership/prerequisite + owned semantic labels |
| `IDENTITY` | archive/entry/block hash 与 candidate source locator 可复核 | source path、identifier token 不等于 canonical quest identity | native task ID/title/region/parent 的同一 owned record |
| `MOTIVATION` / `FORESHADOWING` | 通常只能提供剧情资产定位入口 | 静态结构不能从 token 推导人物动机、因果或伏笔解释 | 受限的任务文本/过场上下文 + Mac interpretation 审核；不提交完整文本 |

## 6. Windows packet 7 clusters 完整去向

| cluster_id | archive / entry_index | relevant observation @ offset | reconciliation destination | disposition |
| --- | --- | --- | --- | --- |
| `QH_SOURCE/guanqia/qinghe_end_task` | `LT71[502]`, `LT51[2597]`, `LT71[318]`, `LT51[86]`, `LT51[322]` | `NodeGraphData@941/526/412/337/315`; `nodeID@495` on `LT51[322]` | `NEX006-UQ-021-A` | follow-up seed only; no part-1 or mechanism semantics |
| `QH_SOURCE/guanqia/qinghe_end_task#2` | `LT31[2415]` | `NodeGraphData@370` | `NEX006-UQ-021-A` | deterministic cap split; adjacency to first cluster adds no semantics |
| `QH_SOURCE/guanqia/qinghe_end_boss_fight` | `LT71[1919]` | `NodeGraphData@501` | `NEX006-UQ-021-A` | boss-fight path is a locator, not final-animation proof |
| `QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx` | `LT51[2232]` | `NodeGraphData@541`; `autoStartList@643` | `NEX006-UQ-021-A` | structural candidate only; no owned story role |
| `QH_SOURCE/task` | `LT51[1943]` | `NodeGraphData@538`; `nodeID@808` | `NEX006-UQ-021-B` | broad Qinghe task seed; filename cannot prove hidden structure |
| `QH_SOURCE/task/lizehao` | `LT31[972]` | `NodeGraphData@346`; `nodeID@496`; `is_only_once@574` | `NEX006-UQ-021-B` | broad Qinghe task seed; `lizehao/moonli` not mapped to required claim |
| `NODE_GRAPH` | `LT71[1248]`, `LT31[566]` | `小稞@1794` (SHORT_CJK); `13610@93` (TEXT_REF); `传送配置@641` (SHORT_CJK) | `NONE` (negative control / excluded) | generic MSD_ST/small-theater/teleport candidates; no semantic match to required claims |

All 7 clusters retain packet warnings `SEMANTIC_ROLE_UNVERIFIED`, `CONSTANT_OWNERSHIP_UNKNOWN`, and `PROTO_OWNERSHIP_UNKNOWN`; none is silently dropped or promoted.
