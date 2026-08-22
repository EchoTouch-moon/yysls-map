# Canonical Story Contract v0.1（设计草案，未实施）

> 阶段：Wave 1.5 / Phase C1 — Canonical Story Contract Design
> 状态：**DESIGN ONLY**。不实施 migration、不改 ORM、不改 contracts/schema、不重冻结 v5。
> 依据：docs/CANONICAL_STORY_ALIGNMENT_PLAN.md（Phase C 候选概念模型）；canonical-story-contract-decision.md（Lead 决议）；qinghe-canonical-story-inventory.md / qinghe-current-to-canonical-mapping.md（A/B 研究）。
> Lead 决议（2026-08-22）：ADDITIVE_MODEL_RECOMMENDED 原则批准；**否决给 StoryEvent 加 canonical 字段**；批准平行 Canonical Story Layer；第一版 scope = 清河主章主线。

## 0. 设计目标

1. 用一层独立实体表达「游戏原生故事结构」，与现有 Interpretation 层（StoryEvent / StoryArcBeat / Character / Relationship / HistoricalContext）解耦。
2. 第一版只保证「第一章·神仙不渡 → 四篇 → 主线剧情节点」backbone 可表达；侠迹/镇守/奇遇/明暗故事作为 secondary narrative branch，不进第一版主 spine。
3. 现有 StoryEvent / StoryArcBeat 语义零改动；canonical 层全部 additive。

## 1. 概念模型

### 1.1 CanonicalStoryNode（候选字段逐个论证）

| 字段 | 必要性论证 | v1 决策 |
| --- | --- | --- |
| canonical_id（stable internal id） | 必须：deep-link 锚点、跨层引用（link 表外键）、导入幂等、与 dataset 冻结解耦。形如 csn-qh-ch1 / csn-qh-part1-arena | 必填，slug 风格 |
| game_id（optional game/native id） | 可选：仅在来源可靠时保存（alignment plan §Phase C）；v1 中多数游戏内 id 未知 | 可空；未知不填 |
| title | 必须：展示名。但"未确认的游戏内名称"与"已核验名称"必须分离（见 §4.5） | 必填 + title_verified |
| node_type | 必须：taxonomy（见 §3） | 必填，枚举 |
| region | 必须：第一版 = 清河；用于筛选/显示 | 必填 |
| chapter | 必须：挂到现有 chapter 语义（qinghe）。v1 用 chapter_slug 文本引用，不强加 DB FK，保持层间解耦 | 必填（slug 引用） |
| parent_id | 必须：章→篇→节点层级是 visibility parent-chain 与顺序推导的根（C4/C8） | 必填（根节点为空） |
| sort_order | 必须：同级排序；previous/next 由它派生（§2.3） | 必填（同 parent 内唯一） |
| previous / next | 不显式存储（§2.3） | 派生 |
| provenance | 必须：多来源、可追踪（C2；§2.5） | 必填（列表） |
| confidence / verification_state | 必须：吸收 A/B 研究的 HIGH/MEDIUM/LOW/UNRESOLVED + Lead 的 SOURCE_CONFLICT / TEMPORAL_WORDING_REVIEW / PROVISIONAL_GROUP | 必填 |
| status | 必须：canonical 层独立发布管线（draft/published/archived），不依赖 v5 冻结 | 必填 |

### 1.2 CanonicalStoryEventLink（node ↔ StoryEvent 映射）

| 字段 | 说明 |
| --- | --- |
| id | 稳定 id |
| canonical_node_id | FK → CanonicalStoryNode |
| story_event_id | FK → StoryEvent（现有表，不改动） |
| link_type | EXACT / MERGED / SPLIT / EDITORIAL_ONLY（正式层）；UNRESOLVED 关联只存在于 research 层（pending_link），不写入 published canonical 层 |
| sort_order | 同一 node 挂多个 event 时的次序（未来多个 interpretation event 用） |
| is_primary | 同 node 多 event 时标记主事件（默认 EXACT 首个为 true） |
| note | 编辑说明（如 MERGED 时说明覆盖了哪些原生子节点） |

### 1.3 分层关系（与 Lead 建议一致）

```text
CanonicalStoryNode (canonical 层：游戏事实坐标)
        │ 1:N（M:N 经 link 表）
        ▼
CanonicalStoryEventLink  ←── link_type: EXACT/MERGED/SPLIT/EDITORIAL_ONLY
        │
        ▼
StoryEvent（解释层：我们对这段剧情的总结）
        ├── StoryArcBeat（解释层：为什么选它、怎么解释）
        ├── Character / Relationship / HistoricalContext（挂载）
```

## 2. 六个重点问题的回答

### Q1 为什么 canonical node 不应直接等同于 StoryEvent？
职责分离（Lead 三职责）：
- CanonicalStoryNode 回答「游戏里到底是什么」；StoryEvent 回答「我们把这里发生的事情总结成什么事件」；StoryArcBeat 回答「为了让玩家理解，我们为什么选它、怎么解释它」。
证据（A/B 研究）：
- MERGED：evt-p2-reunion 一个事件覆盖「寒姨重逢」与「瓷窑/地下仓库」两个原生子节点；
- EDITORIAL_ONLY：evt-wangqing-battle（中渡桥之战）是项目历史—作品对照节点，游戏无同名任务；
- MISSING：寻心 BOSS、舞马人 BOSS、朱八碗等原生节点在当前数据集没有事件；
- 跨任务边界：evt-p2-hospital 横跨 qh-02e / qh-02f（可能还涉及 PROVISIONAL_GROUP 的神仙不渡段）。
若 node=event，canonical 顺序会被迫跟随当前 chapter+sort_order 的压平顺序，编辑节点会污染坐标层（C4 违反）。

### Q2 N:M 是否真的需要？
需要（M:N link 表）：
- event 侧多 link：一个 event 可映射多个 node（SPLIT、跨边界事件）——evt-p2-hospital、evt-p2-reunion 均属此类；
- node 侧多 event：一个 canonical node 未来可挂多个 interpretation event（Wave 2 人工人物线等）。
v1 最小化：link 表 + is_primary；约束：同一 (node, event) 唯一；EXACT 节点至少 1 条 link。

### Q3 previous/next 应显式存储还是由 hierarchy/order 派生？
**派生**。单一事实源 = (parent_id, sort_order) 层级序；显式 prev/next 会造成双写不一致（重排时必须同步两个字段，易漏）。
例外：非树形流（跨篇跳转、PROVISIONAL_GROUP 占位）需要可选字段 game_order_hint 记录攻略观察顺序，仅供研究层，不参与正式顺序推导。

### Q4 part 是否应成为独立 node，而不是 StoryEvent 一个整数？
**是**。篇 = MAIN_PART node（篇一~篇四），是 canonical 层正式一级；若未来恢复 event.part，应引用 MAIN_PART node id，而不是独立整数。
现状：event.part 在导入时被静默丢弃（architecture reality #2）；v1 canonical 层以 MAIN_PART node 表达「篇」，不再依赖 StoryEvent.part。

### Q5 provenance 应如何支持 multiple sources？
node.provenance = 列表：
- source_kind：official / walkthrough / wiki / player / in_game（对应 alignment plan Level 1–2）；
- ref：URL 或游戏内观测记录标识；
- locator / accessed_at；
- evidence_role：identity（名称）/ order（顺序）/ hierarchy（层级）/ type（类型）；
- note。
多来源并存、不合并投票；identity 至少 1 条来源；order/hierarchy 冲突 → verification_state = source_conflict（不取多数，Lead 决策 2 原则）。
与现有 Source 表的关系：v1 不强绑 FK（现有 Source 只能绑定 chapter/faction/character/event/relationship）；未来可扩展 source subject 到 canonical node。

### Q6 未确认游戏名称如何表示而不污染 published canonical data？
title 与核验分离：
- node.title（展示名，可带「待考」标记）；
- node.title_verified: bool（false 时该节点 status 不得为 published，或投影时强制显示「待考」）；
- node.title_variants: [{text, source}]（并列变体，如 又见新来燕 / 又见新燕来——不合并、不投票）。
published canonical 数据只含 title_verified=true 的节点；未确认名称节点留在 research/draft 层。

## 3. Node Taxonomy

### v1（主线 backbone 必达）
| node_type | 示例 | 说明 |
| --- | --- | --- |
| CHAPTER | 第一章·神仙不渡 | 区域/章节级 |
| MAIN_PART | 篇一·又见新来燕 | 主线的篇（对应「四篇」） |
| MAIN_QUEST / STORY_NODE | 将军祠擂台、酒香塔击败千夜 | 篇内主线剧情节点 |

### research-only（不进正式层）
| node_type | 示例 | 说明 |
| --- | --- | --- |
| PROVISIONAL_GROUP | 神仙不渡城镇段 | Lead 决策 1：来源对任务边界不一致，不升格；进入条件：游戏内任务簿观察 / 明确任务目录 / 第二个独立可信来源 |

### 未来类型：扩展同一 taxonomy，还是另一类 branch？
**决策：同一 taxonomy 扩展枚举值 + 新增 spine / branch_kind 属性**。
- JIANGHU_LEGACY（侠迹）/ ENCOUNTER（奇遇）/ SIDE_STORY（明暗故事）/ STRONGHOLD（镇守）/ BOSS：都是「游戏内可定位节点」，只是展示归属不同；
- 用 spine: main | secondary 控制第一版 UI 只渲染 main spine；侠迹/暗线作为 secondary branch 挂在相邻主线节点旁（对齐 UX 提案图）；
- 不引入第二套 taxonomy：避免「任务类型」与「展示层级」两套系统纠缠（保持 C4 单一分层语义）。

## 4. 数据生命周期与质量

- verification_state：verified / provisional / source_conflict / temporal_wording_review（吸收 Lead 三个新标签；provisional 含 PROVISIONAL_GROUP 语义）；
- confidence：HIGH / MEDIUM / LOW / UNRESOLVED（沿用 inventory 约定）；
- status：draft / published / archived（canonical 层独立发布管线，与 v5 dataset 冻结解耦）；
- 未确认名称：见 Q6；红线/伊刀之死：verification_state=source_conflict，不设计分支（Lead 决策 2）。

## 5. Mapping Simulation（纯文档示例，不改数据库）

用 4 个示例证明：新 canonical 层不会强迫现有 StoryEvent 改语义。

### 5.1 EXACT —— 将军祠擂台
```text
CanonicalStoryNode:
  canonical_id: csn-qh-part1-arena
  title: 将军祠擂台            title_verified: true
  node_type: STORY_NODE       parent: csn-qh-part1   sort_order: 5
  provenance: [{walkthrough, app.ali213.net/gl/1599605.html, 第1页步骤15-19, order+identity}]
  confidence: HIGH            verification_state: verified

CanonicalStoryEventLink:
  node: csn-qh-part1-arena  event: evt-p1-arena  link_type: EXACT  is_primary: true
```
现有 StoryEvent 零改动：evt-p1-arena 仍是它自己，只是多了一条指向 canonical 节点的关联。

### 5.2 MERGED —— 寒姨重逢 + 瓷窑/地下仓库
```text
CanonicalStoryNode A:
  canonical_id: csn-qh-part2-reunion     title: 不羡仙与寒姨重逢    node_type: STORY_NODE  sort_order: 1
CanonicalStoryNode B:
  canonical_id: csn-qh-part2-cisheng     title: 瓷窑与地下仓库（瘦老弟/伊刀）  node_type: STORY_NODE  sort_order: 2

CanonicalStoryEventLink:
  (A, evt-p2-reunion, MERGED, note=事件同时覆盖B的原生内容, is_primary=true)
  (B, evt-p2-reunion, MERGED, note=同一事件的另一覆盖面, is_primary=false)
```
一个事件两条 MERGED link——演示 event 侧 M:N 与 MERGED 语义；StoryEvent 无需拆分。

### 5.3 EDITORIAL_ONLY —— 中渡桥之战
```text
CanonicalStoryNode（章节级挂载点）:
  canonical_id: csn-qh-ch1  title: 第一章·神仙不渡  node_type: CHAPTER

CanonicalStoryEventLink:
  (csn-qh-ch1, evt-wangqing-battle, EDITORIAL_ONLY,
   note=历史-作品对照节点，无游戏原生任务锚点；仅挂载于章节解释上下文)
```
EDITORIAL_ONLY 明确该事件不参与 canonical 顺序推导；不为其伪造 canonical node。

### 5.4 unresolved / provisional —— 神仙不渡城镇段 + 揭穿胡为
```text
research 层（不写入 published canonical）:
  pending_node: PROVISIONAL_GROUP「神仙不渡城镇段」
    verification_state: provisional（进入条件未满足：无游戏内任务簿观察/明确目录/第二独立来源）
  pending_link: (pending_node, evt-p1-chouyuehai, UNRESOLVED, note=攻略置于神仙不渡段，v5 归入篇一)
```
正式 canonical 层不含该节点；evt-p1-chouyuehai 在 canonical 层暂不挂任何 link（UNRESOLVED）。

## 6. Migration Impact Assessment（只列影响，不实施）

| 面 | 影响 | additive? | 触碰 frozen contract? |
| --- | --- | --- | --- |
| ORM（models.py） | 新增 CanonicalStoryNode + CanonicalStoryEventLink 两个模型及关系；现有表零改动 | ✅ | 否 |
| Alembic | 新增 1 个迁移（create canonical tables）；历史迁移链不动 | ✅ | 否 |
| import contract（content_import） | 新增 canonical 数据解析（独立通道）；EventItem.part 维持现状（不持久化，不语义化——语义化会改 dataset contract，NO_GO） | ✅ | 否（独立 canonical dataset） |
| API projection | 新增只读 /canonical-story 端点；/timeline、/story-arcs 不动（Phase D 再议） | ✅ | 否 |
| Timeline UI | 本阶段不动；Phase D 连续滚动以 canonical 顺序驱动 | ✅（未来） | 否 |
| character story_path | 未来改为从 canonical node 派生人物出现轨迹（alignment plan §3）；本阶段不动 | ✅（未来） | 否 |
| deep link | 未来新增 /timeline?node={canonical_slug}；现有 /timeline?beat= 保留（C7） | ✅（未来） | 否 |
| v5 migration / re-freeze | **不重冻结 v5**；canonical 数据作为独立数据集（如 yysls-qinghe-canonical-v0.1.json + 独立 sha256）导入 | ✅ | 否 |
| StoryEvent 加列（part/node_type/parent_id/previous_id/next_id） | 已由 Lead 否决（Option B） | — | — |

结论：Phase C1 设计的全部影响均为 additive；唯一会改变 frozen contract 的路径（StoryEvent 字段扩展 / event.part 语义化）已被否决或推迟。

## 7. 与 alignment plan 验收门的对应

- C1（Canonical Coverage）/ C2（Provenance）/ C3（Mapping Closure）/ C4（Layer Separation）/ C9（Contract Discipline）/ C10（Acquisition Decision）由本阶段设计 + thin slice 支撑；
- C5–C8（连续阅读 / Game Alignment / Deep-link / Visibility Closure）属 Phase D 实施验收，本阶段不触碰；
- C10：公开资料覆盖缺口已记录（inventory §7），本地游戏资源研究暂无必要（无决定性证据，inventory §9 feasibility note）。
