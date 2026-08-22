# Wave 1.6 — Narrative Depth & Native Presentation

> Status: **GO / ACTIVE DIRECTION**  
> Updated: 2026-08-23  
> Baseline: Wave 1.5 Canonical Alignment + Continuous Timeline 已闭环，`Canonical Contract v0.1 rev2` 与 `yysls-qinghe-canonical-v0.1` 继续冻结。

## 1. 为什么进入 Wave 1.6

Wave 1.5 已解决最关键的结构错误：网站主阅读顺序不再由编辑层自己编排，而是由游戏原生 canonical spine 驱动。Player Validation 证明该方向正确，但同时暴露出新的核心问题：

1. 剧情解析深度明显不足，每个故事节点还有大量人物动机、因果、伏笔、暗线与历史背景可挖掘；
2. “完整事件”仍沿旧 StoryEvent 顺序展示，用户切换模式后会重新进入另一套叙事坐标；
3. 对游戏真实任务流程、明线/暗线结构、探索叙事的掌握仍不够完整，需要扩大资料采集，并评估本地资源 metadata 的可行性；
4. Canvas 仍有优化空间，但暂不进入本轮核心范围；
5. 当前视觉已经可用，但还没有充分对齐《燕云十六声》的原生审美与叙事气质；
6. 剧情正文中的人物需要 point-of-need recall：点击人物称谓即可快速唤起人物小卡，而不是强迫用户离开当前阅读流；
7. “少东家”“寒姨”“江叔”等官方/社区常用称谓应更自然地进入讲解，让产品语言更接近玩家社区，而不是第三方百科。

因此，Wave 1.6 不再以“继续增加功能”为目标，而以以下一句话为核心：

> **沿游戏原生故事结构，把《燕云十六声》的剧情讲得更深、更清楚、更像燕云，也更像玩家之间在讲燕云。**

---

## 2. 当前产品判断

### 2.1 已经成立的基础

以下内容继续视为冻结基础，不因 Wave 1.6 重开：

- Canonical 与 Interpretation 分层；
- `CanonicalStoryNode -> CanonicalStoryEventLink -> StoryEvent/Interpretation`；
- 清河第一章 canonical v0.1 main spine；
- canonical-first continuous Timeline；
- zero-link canonical node 合法；
- editorial-only event 不得重新进入主 spine；
- `?node=` 与旧 `?beat=` deep-link compatibility；
- spoiler/progress visibility closure；
- 来源、历史背景、人物与关系 overlay；
- exact-HEAD remote `verify` 作为正式工程验收证据。

### 2.2 尚未通过的产品验证

整体 Product Validation **NOT YET PASS**。当前不是工程可靠性问题，而是内容与呈现质量问题：

- Canonical alignment：方向正确；
- Narrative depth：不足；
- Native story coverage：不足；
- Reading model consistency：“完整事件”仍需要重定位；
- Native aesthetic alignment：不足；
- Player-language alignment：不足。

---

## 3. Wave 1.6 产品原则

### P1 — Canonical first，永远不倒退

游戏原生结构决定“发生在哪、顺序是什么、属于哪条故事线”。编辑层只负责解释，不得再次创造第二条权威剧情顺序。

### P2 — Depth before breadth

不要立刻把清河所有节点都写长。先挑一个范围做成最终质量样板，再扩展。

首个 deep-dive pilot：

> **第一章·神仙不渡 / 又见新来燕**

### P3 — 明潮负责前进，暗涌负责补真相

后续 Narrative Model 与 Reading UX 要能够表达：

```text
                    暗涌线索 A
                        ╲
明潮 A ─── 明潮 B ─── 明潮 C ─── 明潮 D
             ╲          ╲
              暗涌 B      暗涌 C
                 ╲        ╱
                  理解 / 真相
```

“明潮/暗涌”首先是叙事拓扑，不只是视觉皮肤。

### P4 — Point-of-need recall

人物解释尽量出现在用户需要回忆人物的瞬间。

目标交互：

- 正文中的人物称谓以虚线/点状下划线标识；
- Desktop：点击后 anchored popover/person card；
- Mobile：点击后 bottom sheet；
- 卡片只展示“此刻为了读懂这段剧情需要知道什么”，不替代完整人物页；
- 继续遵守 progress/spoiler gating。

### P5 — Community-native language, evidence-aware

允许在解释文案中使用玩家熟悉的称谓，但称谓本身需要分层：

- `OFFICIAL_ALIAS`：官方也使用；
- `COMMUNITY_COMMON`：玩家社区长期稳定使用；
- `COMMUNITY_MEME`：语境化梗称，只用于轻量说明，不进入 canonical fact。

“少东家”应优先作为主角的玩家友好称谓之一；其他角色称谓逐步建立 alias ledger。

### P6 — Evidence first

资料不足时显式保留 UNKNOWN / UNRESOLVED / SOURCE_CONFLICT，不因页面需要连贯就补猜测。

### P7 — Native aesthetic is information design

后续视觉不做简单“水墨换皮”。重点研究：

- 长卷与连续阅读；
- 明潮/暗涌的信息层级；
- 金线/墨线作为叙事连接；
- 宣纸、留白、雾、印章等视觉语法；
- 减少大块卡片感；
- 保持可访问性、阅读对比度和信息边界。

---

## 4. 剧情解析的目标深度

每一个高价值剧情段落至少按六层组织，而不是只有 summary + why-it-matters。

### L1 — 发生了什么

玩家回忆：谁、在哪里、做了什么、结果是什么。

### L2 — 为什么会发生

因果链：谁推动了事件、前置条件是什么、为什么此时发生。

### L3 — 人物动机与信息差

分别回答：

- 少东家此时知道什么；
- 关键人物知道什么；
- 谁在隐瞒；
- 谁在误导；
- 人物为什么作出当前选择。

### L4 — 明潮 ↔ 暗涌

把主线任务与探索中获得的碎片联系起来，包括但不限于：

- 明暗故事；
- 侠迹；
- 镇守；
- 奇遇；
- 万事知；
- 关键 NPC 环境对话；
- 道具、书信、记录等线索。

不是所有内容都必须进入正式产品，但研究层必须能标识它们与主线的关系。

### L5 — 伏笔与回看

区分：

- `FIRST_PLAY_READABLE`：第一次走到这里就能理解；
- `RETROSPECTIVE`：后续剧情发生后回头看才成立；
- `REVEAL_REQUIRED`：只有用户明确进入完整解析时才显示。

### L6 — 历史 / 推测 / 社区解读

明确区分作品事实、历史事实、可信对照、编辑推测、社区常见解释与争议观点。

---

## 5. “完整事件”的重新定位

当前“跟着故事读”已经 canonical-first，但“完整事件”仍是旧 StoryEvent inventory 的排序展示。Wave 1.6 明确：

> **产品不得长期保留两套互相竞争的剧情顺序。**

“完整事件”后续应重定位为资料/解析索引，而不是第二条 Timeline。候选命名：

- 事件档案；
- 剧情资料库；
- 全部剧情解析。

目标分类：

```text
剧情资料库
├── 已挂载到 canonical 明潮
├── 已定位的暗涌/探索解析
└── 尚未定位的 editorial-only 解析
```

正式改名与 UI 重构属于 E3，在 E0/E1/E2 完成前不抢跑。

---

## 6. 数据采集与研究范围

Wave 1.6 需要从“main quest backbone”扩大到“理解完整区域故事所需的研究 corpus”，但不等于一次性发布所有内容。

研究对象包括：

- CHAPTER / MAIN_PART / MAIN_QUEST；
- 游戏原生明潮；
- 游戏原生暗涌/明暗故事；
- 侠迹；
- 镇守；
- 奇遇；
- 万事知；
- 关键 NPC 对话上下文；
- 道具、书信、记录等叙事线索；
- 角色常用称谓；
- 任务前后关系与解锁关系。

每条观察应尽量按 evidence role 拆分：

`IDENTITY / TITLE / HIERARCHY / ORDER / PREREQUISITE / CHARACTER / HIDDEN_CLUE / MOTIVATION / FORESHADOWING / COMMUNITY_ALIAS / GENERAL`

---

## 7. 本地资源 / 解包策略

### 7.1 结论

Wave 1.6 **允许启动 Local Asset Feasibility Spike**，但不批准直接进入“完整解包工程”。

目标只是回答：公开资料 + 游戏内观察是否足够；若不足，安装目录中是否存在可合法、稳定读取的结构化 metadata。

### 7.2 调查顺序

1. 公开资料；
2. 自己的游戏内观察、截图和录像；
3. 本地安装目录的只读资源清单；
4. manifest/index/localization/structured table 可行性；
5. 只有前四步不足时，才评估最小 metadata extractor。

### 7.3 允许关注的 metadata

- quest/task ID；
- title/localization key；
- parent/chapter；
- prerequisite/unlock；
- order/category/region；
- 稳定引用标识。

### 7.4 禁止范围

- 不绕过加密、DRM 或访问控制；
- 不绕过、注入或对抗反作弊；
- 不做运行时内存注入/Hook；
- 不修改游戏文件；
- 不建设或发布完整对白、脚本、音频、CG、模型、原画资产数据库；
- raw screenshots/video 默认不提交 GitHub；GitHub 只保存必要的观察记录、哈希、元数据与研究结论。

发现必须突破以上边界才能继续时：**STOP / NO_GO**。

---

## 8. 双机工作模型

### Mac — Research / Product Hub

负责：

- 公共资料研究；
- evidence reconciliation；
- unresolved question registry；
- community alias ledger；
- Narrative Model v0.2 proposal；
- “又见新来燕” deep-dive 内容样板；
- UX prototype；
- 最终产品代码与 reviewed dataset。

### Windows — Game Evidence Station

负责：

- 游戏原生任务与剧情 UI 采集；
- 明潮/暗涌界面与层级观察；
- 清河第一章与“又见新来燕”任务流程证据；
- 针对 Mac unresolved list 的二次游戏内核验；
- 本地安装目录 metadata feasibility。

### 核心边界

> **Windows 负责“看到什么”；Mac 负责“这些证据说明什么”。**

Windows 不直接根据现场观察修改正式 canonical dataset；Mac 在 reconciliation 后才产生 reviewed claim / model / dataset change。

---

## 9. Wave 1.6 阶段

### E0 — Narrative Research Expansion — GO

目标：建立清河第一章尤其“又见新来燕”的可靠 research corpus。

退出条件：

- 公开资料 inventory 完成；
- 游戏内明潮/暗涌 UI 与任务流程完成首轮观察；
- unresolved list 可追踪；
- raw evidence 与 research conclusion 分离。

### E0.5 — Local Asset Feasibility — GO, READ-ONLY

目标：确认是否存在可直接读取的稳定 quest/localization metadata。

退出条件：形成 `FEASIBLE / PARTIAL / NO_GO` 结论，不要求实现 extractor。

### E1 — Narrative Model v0.2 Proposal — WAITING_FOR_E0

目标：定义“明潮 + 暗涌 + interpretation + character recall + alias”如何映射到现有 canonical 架构。

约束：先 proposal/research doc，**不立即迁移数据库**。

### E2 — “又见新来燕” Deep Dive Pilot — WAITING_FOR_E0

目标：把一段做到最终内容质量，验证六层解析模型。

退出条件：团队/Lead 能明确判断“这才是目标剧情解析质量”。

### E3 — Reading UX v2 — WAITING_FOR_E1_E2

目标：

- 明潮主阅读 + 暗涌局部展开；
- inline character card；
- “完整事件”重定位为事件档案/解析库；
- 继续保持 canonical-first 与 spoiler-safe。

### E4 — Yanyun Visual Alignment — WAITING_FOR_E3

目标：在已验证的信息架构上做燕云审美对齐，不用视觉重构掩盖内容/结构问题。

### E5 — Player Validation Round 2 — WAITING_FOR_E2_E3

重新验证：

1. Alignment：是否像游戏里走过的故事结构；
2. Reading Flow：明潮/暗涌是否自然；
3. Understanding：能否复述因果、人物动机与暗线；
4. Recall：人物小卡是否减少跳页；
5. Community Fit：语言是否更像玩家之间的讲解而非百科。

---

## 10. 当前优先级

### P0

- 扩大剧情研究 corpus；
- 游戏内任务/明潮/暗涌结构采集；
- “又见新来燕” deep-dive；
- “完整事件”第二套排序问题的设计收口。

### P1

- inline character card；
- community aliases；
- 燕云原生视觉语言研究；
- Narrative Model v0.2。

### DEFER

- Canvas 优化；
- 开封扩张；
- AI chat；
- 收藏/账号；
- 全量侠迹/镇守/奇遇产品化；
- 大规模解包；
- Wave 2 其他功能扩张。

---

## 11. Wave 1.6 总 Gate

Wave 1.6 不以“完成多少页面”验收，而以以下 Gate 判断：

- **G1 Native Evidence**：关键任务流程有游戏内或等价强证据；
- **G2 Narrative Depth**：pilot 能覆盖六层解析，而不是拉长 summary；
- **G3 Topology**：明潮/暗涌关系可被模型表达，且不污染 canonical fact；
- **G4 Single Ordering Authority**：主阅读只有 canonical/native ordering authority；
- **G5 Recall UX**：人物 quick recall 不要求跳离阅读流；
- **G6 Community Language Provenance**：社区称谓有来源等级，不冒充 canonical identity；
- **G7 Safety/Legal Boundary**：asset research 不突破访问控制/反作弊/版权边界；
- **G8 Verification**：进入产品实现阶段后继续保持 exact-HEAD remote `verify`。

---

## 12. 当前 Success Criterion

Wave 1.6 第一阶段真正需要证明的不是“我们收集了更多数据”，而是：

> **玩家沿着游戏熟悉的明潮往前读时，可以随时看到暗涌如何改变对这一段故事的理解；遇到人物能马上想起是谁；读完后不仅记得发生了什么，还能说清为什么发生、人物为什么这么做，以及之前漏掉了什么。**

在这个标准被“又见新来燕”pilot 证明前，不扩整章，不扩开封，不以功能数量代替内容质量。
