# Wave 1.6 Dual-Machine Task Distribution

> Status: **ACTIVE**  
> Direction: `docs/WAVE_1_6_NARRATIVE_DIRECTION.md`  
> Rule: Mac 与 Windows 可以并行执行，但 **raw evidence 与 reviewed conclusion 必须分离**。

## 0. 执行协议

### 0.1 机器职责

- **Mac**：Research / Analysis / Product Hub
- **Windows**：Game Evidence / Local Asset Feasibility Station

### 0.2 状态词

每个任务只允许使用：

- `READY`
- `IN_PROGRESS`
- `WAITING`
- `BLOCKED`
- `DONE`
- `REVIEW_REQUIRED`
- `CLOSED`

### 0.3 回报格式

每台机器完成任务后统一用：

```text
Task-ID:
Status:
Branch / Commit:
Inputs:
Outputs:
Evidence:
Unresolved:
Risks:
Next:
```

### 0.4 强约束

1. Windows 不直接修改正式 canonical dataset；
2. Mac 不凭二手攻略把未确认节点升级为 VERIFIED；
3. raw screenshot/video 默认不提交 GitHub；
4. 不在两台机器上同时编辑同一个正式 JSON；
5. Local asset research 只读优先，不绕过加密/DRM/反作弊；
6. 任何“为了 UI 好看”而修改 canonical fact 的行为禁止；
7. 发现事实问题时记录 Data Defect / Unresolved，不顺手改解释层掩盖。

---

# 1. Mac Track

## M-00 — Baseline Sync & Workspace Check

**Owner**: Mac  
**Status**: READY

### 输入

- remote `codex/mvp-platform`
- Wave 1.6 direction doc
- current frozen canonical v0.1

### 操作

1. fetch remote；
2. 确认当前 HEAD 包含 Wave 1.6 docs；
3. 检查 working tree；
4. 不覆盖任何未提交本地变更；
5. 建议建立工作分支：`research/wave-1.6-mac-narrative`。

### 输出

- 当前 HEAD；
- working tree 状态；
- branch；
- 是否存在本地冲突/未提交文件。

### 验收

- provenance 清楚；
- 不带入旧脏工作树。

### STOP

发现无法解释的本地修改时停止，不 rebase/reset 覆盖。

---

## M-01 — Qinghe Narrative Research Index

**Owner**: Mac  
**Status**: READY  
**Depends on**: M-00

### 目标

建立清河研究总账，不再让资料散落在不同文档中。

### 建议目录

```text
docs/research/narrative/qinghe/
├── README.md
├── source-ledger.md
├── main-story-inventory.md
├── hidden-story-inventory.md
├── unresolved-questions.md
├── character-aliases.md
└── interpretation/
    └── part-1-you-jian-xin-lai-yan.md
```

### 操作

1. 汇总已有 canonical research 文档；
2. 汇总公开资料来源；
3. 不复制大段攻略原文，只记录 claim + locator + URL + evidence role；
4. 建立 unresolved registry；
5. 把 Windows 后续需要现场确认的问题明确列出。

### 输出

至少形成：

- 清河故事结构总表；
- `又见新来燕` 已知任务节点；
- 已知明/暗线关联候选；
- 需要 Windows 核实的问题列表。

### 验收

每条高价值 claim 至少包含：

```text
claim
source
source_kind
evidence_role
confidence / state
notes
```

---

## M-02 — Public Source Expansion

**Owner**: Mac  
**Status**: READY  
**Depends on**: M-01

### 目标

补充公开资料，尤其是：

- 第一章结构；
- 又见新来燕完整流程；
- 明潮/暗涌；
- 清河明暗故事；
- 侠迹/镇守/奇遇/万事知与主线关系；
- 关键人物动机；
- 官方/社区称谓。

### 操作

按 evidence role 记录：

- `IDENTITY`
- `TITLE`
- `HIERARCHY`
- `ORDER`
- `PREREQUISITE`
- `CHARACTER`
- `HIDDEN_CLUE`
- `MOTIVATION`
- `FORESHADOWING`
- `COMMUNITY_ALIAS`

### 输出

更新 `source-ledger.md` 与各 inventory。

### 验收

不能只堆 URL；必须说明每个来源能证明什么、不能证明什么。

---

## M-03 — Community Alias Ledger

**Owner**: Mac  
**Status**: READY  
**Depends on**: M-01

### 目标

建立玩家友好称谓表。

### 最小字段

```text
character_id / slug
canonical_name
alias
alias_kind = OFFICIAL_ALIAS | COMMUNITY_COMMON | COMMUNITY_MEME
source
context
safe_for_narrative
notes
```

### 首批

至少研究：

- 主角 / 少东家；
- 寒香寻 / 寒姨；
- 江晏 / 江叔；
- 红线；
- 伊刀；
- 田英；
- 王清等当前清河核心人物。

### 验收

- alias 不替代 canonical identity；
- meme 不进入事实字段；
- 至少区分官方称谓与社区称谓。

---

## M-04 — “又见新来燕” Deep-Dive Skeleton

**Owner**: Mac  
**Status**: READY  
**Depends on**: M-01, 可与 W-01/W-02 并行

### 目标

先搭深度解析模板，不等待所有现场证据完成。

### 每个子段至少预留

1. 发生了什么；
2. 为什么发生；
3. 少东家此时知道什么；
4. 其他角色知道什么；
5. 人物动机；
6. 明潮；
7. 暗涌；
8. 第一次玩容易漏掉什么；
9. 回头看才明白的伏笔；
10. 与后续剧情的关系；
11. 社区称谓/玩家语境；
12. 历史背景；
13. 事实/推测/争议边界。

### 输出

`interpretation/part-1-you-jian-xin-lai-yan.md`

### 验收

允许大量 `TODO: NEED_GAME_EVIDENCE`，但不能用猜测填空。

---

## M-05 — Windows Evidence Reconciliation

**Owner**: Mac  
**Status**: WAITING  
**Depends on**: W-01, W-02, W-03

### 目标

把游戏内 evidence 与公开资料对齐。

### 操作

对每个 claim 标记：

- `CONFIRMED_IN_GAME`
- `PUBLIC_ONLY`
- `OBSERVED_ONLY`
- `SOURCE_CONFLICT`
- `UNRESOLVED`

### 输出

- `qinghe-part1-evidence-map.md`
- Windows 第二轮定向补证据清单

### 验收

不因为多数来源一致就覆盖游戏内冲突。

---

## M-06 — Narrative Model v0.2 Proposal

**Owner**: Mac  
**Status**: WAITING  
**Depends on**: M-05, W-04

### 目标

提出模型，不迁移数据库。

### 必须回答

1. `明潮` 是否映射现有 CanonicalStoryNode spine；
2. `暗涌` 是 node、clue、thread 还是独立结构；
3. 一个暗涌如何连接多个 canonical nodes；
4. 伏笔/回看如何表达；
5. CharacterAppearance / CharacterRecall 是否需要新模型；
6. alias 放数据层还是展示层；
7. 如何保持 field-level reveal 与当前 page/entity reveal 的边界；
8. 如何兼容现有 StoryEvent/StoryArcBeat。

### 输出

`docs/research/narrative-model-v0.2-proposal.md`

### 验收

- additive first；
- 不破坏 frozen v0.1；
- 明确 migration 是否真的必要；
- 给出 rejected alternatives。

### STOP

没有足够现场 evidence 时不要写 schema migration。

---

## M-07 — Reading UX v2 Prototype Spec

**Owner**: Mac  
**Status**: WAITING  
**Depends on**: M-04, M-06

### 目标

设计而非立即实现。

### 原型必须包含

- 明潮 continuous rail；
- 暗涌局部分叉；
- inline character mention；
- Desktop popover；
- Mobile bottom sheet；
- zero-link / unresolved presentation；
- “完整事件”重定位为资料库/事件档案；
- deep link；
- spoiler gate。

### 输出

`docs/research/reading-ux-v2-proposal.md`

### 验收

明确“滚动负责前进，点击负责深入”仍成立。

---

## M-08 — Yanyun Visual Language Study

**Owner**: Mac  
**Status**: READY  
**Depends on**: None

### 目标

研究《燕云》视觉语法，但暂不全站改 CSS。

### 记录维度

- 页面结构；
- 长卷感；
- 墨/纸/金/朱；
- 线性连接；
- 雾与留白；
- 信息密度；
- 动效节制；
- Typography；
- 明潮/暗涌层级。

### 输出

`docs/research/yanyun-visual-language.md`

### 验收

结论必须区分：

- 可借鉴的信息设计；
- 可借鉴的视觉语法；
- 不应复制的具体资产/装饰。

---

# 2. Windows Track

## W-00 — Baseline / Evidence Workspace Setup

**Owner**: Windows  
**Status**: READY

### 目标

把 Windows 定义为 evidence station，不作为正式产品编辑机。

### 操作

1. 确认游戏版本/区服/日期；
2. 建立本地证据目录；
3. 不把大型截图/视频直接提交仓库；
4. 建立 evidence ledger。

### 建议目录

```text
EVIDENCE-QH-WAVE16/
├── ledger.csv
├── screenshots/
├── clips/
├── observations/
└── asset-feasibility/
```

### ledger 最小字段

```text
evidence_id,type,area,subject,captured_at,game_version,file,hash,note
```

### 验收

- evidence ID 稳定；
- 文件可回溯；
- 截图不再使用随机名字作为唯一索引。

---

## W-01 — Native “明潮 / 暗涌” UI Capture

**Owner**: Windows  
**Status**: READY  
**Depends on**: W-00

### 目标

系统记录游戏自己如何呈现明线/暗线。

### 必采视图

1. 进入相关系统前的入口；
2. 清河全局；
3. 第一章相关明潮；
4. 暗涌展开前；
5. 暗涌展开后；
6. 节点 hover/click/details；
7. 已解锁 vs 未解锁；
8. 线、节点、图例、颜色、层级；
9. 如存在关系/时间/区域切换，也记录。

### 每张截图记录

```text
what_is_visible
what_is_clickable
what_changes_after_click
what_is_locked
observed_labels
uncertainty
```

### 输出

- 截图 evidence pack；
- `observations/native-story-ui.md`

### 验收

不能只交“几张好看的图”；必须能还原交互层级。

---

## W-02 — Qinghe Chapter 1 Native Structure Capture

**Owner**: Windows  
**Status**: READY  
**Depends on**: W-00

### 目标

确认第一章、四篇与可见任务层级。

### 必采

- 第一章标题；
- 四篇名称；
- 游戏显示顺序；
- 每篇可见 main quest 名称；
- 已完成/未完成状态；
- 任务簿中 parent/child 视觉层级；
- 若有 prerequisite 或 unlock 提示，记录；
- 任务完成后系统如何归档。

### 输出

`observations/qinghe-ch1-native-structure.md`

### 验收

每个 observation 指向 evidence ID，不直接写“VERIFIED canonical”。

---

## W-03 — “又见新来燕” Flow Capture

**Owner**: Windows  
**Status**: READY  
**Depends on**: W-00

### 目标

把 pilot 所需现场证据采到足够细。

### 优先采集

- 任务开始时状态；
- 当前目标变化；
- 关键人物出现；
- 关键地点；
- 系统任务名；
- 任务完成；
- 明潮节点变化；
- 暗涌相关变化；
- 任务后人物/世界状态变化。

### 额外观察

遇到关键人物时记录：

```text
人物称谓
UI 中的正式名
NPC/剧情中常见叫法
少东家此时是否应该认识此人
当前剧情需要玩家记住什么
```

### 输出

`observations/part1-flow.md`

### 验收

能让未在现场的 Mac reviewer 大致重建流程，而不依赖记忆猜测。

---

## W-04 — Narrative Surface Inventory

**Owner**: Windows  
**Status**: READY  
**Depends on**: W-01/W-02

### 目标

盘点游戏内有哪些可能承载清河暗线信息的系统。

### 检查

- 明暗故事；
- 侠迹；
- 镇守；
- 奇遇；
- 万事知；
- 人物志/人物页；
- 道具/书信/记录；
- 世界探索日志；
- 其他剧情回顾入口。

### 输出

表格：

```text
surface
entry_path
contains_story_identity
contains_order
contains_unlock_state
contains_character_info
contains_hidden_clue
usefulness
```

### 验收

只是 inventory，不要求全量收集每一条内容。

---

## W-05 — Mac Unresolved Targeted Recheck

**Owner**: Windows  
**Status**: WAITING  
**Depends on**: M-05

### 目标

只补 Mac reconciliation 之后仍 unresolved 的关键问题。

### 规则

- 一次只查明确问题；
- 不再漫无目的全图截图；
- 每个问题输出 `CONFIRMED / NOT_FOUND / CONFLICT / CANNOT_REPRODUCE`。

### 输出

`observations/targeted-recheck.md`

---

## W-06 — Local Asset Feasibility: Installation Inventory

**Owner**: Windows  
**Status**: READY  
**Depends on**: W-00

### 目标

只读确认安装目录与资源形态。

### 允许操作

- 查看目录结构；
- 记录扩展名；
- 查看普通文本/公开 manifest/index；
- 计算文件 hash；
- 记录更新时间、大小、路径模式。

### 重点寻找

```text
manifest
index
localization
string table
quest/task table
json/csv/db/sqlite
pak/bundle/archive metadata
```

### 输出

`asset-feasibility/install-inventory.md`

### 验收

给出：

- `STRUCTURED_VISIBLE`
- `ARCHIVED_BUT_INDEXED`
- `OPAQUE`
- `UNKNOWN`

而不是直接声称“能解包”。

### STOP

任何步骤要求绕过权限、解密、注入、反作弊或修改游戏文件时停止。

---

## W-07 — Local Asset Feasibility: Metadata Probe

**Owner**: Windows  
**Status**: WAITING  
**Depends on**: W-06

### 目标

如果 W-06 发现普通可读或合法可解析 metadata，再做最小 probe。

### 只回答

1. 是否存在稳定 quest/task ID；
2. 是否存在 localization key；
3. 是否存在 parent/chapter；
4. 是否存在 prerequisite/order/category；
5. 是否能仅提取 metadata 而不接触完整剧情文本/资产。

### 输出

`asset-feasibility/metadata-probe.md`

### 最终判定

- `FEASIBLE`
- `PARTIAL`
- `NO_GO`

### STOP

不要为了获得“完整结果”扩大到 runtime memory / anti-cheat / protected asset bypass。

---

# 3. Join / Merge Track

## J-01 — Evidence Join Review

**Owner**: Mac Lead  
**Status**: WAITING  
**Depends on**: M-05, W-05

### 目标

决定第一轮 evidence 是否足够支撑 Narrative Model 与 Deep Dive。

### Gate

- 任务 title/order/hierarchy：关键项有强证据；
- 明潮/暗涌：至少理解其 UI 与基本语义；
- unresolved 有明确列表；
- 不存在“为了完整而猜”的 published claim。

### 结果

- `E0 PASS`
- `E0 PASS_WITH_GAPS`
- `E0 NO_GO`

---

## J-02 — Asset Research Decision

**Owner**: Mac Lead + Windows evidence  
**Status**: WAITING  
**Depends on**: W-06, 可选 W-07

### 决策问题

> Public + Observed 是否已经足够？

若足够：

- extractor `NO_GO / NOT_NEEDED`。

若不足且 metadata probe 可行：

- 另起 proposal，定义最小 extractor 范围；
- 不在本 Task 内实现。

---

## J-03 — “又见新来燕” Deep-Dive Review

**Owner**: Mac Lead  
**Status**: WAITING  
**Depends on**: M-04, M-05, J-01

### Gate

pilot 是否真的覆盖：

- 发生什么；
- 因果；
- 动机；
- 信息差；
- 明潮/暗涌；
- 伏笔；
- 玩家称谓；
- 历史/推测边界。

### 通过标准

不是“更长”，而是能让玩家重新组织故事。

---

## J-04 — E1/E2 GO Decision

**Owner**: Lead  
**Status**: WAITING  
**Depends on**: J-01, J-03

### 可能结果

- `Narrative Model v0.2 — GO`
- `Deep Dive Pilot Implementation — GO`
- `Need More Evidence — RETURN_TO_E0`

在 J-04 之前，不开始正式 DB migration，也不把全清河一次性深挖。

---

# 4. Suggested Parallel Order

## Mac 第一批

```text
M-00
 ├─ M-01
 │   ├─ M-02
 │   ├─ M-03
 │   └─ M-04
 └─ M-08
```

## Windows 第一批

```text
W-00
 ├─ W-01
 ├─ W-02
 ├─ W-03
 └─ W-06
      └─ W-07 (only if allowed/needed)
```

第一轮汇合：

```text
M-01/M-02/M-04
      +
W-01/W-02/W-03
      ↓
M-05
      ↓
W-05
      ↓
J-01 / J-03
```

Asset 分支独立汇合：

```text
W-06
  ↓
W-07?
  ↓
J-02
```

---

# 5. 当前明确不做

- 不继续优化 Canvas；
- 不扩开封；
- 不增加 AI chat；
- 不做账号/收藏；
- 不全量搬运游戏文本；
- 不直接开始大规模解包；
- 不为“完整事件”马上写第二次大重构；
- 不在 evidence 未闭环前扩展 canonical v0.2；
- 不用 UI 需求反向改事实层。

---

# 6. 第一轮执行完成后的最小交付集

## Mac

- `docs/research/narrative/qinghe/README.md`
- `source-ledger.md`
- `unresolved-questions.md`
- `character-aliases.md`
- `interpretation/part-1-you-jian-xin-lai-yan.md`
- `yanyun-visual-language.md`

## Windows

本地 evidence pack：

- `ledger.csv`
- `observations/native-story-ui.md`
- `observations/qinghe-ch1-native-structure.md`
- `observations/part1-flow.md`
- `asset-feasibility/install-inventory.md`

Windows 的 raw image/video 不要求进 Git；后续只把必要的 observation、hash、选定截图或可公开派生材料提交仓库。

---

# 7. Definition of Done — First Dual-Machine Cycle

第一轮双机任务只有在以下条件全部满足时才算完成：

1. Mac 已把公开资料整理成 claim/evidence，而不是链接堆；
2. Windows 已完成游戏原生明潮/暗涌和第一章结构的首轮观察；
3. “又见新来燕”有可追踪 evidence map；
4. unresolved list 能明确告诉 Windows 下一次进游戏查什么；
5. local asset feasibility 至少完成 installation inventory；
6. 没有任何正式 canonical 数据因为这轮采集被未经 review 地修改；
7. Lead 可以明确决定：继续补证据 / 进入 Narrative Model v0.2 / 是否需要 metadata extractor proposal。
