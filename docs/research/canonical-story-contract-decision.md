# Canonical Story Contract — Schema Decision Memo

> 阶段：Wave 1.5 / Canonical Story Alignment — Task 5
> 结论（三选一）：**ADDITIVE_MODEL_RECOMMENDED**
> 依据：docs/research/architecture-reality-summary.md + qinghe-canonical-story-inventory.md + qinghe-current-to-canonical-mapping.md。
> 本 memo 只作决策与候选字段提案；**不在本任务内实施 migration、改 ORM、改 JSON schema 或重冻结 v5**。

## 0. Lead 决议更新（2026-08-22，Phase A/B ACCEPTED 后）

- ADDITIVE_MODEL_RECOMMENDED 原则批准，但 **否决"给 StoryEvent 加 canonical 字段"的 Option B**（part / node_type / parent_id / previous_id / next_id 不进入 StoryEvent）；
- 批准方向：**新建平行 Canonical Story Layer**（CanonicalStoryNode → CanonicalStoryEventLink → StoryEvent），StoryEvent 语义保持不变；
- 第一版 canonical scope = **清河主章主线**；侠迹 / 镇守 / 奇遇 / 明暗故事为 secondary narrative branch，不进第一版主 spine；
- schema 1.2 / migration / 重冻结 v5：NO_GO（本阶段只设计，不实施）。
- 详细契约设计见 canonical-story-contract-v0.1.md。

## 1. 决策结论

### ADDITIVE_MODEL_RECOMMENDED

现有模型（Chapter / StoryEvent / StoryArc / StoryArcBeat / HistoricalContext 等）继续承担既有职责，不做破坏性改造；
**新增一条平行的"canonical story 层"（游戏原生任务骨架），以 additive 方式补充字段/实体**，并保留 arc→beat→event 作为"人工导读层"。

## 2. 为什么不是另外两个结论

### 不是 NO_SCHEMA_CHANGE_NEEDED（存在明确证据缺口）
- v5 JSON 的 event.part（"篇"切分）在导入 DB 时被静默丢弃（architecture reality summary #2）——说明 schema 1.1 即使有"篇"意图也没有落到持久层。
- 当前任何实体都没有 quest_id / node_type / parent / previous / next / region 字段（#1、#13）——无法表达"第一章·神仙不渡 → 篇 → 任务节点 → 子任务"层级。
- 10 个 beat 中 2 个无法唯一落到游戏任务节点（UNRESOLVED），27 个 event 中 5 个映射存疑（mapping §2/§3），且 20+ 个游戏原生节点（侠迹/镇守/奇遇/序章细节）在数据集中完全缺失（mapping §4）——"canonical story"没有可挂载的字段。
- Source 体系无法绑定到任务主体（SourceType.QUEST_REFERENCE 存在但 v5 零使用，#12）。

### 不是 CURRENT_MODEL_INSUFFICIENT
- 现有 arc/beat/event 完整支撑了产品当前的核心用例：人工编排导读（/story-arcs）、扁平事件时间线（/timeline）、人物剧情足迹（story_path）、历史对照卡、progress/spoiler 可见性闭包。
- 缺口是"缺少一层表达游戏原生结构"，而不是"现有层无法工作"。用 additive 层补齐即可，不需要推翻现有契约。

## 3. 建议的 additive 候选（仅提案，本任务不实施）

### 方案 A（推荐）：新增 Quest / QuestNode 实体层
- Quest（任务）：id / canonical_slug / chapter_id / region / quest_name（游戏内名称，如"神仙不渡"）/ quest_type（main_quest / side_quest 侠迹 / garrison 镇守 / encounter 奇遇 / hidden_line / prologue）/ parent_id（章→篇→节点）/ sort_order / previous_id / next_id / spoiler_level / visible_after_progress / status / source_ids。
- QuestNode（任务节点/子任务）：quest_id / node_type（segment / step / boss / plot_beat）/ title / summary / sort_order / parent_node_id / prev_next / event_id（nullable FK→story_events，非每个节点都有事件）。
- 挂载：StoryEvent 增加可空 quest_id 或 event_quests 关联表；保留 event 现有字段。
- 同时：把 event.part 持久化（或直接由 quest_id 派生），不再丢弃。

### 方案 B（更小改动）：StoryEvent 加 additive 列
- event 增加：quest_slug / quest_title / node_type（quest_segment / plot_node / lore_node）/ parent_event_id / previous_event_id / next_event_id / region。
- 优点：无新表、迁移小；缺点：表达不了"任务→子节点"层级与无事件节点（寻心/舞马人等），且 27 个事件覆盖不了全部任务节点。

### 与现有层的关系（两种方案一致）
- StoryArc / StoryArcBeat 不动：继续作为"人工导读层"。
- Canonical 层与导读层并行：beat 通过 event_id 关联 canonical 节点；后续可让"导读幕次 = canonical 节点 + 编辑文案"。
- Visibility/spoiler 机制复用：canonical 实体沿用 visible_after_progress + spoiler_level + status 三件套。

## 4. 数据准备（建议但不在本任务执行）
- 先把 inventory（docs/research/qinghe-canonical-story-inventory.md）中的 qh-* 节点作为 canonical 草稿，经 Lead 审核后再考虑是否进入 content contract 演化（届时才评估 schema 1.2 与重冻结）。
- 冲突项（§7 UNRESOLVED 清单）在进入 schema 前必须逐条消解或显式标记不可用。

## 5. 决策风险
- 若选择"先不改 schema，用现有 event 扩展内容"：会在 content 层继续混入任务结构语义，进一步加剧 beat/event 与任务边界的错位（如 beat 6/7 的 UNRESOLVED）。
- 若选择"直接重构模型"：破坏 Wave 1 冻结边界（G6），且当前数据量（27 事件）不足以支撑模型复杂度。
- ADDITIVE 方案的成本：一次 schema 1.2 + 迁移 + 数据集演化，收益：canonical story 首次可被程序化引用（deep link 升级、篇级进度、任务级剧透）。
