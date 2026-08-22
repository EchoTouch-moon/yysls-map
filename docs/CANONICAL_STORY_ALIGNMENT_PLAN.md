# Canonical Story Alignment Plan

> 决议日期：2026-08-22  
> 状态：**APPROVED / WAVE 1.5 GO**  
> 基线：`59e33a6`（Wave 1 IMPLEMENTED / VALIDATION_PENDING）

## 1. 背景与问题定义

Wave 1 已完成「逐层理解剧情」的信息架构、人物剧情足迹、Story-first 首页、人物级 Reveal、历史背景回链与可见性 hardening，但在玩家视角复核时暴露出一个更上游的问题：

> 当前产品用于组织“剧情理解”的主线，主要由项目自行编排的 StoryArc / StoryBeat 驱动，而不是严格沿游戏中的原生故事线展开。

这会造成三个直接问题：

1. **叙事坐标错位**：玩家进入产品是为了回顾或理解自己在游戏中刚经历的故事，但当前导读无法与游戏任务/篇章顺序一一对齐，容易产生“内容能看懂，但和我玩的不是同一条线”的割裂感。
2. **阅读方式不自然**：当前“跟着故事读”采用单幕切换、频繁点击的阅读方式，更像卡片/PPT；剧情回顾更适合连续滚动的一条主线，在需要深挖时再进入人物、暗线、历史或解析层。
3. **Canonical 数据来源不足**：游戏本身存在可识别的篇章、主线、任务与故事节点，但当前仓库缺少一套经核验的原生剧情骨架；后续需要先确认公开资料、游戏内观察与其他合法可验证来源能覆盖多少，再决定是否有必要研究本地游戏资源。

因此，本轮不是对 Wave 1 UI 做局部优化，而是校正产品的叙事基础设施。

## 2. 产品决策

新的核心命题调整为：

> **沿着《燕云十六声》的游戏原生故事线，把主线、暗线、人物、伏笔、历史背景和编辑解析重新连接起来。**

产品必须明确区分两层：

### 2.1 Canonical Story Layer（事实/坐标层）

用于表达玩家在游戏中真实经历的故事结构，包括但不限于：

- 区域 / 章节；
- 主线篇章；
- 任务或可核验的剧情节点；
- 原生顺序、父子关系和前后继关系；
- 节点类型与来源/provenance。

该层负责回答：

> “游戏里的这段剧情，准确位于哪里？”

它不承载项目自创的叙事顺序。

### 2.2 Interpretation Layer（解释层）

挂载在 Canonical Story Node 之上，用于表达：

- 发生了什么；
- 为什么重要；
- 人物动机与人物足迹；
- 关系变化；
- 暗线与支线关联；
- 历史背景；
- 伏笔、回看与编辑解释；
- 来源、置信度和争议边界。

该层负责回答：

> “这一段为什么会这样？它和其他故事到底有什么关系？”

**原则：解释层可以重组信息，但不能取代游戏原生故事线成为页面的第一坐标轴。**

## 3. 对现有 Wave 1 的处理

Wave 1 的工程成果保留，不推倒重做：

- Story-first 首页：保留；
- 人物页五段式渐进阅读：保留；
- `story_path` 派生思路：保留，但未来应改为从 Canonical Story Node 派生人物出现轨迹；
- History 与 Story 的双向深链：保留；
- Reveal / spoiler protection：继续作为保护层；
- visibility parent-chain invariant：继续作为所有公开 projection 的强约束；
- 当前 10 个 StoryBeat：不删除，但降级为 **Editorial Interpretation Track**，不再决定主阅读页面的原生顺序。

状态调整：

- **Wave 1 Engineering：CLOSED / BASELINE FROZEN**
- **Wave 1 Player Validation：PAUSED**
- 暂停原因：`Canonical storyline mismatch`
- **Wave 2：继续 NO_GO / VALIDATION_REQUIRED**
- **Wave 1.5：GO**

在 Wave 1.5 完成前，不使用当前“跟着故事读”作为主要产品形态进行 5–10 人正式验证。

## 4. Wave 1.5 — Canonical Story Alignment

### Phase A — Canonical Qinghe Inventory

目标：建立清河区域可核验的游戏原生剧情骨架。

输出应能够表达：

`Region → Chapter → Main Story / Quest → Story Node → Order / Parent / Previous / Next`

只收集建立骨架所需的结构化 metadata，不以收集完整对白、剧情原文或媒体资源为目标。

退出条件：

- 清河主要篇章与任务/剧情节点形成一条可读、可核验的原生主干；
- 每个节点至少有一个 provenance；
- 对顺序、层级或命名有争议的节点明确标记 unresolved，而不是猜测填充。

### Phase B — Existing Content Mapping

目标：建立“游戏原生节点 ↔ 当前内容实体”的映射矩阵。

映射对象至少覆盖：

- Canonical Story Node；
- 当前 `StoryEvent`；
- 当前 `StoryArcBeat`；
- Character appearances；
- Historical links。

映射结果需要显式区分：

- `EXACT`：一一对应；
- `MERGED`：当前一个实体合并多个游戏节点；
- `SPLIT`：当前多个实体对应一个游戏节点；
- `EDITORIAL_ONLY`：仅为项目解释层节点，不存在游戏原生锚点；
- `MISSING`：游戏有节点但项目尚未覆盖；
- `UNRESOLVED`：证据不足。

退出条件：

- 当前 10 个 StoryBeat 的原生锚点状态全部可解释；
- 不允许继续把 `EDITORIAL_ONLY` 节点当成 Canonical 顺序。

### Phase C — Canonical Story Contract

目标：在确认 Inventory 与 Mapping 有效后，再决定是否引入新的持久化模型/Schema。

候选概念模型：

`CanonicalStoryNode`

- stable/local id；
- optional game id（仅在来源可靠时保存）；
- title；
- node type；
- parent / previous / next；
- region / chapter；
- game order；
- provenance / evidence；
- publication / spoiler visibility metadata。

`StoryInterpretation`

- canonical node reference；
- summary；
- why_it_matters；
- bridge / explanation；
- character / relationship links；
- history / hidden-thread links；
- editorial analysis。

Schema 变更不是 Phase A/B 的前置条件。只有 Mapping 证明当前模型无法可靠表达 Canonical Story 时，才进入 schema migration / dataset refreeze。

### Phase D — Continuous Storyline UX

目标：用游戏原生故事线替换当前“单幕点击式”主阅读体验。

主模式应满足：

- 以一条连续可滚动的纵向故事线为默认；
- 主干顺序与 Canonical Story 对齐；
- 用户通过滚动即可完成故事回顾，不依赖频繁“上一幕/下一幕”点击；
- 人物、暗线、历史、关系和完整解析作为从主干向外展开的 secondary layer；
- 点击行为用于“深挖”，而不是用于“继续阅读下一段”；
- 当前“完整事件”模式中的连续浏览体验可作为交互参考，但最终页面必须以 Canonical Story 而非当前 Event 排序直接替代。

不要求在本阶段同时实现复杂多分支图。视觉优先级始终是：**主线必须一眼可跟随，支线只在需要时展开。**

退出条件：

- 玩家能从清河开头连续滑到结尾；
- 页面节点能与游戏中的篇章/任务名称建立稳定对应；
- Story → Character / Hidden Thread / History → Story 深链仍成立；
- 现有 spoiler / visibility invariant 不退化。

### Phase E — Player Validation Restart

只有 Canonical Storyline 成为默认阅读骨架后，才恢复 5–10 名玩家验证。

验证重点继续记录：

- Entry；
- Depth；
- Continuity；
- Understanding。

新增一个首要判断：

> **Alignment：用户是否能快速把网站中的剧情节点与自己在游戏中经历的任务/篇章对应起来。**

若 Alignment 失败，则继续修正 Canonical Story 数据与页面骨架；不得用更多解释内容掩盖顺序错误。

## 5. 剧情数据获取策略

获取 Canonical Story 数据按风险和成本从低到高推进：

### Level 1 — 公开可核资料

优先使用：

- 官方公开页面/公告/叙事资料；
- 可核验攻略与任务目录；
- Wiki / 公共数据库；
- 玩家公开流程记录。

目标是任务名、章节层级、顺序、类型等 metadata，不直接复制大段原文。

### Level 2 — 游戏内人工观察

通过实际游玩、任务界面和流程截图核对：

- 名称；
- 父子层级；
- 顺序；
- 前置/后继；
- 节点类型。

游戏内观察应作为高价值 provenance，而不是只凭社区二手总结。

### Level 3 — 半自动采集

当人工维护成本升高时，可考虑：

`截图/录屏 → 文本或结构提取 → 人工复核 → Canonical dataset`

任何自动提取结果都必须经过人工核验后才能成为 canonical 数据。

### Level 4 — 本地游戏资源研究

只有当前三级来源无法满足以下需求时，才评估本地游戏资源研究：

- 稳定 quest ID；
- 完整 hierarchy；
- 大规模版本同步；
- 人工采集成本明显不可持续。

即使进入该层，目标也应优先限定为**结构化 metadata**，而不是分发完整对白、CG、音频、美术资源或原始资源包。

如果数据受到加密、DRM、反作弊或其他访问控制保护，不把绕过这些机制作为产品依赖。

## 6. 数据与版权边界

项目继续坚持：

- 不建设完整对白/剧情原文数据库；
- 不复制或重新分发游戏媒体资产；
- Canonical Story 只保存建立导航骨架所必需的 metadata 与原创摘要；
- 来源与 provenance 必须可追踪；
- 社区总结、玩家观察、官方资料和编辑推测必须保持类型区分；
- 对本地资源研究的任何结果，先评估法律、平台规则、版权和发布边界，再决定是否进入公开数据集。

## 7. Wave 1.5 Acceptance Gates

- **C1 — Canonical Coverage**：清河主线骨架已建立，核心篇章/节点无未解释的顺序空洞。
- **C2 — Provenance**：每个 canonical 节点至少存在一条可追踪来源；不允许凭印象生成 canonical 顺序。
- **C3 — Mapping Closure**：当前 StoryEvent / StoryBeat 与 canonical node 的映射状态全部明确。
- **C4 — Layer Separation**：Canonical Story 与 Editorial Interpretation 在数据和 UI 语义上明确分层。
- **C5 — Continuous Reading**：默认故事页可连续滚动阅读，不需要逐幕点击才能前进。
- **C6 — Game Alignment**：节点命名/顺序可被实际玩家与游戏任务线快速对应。
- **C7 — Deep-link Preservation**：人物、暗线、历史、关系与故事节点之间的已有深链能力不退化。
- **C8 — Visibility Closure**：任何新 projection 继续满足完整 parent-chain visibility invariant。
- **C9 — Contract Discipline**：在 Phase A/B 证据不足前不提前引入 schema 1.2 或重新冻结 v5。
- **C10 — Acquisition Decision**：只有明确记录公开资料/游戏内观察的覆盖缺口后，才能决定是否进入本地游戏资源研究。

## 8. 暂停与非目标

Wave 1.5 完成前暂停：

- 人工人物线大规模扩写；
- `foreshadows` schema；
- 问题驱动答案引擎；
- 字段级 Reveal；
- 开封扩容；
- AI 剧情聊天；
- 账号/收藏/推荐等横向能力。

本轮不以“增加剧情数量”为成功标准。

成功标准是：

> **玩家看到的网站故事线，首先就是他在游戏里经历的那条线；我们的价值来自在这条线上补充理解，而不是重新替游戏编排一条故事。**
