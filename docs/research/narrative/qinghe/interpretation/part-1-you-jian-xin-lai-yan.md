# 「又见新来燕」Deep-Dive Draft（M-04，claim-aware）

> 状态：DRAFT · 2026-08-23 · Mac
> 原则（Lead）：**可以写得深，但不能写得比证据更确定**；深度按 narrative density 分配，不要求每节点等长。
> 上游：main-story-inventory（canonical 节点）· hidden-story-inventory（暗线候选）· source-ledger（来源与 lineage）· unresolved-questions（UQ registry）

## 0. 写作方法

### 0.1 段落内部逻辑链

```text
事实 → 玩家当时看到什么 → 为什么发生 → 人物各自知道什么 → 人物为什么这么做 → 暗线怎样改变理解 → 后续回看会发现什么
```

### 0.2 Evidence tier（每个重要句子都归级）

| tier | 含义 |
| --- | --- |
| CANONICAL / STRONG FACT | 冻结 canonical 或 v5 已核验事实 |
| PUBLIC_SUPPORTED | 公开资料（含 lineage 一致的页面）支持 |
| COMMUNITY_INTERPRETATION | 社区解读（小黑盒/17173/nga 等） |
| RETROSPECTIVE_INFERENCE | 回头看才成立的推断（明确标注推断） |
| SOURCE_CONFLICT | 来源冲突 |
| UNRESOLVED | 无来源/待核 |

### 0.3 TODO 分类（Windows 静态/人工验证接口）

```text
TODO: NEED_NATIVE_TITLE            # 游戏内精确标题/任务名
TODO: NEED_ORDER_EVIDENCE          # 顺序/前置证据
TODO: NEED_CHARACTER_IDENTITY      # 人物身份确认
TODO: NEED_MOTIVATION_EVIDENCE     # 动机证据
TODO: NEED_HIDDEN_THREAD_EVIDENCE  # 暗线/伏笔证据
TODO: NEED_ALIAS_PROVENANCE        # 称谓出处
TODO: SOURCE_CONFLICT              # 来源冲突待裁决
```

---

## 1. 篇一总览（arc frame）

- 位置：canonical `wwm:qinghe:chapter-1:part-1`，5 个 main_quest（顺序 = canonical sort_order）。
- 弧线（CANONICAL 顺序 + PUBLIC_SUPPORTED 步骤）：**被动醒来 → 轻装启程（断桥）→ 学技（北竹林）→ 遇引路人（百草野）→ 立足收束（将军祠）**。
- 篇一核心问题（项目 beat 文案，EDITORIAL）：失玉 → 寻人/寻物双线启动。

## 2. 竹林旧居醒来（深度：高）

### L1 发生了什么（CANONICAL / PUBLIC_SUPPORTED）
- 红线唤醒主角；主角在竹林旧居查找线索，发现罐中信与灵位，得知养父江叔曾召唤自己（v5 evt-p1-awaken，PUBLIC_SUPPORTED ali213/9game）。
- 事件外框：黑衣人袭击夺玉在先（canonical 序章段，v5 evt-prologue-attack）。

### L2 为什么发生（UNRESOLVED 为主）
- 袭击者动机、江叔为何缺席、信/灵位为何此刻才被发现 —— 均无直接来源。**UNRESOLVED**。

### L3 人物状态与信息差（claim-aware）
- 主角：刚失去玉佩、得知江叔召唤 → 目标确立"寻江叔"（PUBLIC_SUPPORTED）。
- 红线：比主角更早到现场、未看见袭击者（v5 summary，CANONICAL）；红线对江叔/竹林了解多少 —— **UNRESOLVED**。
- 江叔：不在场、留信与灵位 —— 其去向与意图 **UNRESOLVED**（NEED_MOTIVATION_EVIDENCE）。

### L4 明潮 ↔ 暗涌（hypothesis，HIGH-CANDIDATE）
- HC-01：竹林旧居为江晏安置之所，与江晏前史/绣金楼追索相关（RETROSPECTIVE_INFERENCE，待 W 证据）。
- 袭击者只夺玉不取命（v5，CANONICAL）→ 玉佩（镇冠珏）价值高于主角性命 → 与身世暗线接驳（COMMUNITY_INTERPRETATION 候选）。

### L5 伏笔与回看（conservative）
- FIRST_PLAY_READABLE：信与灵位给出寻人目标（CANONICAL）。
- RETROSPECTIVE：竹林旧居是"被保护童年"的象征，日后与身世/绣金楼回看（RETROSPECTIVE_INFERENCE）。

### L6 历史/社区
- 无历史对照；社区多聚焦"江叔去哪了"猜测（COMMUNITY_INTERPRETATION，不入事实层）。

### TODO
- NEED_NATIVE_TITLE（本段在任务簿中的原生标题）
- NEED_MOTIVATION_EVIDENCE（袭击者动机、江叔缺席）
- NEED_CHARACTER_IDENTITY（红线与江叔的已知/未知边界）

## 3. 断桥（深度：低 — 判定为 gameplay transition + 轻叙事纹理）

- **判定（M-04 重要示例）**：断桥本质是**教学/位移节点**（轻功过桥），叙事密度低；不为六层模板硬写六层。
- 唯一轻叙事纹理（PUBLIC_SUPPORTED，sohu）：红线蹦跳先行、桥应声而断 → 呼应红线性格与二人关系（轻量 CHARACTER beat）。
- 若 W 证据显示桥段有隐藏设计（如断桥=江晏旧径），再升级深度；当前 **UNRESOLVED**。
- TODO：NEED_NATIVE_TITLE；NEED_HIDDEN_THREAD_EVIDENCE（若有暗线设计）。

## 4. 北竹林学射（深度：中）

### 人物首次进入：冯继升（PUBLIC_SUPPORTED）
- 射落白鸟之人 → 赠射术心得 → 邀箭术比试（ali213 步骤 8-10；9game 一致）。
- **名字写法 SOURCE_CONFLICT**：冯继升（bilibili/9game）vs 冯继生（ali213 步骤文本）→ TODO: SOURCE_CONFLICT / NEED_NATIVE_TITLE。

### 教学 vs 叙事（assessment）
- 本段主要承担**射箭教学**（战斗 tutorial）+ 轻微世界观（"北竹林界碑"地名）；是否暗示冯继升后续回收 —— **UNRESOLVED**（NEED_HIDDEN_THREAD_EVIDENCE，回看无证据）。

### L3（轻量）
- 冯继升对主角：陌生善意/补偿（射落白鸟"赔罪"）；其动机仅为局部 —— UNRESOLVED。
- 玩家第一遍：把冯继升当作"教你射箭的人"，不会记住为关键人物（COMMUNITY 常识，非事实）。

### TODO
- SOURCE_CONFLICT（人名）；NEED_CHARACTER_IDENTITY（冯继升在后续章节是否回收）；NEED_NATIVE_TITLE。

## 5. 百草野遇天涯客（深度：高 — 篇一最有研究价值的节点）

### 两个来源，可能指向同一叙事位置（不合并，写清楚）
- 游戏内：**天涯客** 在百草野给清河舆图、可兑换道具（PUBLIC_SUPPORTED，ali213/9game/v5）。
- 官方访谈（SRC-YYSLCN-NARRATIVE-INTERVIEW）：清河主线"**神秘的江湖人**"改变少年人生。
- 候选对应（HIGH-CANDIDATE）：天涯客 ↔ 神秘的江湖人。**不提前合并**；需要 Windows 确认该 NPC 在剧情中的命名与叙事角色（NEED_CHARACTER_IDENTITY / NEED_NATIVE_TITLE）。

### L1（PUBLIC_SUPPORTED）
- 天涯客赠舆图（世界/地图引入）→ 驱熊 → 偷师"太极"奇术 → 宝箱（ali213 步骤 11-14）。

### L2/L3
- 天涯客为何关注主角、其身份（流浪者？暗线推手？）—— **UNRESOLVED**（NEED_MOTIVATION_EVIDENCE / NEED_CHARACTER_IDENTITY）。
- 玩家第一遍：把天涯客当"给地图的 NPC"；回看时若=江湖人，则其出现是"改变人生"的关键入口（RETROSPECTIVE_INFERENCE）。

### L4（hypothesis，HIGH-CANDIDATE）
- HC-02：天涯客若为暗线引线，则篇一"遇引路人"同时是明潮推进与暗涌入口（与官方"江湖人"叙事位置重叠）→ 待 W 证据。

### L6
- 无历史对照；社区对天涯客身份讨论有限（COMMUNITY_INTERPRETATION 弱）。

### TODO
- NEED_CHARACTER_IDENTITY（天涯客身份与后续出现）；NEED_NATIVE_TITLE；NEED_HIDDEN_THREAD_EVIDENCE（HC-02 判定）。

## 6. 将军祠擂台（深度：高 — arc-level）

### 篇一收束（CANONICAL + PUBLIC_SUPPORTED）
- 将军祠擂台：方旭参与擂台 → 老金（听风辨位、手套、外观）→ 与红线、广胡子对话收尾（ali213 步骤 15-19）。
- beat-p1-arena（EDITORIAL，v5）：主角"凭自己能力被清河认识"，建立名声与关系网。

### arc-level interpretation（EDITORIAL / RETROSPECTIVE 明确标注）
- 角色弧：从"被动醒来、被袭击的少年"到"主动上擂台、赢得认可" → 篇一完成**立足**；这是"离开被保护童年"的第一步。
- 下一篇衔接（canonical order）：匹马映林嘶"回家寻亲"（回神仙渡/不羡仙）——立足后才有能力面对"家"的复杂（RETROSPECTIVE_INFERENCE，编辑视角）。

### L3（轻量）
- 方旭/老金动机：擂台组织者/商人 —— UNRESOLVED（NEED_MOTIVATION_EVIDENCE 低优先）。

### TODO
- NEED_NATIVE_TITLE（擂台段任务内标题）；NEED_MOTIVATION_EVIDENCE（方旭/老金，低优先）。

---

## 7. 跨节点回看与伏笔候选（conservative）

| 伏笔候选 | 出现节点 | 类型 | 状态 |
| --- | --- | --- | --- |
| 镇冠珏（玉佩） | 竹林旧居（袭击） | RETROSPECTIVE（身世/绣金楼） | CANONICAL 物件；意义 HIGH-CANDIDATE |
| 江叔的召唤（信/灵位） | 竹林旧居 | FIRST_PLAY_READABLE | CANONICAL |
| 红线"没看见袭击者" | 竹林旧居 | RETROSPECTIVE（红线所知边界） | CANONICAL 表述；解读 UNRESOLVED |
| 天涯客=江湖人 | 百草野 | RETROSPECTIVE | HIGH-CANDIDATE / W-VERIFY |

## 8. TODO 汇总（按分类，供 Windows 静态/人工路线关闭）

| TODO | 节点 | 静态路线可能关闭？ |
| --- | --- | --- |
| NEED_NATIVE_TITLE（篇一段落原生标题） | 全篇 | 是（localization/metadata） |
| NEED_CHARACTER_IDENTITY（天涯客/冯继升） | 百草野/北竹林 | 是（quest 表） |
| NEED_MOTIVATION_EVIDENCE（袭击者/江叔缺席） | 竹林旧居 | 否（需叙事） |
| NEED_HIDDEN_THREAD_EVIDENCE（断桥暗线/天涯客引线） | 断桥/百草野 | 部分（资源名可能提示） |
| SOURCE_CONFLICT（冯继升/冯继生） | 北竹林 | 是（native 文本） |
| NEED_ALIAS_PROVENANCE（少东家/寒姨/江叔官方文本） | 篇外 | 是（native 文本） |

> 每一条在 Windows W-R04/R05 静态探测后重新评估；静态拿不到且阻塞 E1 的才回退 W-01 人工采集。
