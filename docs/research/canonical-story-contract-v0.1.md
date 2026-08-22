# Canonical Story Contract v0.1 — rev 2（C1.1 修正后；设计草案，未实施）

> 阶段：Wave 1.5 / Phase C1.1 — Contract Repair（Lead: APPROVED_WITH_CHANGES）
> 状态：**DESIGN ONLY**。不实施 migration、不改 ORM、不改 contracts/schema、不重冻结 v5。
> 修订：rev 1（Phase C1 初稿，commit 1d7b658）→ rev 2（本版，应用 Lead C1.1 全部修正）。
> Lead 决议：Phase C1 COMPLETE / CONTRACT_REPAIR_REQUIRED；C2 Migration WAITING_FOR_FREEZE。

## 0. C1.1 修订记录（相对 rev 1）

1. **mapping_kind = EXACT / MERGED / SPLIT**，从 link 枚举移除 EDITORIAL_ONLY；
2. **EDITORIAL_ONLY 不再是 link type**：定义为「该 StoryEvent 在 canonical 层无任何 link」的审计状态（派生，不存储；不产生假 node、不允许 node_id=NULL）；
3. **EXACT / MERGED / SPLIT 定义 cardinality invariant**（机器可校验，见 §1.2.1）；
4. **provenance 保持 node 级 JSON + evidence_role 强枚举**（不新增第三张 evidence 表；未来数据规模上升再评估）；
5. **移除 title_verified boolean**，统一由 verification_state（VERIFIED / PROVISIONAL / SOURCE_CONFLICT / UNRESOLVED）表达；
6. **id / canonical_key / native_id 三者分离**（DB 内部 UUID / 项目稳定 key / 可选游戏原生 id）；
7. **taxonomy 统一为 MAIN_QUEST**（不再用 MAIN_QUEST=STORY_NODE 双名）；PROVISIONAL_GROUP 仅 research 层，不进 DB enum；
8. Freeze gates C1-G1..C1-G6 明确对应（§7）。

## 1. 概念模型

### 1.1 CanonicalStoryNode（字段逐个论证，rev 2）

| 字段 | 必要性论证 | v1 决策 |
| --- | --- | --- |
| id | DB 内部主键（UUID），纯存储身份 | 必填（内部） |
| canonical_key | 项目自维护的稳定 key（如 wwm:qinghe:chapter-1:part-1）：deep-link 锚点、导入幂等、跨层引用；**不与游戏原生 id 混用** | 必填，唯一，slug 风格 |
| native_id | 可选：游戏原生 id，仅当来源可靠时保存（alignment plan：optional game id 仅在来源可靠时保存）；v1 中多数未知 | 可空；未知不填 |
| title | 展示名。未核验名称由 verification_state 门控（§1.4），不发布 | 必填 |
| node_type | CHAPTER / MAIN_PART / MAIN_QUEST（v1，单一命名）；未来扩展见 §3 | 必填，枚举 |
| region / chapter | 第一版 = 清河 / qinghe；用于筛选与显示。v1 用 chapter_slug 文本引用，不强加 FK | 必填 |
| parent_id | 层级根（visibility parent-chain 与顺序推导的根；C4/C8） | 必填（根节点为空） |
| sort_order | 同级排序；previous/next 由它派生（Lead APPROVED：不存 previous_id/next_id） | 必填（同 parent 内唯一） |
| spine | MAIN / SECONDARY：第一版固定 MAIN；侠迹/奇遇/暗线等 secondary branch 未来用（Lead：合理） | v1 固定 MAIN |
| provenance | 多来源、可追踪（C2/G4；§1.3） | 必填（JSON 列表） |
| verification_state | VERIFIED / PROVISIONAL / SOURCE_CONFLICT / UNRESOLVED；**替代 rev 1 的 title_verified boolean**（Boolean 对研究型数据太粗） | 必填 |
| status | draft / published / archived；PROVISIONAL 与 UNRESOLVED 不得 published（G5） | 必填 |

### 1.2 CanonicalStoryEventLink（node ↔ StoryEvent 映射，rev 2）

| 字段 | 说明 |
| --- | --- |
| id | 稳定 id |
| canonical_node_id | FK → CanonicalStoryNode |
| story_event_id | FK → StoryEvent（现有表，不改动） |
| mapping_kind | **EXACT / MERGED / SPLIT**（正式 enum） |
| sort_order | 同 node 多 event 时的次序 |
| is_primary | 同 node 多 event 时标记主事件 |
| note | 编辑说明 |

约束：Unique (canonical_node_id, story_event_id)。

**EDITORIAL_ONLY 的处理（G2）**：
- EDITORIAL_ONLY 不是 mapping_kind。一个 StoryEvent 在 canonical 层**没有任何 link**，即为 editorial-only 事件（如 evt-wangqing-battle 中渡桥之战——项目历史/作品对照节点，无游戏原生锚点）。
- 禁止为此制造假 canonical node；禁止 node_id=NULL 的 link。
- 若未来需要显式查询 editorial-only 事件，在 StoryEvent 上做 projection/classification（不污染 canonical link 表）。
- 注意区分：Phase B 研究文档（inventory/mapping）中的 EDITORIAL_ONLY 是**映射状态词汇**（描述「当前内容 ↔ 原生节点」的研究结论）；本契约的 mapping_kind 是**数据库层枚举**。两者语义一致（editorial-only 即无原生锚点），但前者是研究标签、后者是数据约束。

### 1.2.1 Cardinality invariants（机器可校验，G3）

| mapping_kind | 语义 | 校验规则 |
| --- | --- | --- |
| EXACT | 1 canonical node ↔ 1 StoryEvent（当前事件基本对应这个游戏节点） | 该 event 恰有 1 条 link 且为 EXACT；该 node 恰有 1 条 link 且为 EXACT |
| MERGED | N canonical nodes → 1 StoryEvent（项目把多个游戏原生节点总结成一个事件） | 该 event 的 link 数 ≥ 2，且其全部 link 的 mapping_kind 均为 MERGED |
| SPLIT | 1 canonical node → N StoryEvents（项目为理解/表达将原生节点拆成多个事件） | 该 node 的 link 数 ≥ 2，且其全部 link 的 mapping_kind 均为 SPLIT |

一致性规则（validator 在 canonical import 阶段强制）：
- 一个 event 若含 EXACT link → 不得再有其他 link（EXACT 是 1:1）；
- 一个 node 若含 EXACT link → 不得再有其他 link；
- 一个 event 标记 MERGED → 至少 2 条 link，且全部为 MERGED（防止"Node A --MERGED--> Event X"只有一条的失真）；
- 一个 node 标记 SPLIT → 至少 2 条 link，且全部为 SPLIT；
- 违反上述任一规则 → 拒绝导入（import validation error）。

### 1.3 Provenance（node 级 JSON + evidence_role 强枚举，G4）

- 存储：node.provenance = JSON 数组（v1 不新增第三张 evidence 表；规模上升再评估）。
- 每条：{ source_kind, ref, locator, accessed_at, evidence_role, note }。
- **evidence_role 正式枚举**（回答"哪个来源支持哪个字段"）：
  | evidence_role | 含义 |
  | --- | --- |
  | IDENTITY | 证明「该节点存在 / 与另一来源指向同一节点」 |
  | TITLE | 证明名称（含变体） |
  | HIERARCHY | 证明 parent 关系 |
  | ORDER | 证明顺序 / sort_order |
  | TYPE | 证明 node_type |
  | GAME_ID | 证明 native_id |
  | GENERAL | 综合/兜底 |
- 规则：
  - 同一 node 的多个来源按 evidence_role 归位；字段级证据冲突 → verification_state = SOURCE_CONFLICT（不投票、不取多数）；
  - 至少 1 条 IDENTITY 或 GENERAL 来源（C2：每个 canonical 节点至少一条可追踪来源）；
  - title 冲突（如 又见新来燕/又见新燕来）→ title 保留变体记录于 provenance（TITLE 角色）+ verification_state = SOURCE_CONFLICT。

### 1.4 分层关系（与 Lead 建议一致；EDITORIAL_ONLY 事件无 link）

```text
CanonicalStoryNode (canonical 层：游戏事实坐标)
        │ 1:N（经 link 表；M:N 语义由 mapping_kind + invariants 约束）
        ▼
CanonicalStoryEventLink  ←── mapping_kind: EXACT / MERGED / SPLIT
        │
        ▼
StoryEvent（解释层：我们对这段剧情的总结）
        ├── StoryArcBeat（解释层：为什么选它、怎么解释）
        ├── Character / Relationship / HistoricalContext（挂载）

Editorial-only StoryEvent（如 evt-wangqing-battle）＝ 无任何 canonical link（审计状态，不产生记录）
```

## 2. 六个重点问题（rev 2 更新）

1. **为什么 canonical node 不应直接等同于 StoryEvent？** 职责分离（node=游戏事实坐标；event=我们对剧情的总结；beat=为什么选它/怎么解释）。证据：MERGED（evt-p2-reunion 跨两个原生子节点）、SPLIT（未来 1 node → N events）、MISSING（寻心/舞马人无事件）、跨任务边界（evt-p2-hospital）。**EDITORIAL_ONLY 事件（evt-wangqing-battle）无原生锚点 → 不产生 link**，不能为了挂它而造假 node。
2. **N:M 是否真的需要？** 需要（M:N link 表）：event 侧多 link（MERGED/SPLIT/跨边界）、node 侧多 event（未来 interpretation）。v1 用 mapping_kind + §1.2.1 invariants 约束，防止语义失真。
3. **previous/next 存储还是派生？** **派生**（Lead APPROVED）：单一事实源 = (parent_id, sort_order)。不存 previous_id/next_id（避免三份状态不一致）。未来非线性分支再单独建 StoryEdge/CanonicalTransition，不提前设计。
4. **part 是否应成为独立 node？** **是**：篇 = MAIN_PART node；event.part（若未来恢复）应引用 MAIN_PART node 而非独立整数。现状 event.part 导入时被丢弃；v1 canonical 层以 MAIN_PART node 表达「篇」。
5. **provenance 如何支持 multiple sources？** node 级 JSON + evidence_role 强枚举（§1.3）；每个来源声明支持哪个字段；冲突不投票不取多数 → SOURCE_CONFLICT。
6. **未确认游戏名称如何表示而不污染 published canonical data？** verification_state（VERIFIED/PROVISIONAL/SOURCE_CONFLICT/UNRESOLVED）门控 + provenance TITLE 角色记录变体；**非 VERIFIED 节点 status 不得为 published**（G5）；不使用 boolean。

## 3. Node Taxonomy（rev 2）

### v1（主线 backbone 必达，单一命名）
| node_type | 示例 | 说明 |
| --- | --- | --- |
| CHAPTER | 第一章·神仙不渡 | 区域/章节级 |
| MAIN_PART | 篇一·又见新来燕 | 主线的篇（「四篇」） |
| MAIN_QUEST | 将军祠擂台、酒香塔击败千夜、序章 | 主线剧情节点（统一名字，不再用 STORY_NODE 别名） |

### research-only（不进 DB enum，G5）
| node_type | 示例 | 说明 |
| --- | --- | --- |
| PROVISIONAL_GROUP | 神仙不渡城镇段 | Lead 决策 1：来源对任务边界不一致，不升格；进入条件：游戏内任务簿观察 / 明确任务目录 / 第二个独立可信来源 |

### 未来类型：同一 taxonomy 扩展 + spine
- JIANGHU_LEGACY（侠迹）/ ENCOUNTER（奇遇）/ SIDE_STORY（明暗故事）/ STRONGHOLD（镇守）/ BOSS：**同一 taxonomy 扩展枚举值**，配合 spine: MAIN | SECONDARY 控制第一版 UI 只渲染 main spine；
- 不引入第二套 taxonomy（避免「任务类型」与「展示层级」两套系统纠缠）。

## 4. 数据生命周期与质量（rev 2）

- verification_state：**VERIFIED / PROVISIONAL / SOURCE_CONFLICT / UNRESOLVED**（canonical 层正式状态；Lead 决策 3 的 TEMPORAL_WORDING_REVIEW 属 research 层注记标签，不进入 canonical enum）；
- status：draft / published / archived；**PROVISIONAL_GROUP 与 UNRESOLVED 节点 status 不得为 published**（G5）；
- 红线/伊刀之死：verification_state = SOURCE_CONFLICT，不设计分支（Lead 决策 2）；
- editorial-only 事件：零 link → 审计分类，不进 canonical 查询投影。

## 5. Mapping Simulation（rev 2，纯文档示例，不改数据库）

### 5.1 EXACT —— 将军祠擂台（1:1）
```text
CanonicalStoryNode:
  canonical_key: wwm:qinghe:chapter-1:part-1:arena
  title: 将军祠擂台                verification_state: VERIFIED
  node_type: MAIN_QUEST           parent: (part-1)   sort_order: 5   spine: MAIN
  provenance: [{walkthrough, app.ali213.net/gl/1599605.html, 第1页步骤15-19, ORDER, ...},
               {walkthrough, 同上, IDENTITY, ...}]
CanonicalStoryEventLink:
  (node, evt-p1-arena, mapping_kind=EXACT, is_primary=true)
→ invariant: event 恰 1 条 link 且为 EXACT ✓；node 恰 1 条 link ✓
```

### 5.2 MERGED —— 寒姨重逢 + 瓷窑/地下仓库（N→1）
```text
Node A: wwm:qinghe:chapter-1:part-2:reunion    title: 不羡仙与寒姨重逢     MAIN_QUEST  sort_order: 1
Node B: wwm:qinghe:chapter-1:part-2:cisheng    title: 瓷窑与地下仓库（瘦老弟/伊刀）  MAIN_QUEST  sort_order: 2

CanonicalStoryEventLink:
  (A, evt-p2-reunion, MERGED, note=事件同时覆盖B的原生内容, is_primary=true)
  (B, evt-p2-reunion, MERGED, is_primary=false)
→ invariant: event 有 2 条 link 且全部 MERGED ✓
```

### 5.3 SPLIT —— 活人医馆/寒姨房刺杀（1→N，示意）
```text
Node: wwm:qinghe:chapter-1:part-2:hospital   title: 活人医馆与寒姨房刺杀  MAIN_QUEST
Event X: evt-p2-hospital（现有；医馆/弱水岸部分）
Event Y: <未来事件：寒姨房刺杀/伊刀段>（research 层 pending，v1 不创建）
CanonicalStoryEventLink（未来形态）:
  (hospital, X, SPLIT, is_primary=true)
  (hospital, Y, SPLIT, is_primary=false)
→ invariant: node 有 2 条 link 且全部 SPLIT ✓（本示例为形态演示；v1 中 evt-p2-hospital 归属仍 UNRESOLVED，不进正式层）
```

### 5.4 editorial-only audit —— 中渡桥之战（零 link）
```text
evt-wangqing-battle（作品中的中渡桥之战）：
  canonical 层：无任何 CanonicalStoryEventLink（没有对应游戏原生任务节点）
  → 审计分类：EDITORIAL_ONLY（派生，不存储；不产生假 node，不允许 node_id=NULL）
  → 该事件继续作为解释层内容存在（历史/作品对照），不参与 canonical 顺序推导
```

结论：新 canonical 层未强迫任何现有 StoryEvent 改语义；EDITORIAL_ONLY 事件保持零 link。

## 6. Migration Impact Assessment（rev 2，只列影响，不实施）

| 面 | 影响 | additive? | 触碰 frozen contract? |
| --- | --- | --- | --- |
| ORM（models.py） | 新增 CanonicalStoryNode + CanonicalStoryEventLink 两模型；现有表零改动 | ✅ | 否 |
| Alembic | 新增 1 个迁移（create canonical_story_nodes / canonical_story_event_links）；历史迁移链不动 | ✅ | 否 |
| import contract | 新增 canonical 数据解析（独立通道）；import validator 内置 §1.2.1 cardinality invariants；EventItem.part 维持现状（不持久化、不语义化——NO_GO） | ✅ | 否（独立 canonical dataset） |
| API projection | 新增只读 /canonical-story 端点；/timeline、/story-arcs 不动（Phase D 再议） | ✅ | 否 |
| Timeline UI | 本阶段不动；Phase D 连续滚动以 canonical 顺序驱动 | ✅（未来） | 否 |
| character story_path | 未来改为从 canonical node 派生人物出现轨迹（alignment plan §3）；本阶段不动 | ✅（未来） | 否 |
| deep link | 未来新增 /timeline?node={canonical_key}；现有 /timeline?beat= 保留（C7） | ✅（未来） | 否 |
| v5 migration / re-freeze | **不重冻结 v5**；canonical 数据独立数据集（yysls-qinghe-canonical-v0.1.json + 独立 sha256） | ✅ | 否 |

C2 目标形态（Lead 确认）：2 张新表（canonical_story_nodes / canonical_story_event_links），不碰 story_events / story_arcs / story_arc_beats / content/yysls-qinghe-v5.json。

## 7. Freeze Gates（C1-G1..C1-G6）对照

| Gate | 要求 | 本契约落实 |
| --- | --- | --- |
| C1-G1 | CanonicalStoryNode 不依赖 StoryEvent 存活 | node 无 FK 到 story_events；仅 link 表引用事件；native_id 可选 |
| C1-G2 | Editorial-only Event 不产生 canonical link | mapping_kind 无 EDITORIAL_ONLY；零 link 即 editorial-only；禁假 node / NULL node_id（§1.2） |
| C1-G3 | EXACT/MERGED/SPLIT cardinality 可机器校验 | §1.2.1 invariants + import validator |
| C1-G4 | provenance 说明"哪个来源支持什么" | evidence_role 枚举（IDENTITY/TITLE/HIERARCHY/ORDER/TYPE/GAME_ID/GENERAL，§1.3） |
| C1-G5 | provisional/unresolved 不伪装成 published canonical fact | verification_state 门控 + PROVISIONAL_GROUP 仅 research 层 + status 规则（§1.1/§4） |
| C1-G6 | thin slice 不要求改 v5 / StoryEvent / StoryArcBeat | thin slice v0.1（rev 2）全部通过 canonical 层表达，未触碰三者（§6） |
