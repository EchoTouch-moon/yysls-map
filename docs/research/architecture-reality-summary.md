# Architecture Reality Summary — Wave 1.5 基线盘点

> 阶段：Wave 1.5 / Canonical Story Alignment — Task 1（只读盘点，无代码修改）
> 基线：HEAD 59e33a6（Wave 1 Engineering 冻结基线）
> 覆盖：DB 模型 / 导入管线 / API / Timeline 前端 / deep link / 冻结数据集。共 15 条。

## 结论（≤15 条）

1. **StoryEvent 是扁平事件，不是任务节点。**
   DB 模型（apps/api/app/models.py :: StoryEvent）只有 id/slug/title/summary/impact/chapter_id/sort_order/spoiler_level/visible_after_chapter_id/status，
   以及 characters/factions 多对多。**没有** region、part、quest_id、node_type、parent、previous/next 等任何“任务结构”字段。

2. **v5 JSON 的 event.part 字段在导入时被静默丢弃。**
   content_import/models.py 的 EventItem 校验了 part（0–4），但 content_import/apply.py 写入 StoryEvent 时未映射该字段；
   全代码库（API/Web/api-client）对 part 零引用（唯一命中是 import 模型本身）。即“篇”的切分信息进入数据库后即丢失。

3. **StoryArc 是人工策展的阅读路径，不是游戏任务。**
   v5 冻结集中只有 1 个 arc：qinghe-main-journey（“清河主线：从失玉到离乡”）。
   title/summary/core_question/estimated_minutes（12 分钟）与 10 个 beat 的 guide/why_it_matters/bridge/next_question 全部为项目自撰导读文案，
   不是游戏内任务名称或任务描述。

4. **StoryArcBeat 通过 event_id 引用 StoryEvent，形成 arc→beat→event 三层。**
   10 个 beat 只引用 27 个 event 中的 10 个；beat 另有 role 枚举（setup/clue/escalation/turning_point/consequence/resolution）——
   该枚举是叙事角色标签，与游戏任务分类（主章/侠迹/镇守/奇遇）无对应关系。

5. **/timeline API（routes/timeline.py）只返回扁平事件序列。**
   按 chapter.sort_order + event.sort_order 排序，按 progress/spoiler 过滤；无任务分组、无篇、无章内层级。

6. **/story-arcs API（routes/story_arcs.py）返回 arc + beats 全量（含事件、人物、来源、关系、历史卡），全部经过 arc→beat→event 可见性过滤。**
   由于冻结集只有一个 arc，该 API 实际只服务一条导读线。

7. **story_path（人物剧情足迹）是派生投影，不是持久化字段。**
   routes/details.py::_story_path 实时 join beats→events→arcs，选出“该人物出现在其 event.characters 中的 beat”，
   按 arc 标题字典序 + beat.sort_order 排序，并做 arc→beat→event 三层可见性闭包（H2 hardening）。
   语义上它是“人物在人工导读中的足迹”，不是“人物在游戏任务中的进度”。

8. **/timeline UI 是“单卡阅读器”，不是连续滚动。**
   TimelineExplorer.tsx 默认 guide 模式 = 卷首（GuideMasthead）+ 左侧幕次导航 + 单张阅读卡 + “上一节/下一节”按钮；
   events 模式 = 章节筛选 + 扁平事件列表。进度切换会整体 remount（spoiler-safe，T05 设计）。

9. **所有 deep link 依赖 event slug：/timeline?beat={event_slug}。**
   来源包括：人物页剧情足迹（CharacterProfile.tsx L225）、历史卡 related beats（HistoryDetailCard.tsx L206）、e2e（character-trail.spec.ts）。
   解析逻辑：前端逐个请求每个 arc 详情，比对 beat.event.slug === pendingBeatSlug，命中后定位幕次（TimelineExplorer.tsx L248 起）。
   即 deep link 的锚点粒度是 **event slug**，且只对“存在于某 arc beat 中的事件”有效。

10. **StoryArc 目前被当作“canonical story”使用。**
    guide 模式把 qinghe-main-journey 呈现为“清河主线”；人物页“剧情足迹”、历史页“在故事中的位置”都从这一条 arc 派生。
    但该 arc 与游戏原生任务结构（神仙不渡主线四篇）不是同一对象——标题、顺序、节点粒度均不同。

11. **内容导入强制 PUBLISHED，schema 校验通过即进入公开面。**
    apply.py 对所有导入实体 status = ContentStatus.PUBLISHED；没有草稿-发布工作流用于数据集导入。
    剧透防护完全依赖 progress/spoiler 运行时过滤。

12. **来源结构：24 条 source 中 21 条 community_analysis、3 条 official_reference。**
    SourceType.QUEST_REFERENCE（任务定位）枚举存在但 v5 中 0 使用；也没有任何 source 绑定到“任务/任务节点”主体
    （Source 只可绑定 chapter/faction/character/event/relationship，无 quest 主体）。

13. **schema 1.1（content-data.schema.json）与 DB 均无 canonical 字段。**
    storyArc/storyArcBeat/event 的 JSON Schema 中都没有 quest_id/node_type/parent/previous/next/region；
    event 的 part 是唯一接近“篇”的字段且被丢弃（见 #2）。

14. **冻结数据集锚点**：release-manifest.json 固定 yysls-qinghe-v5.json（sha256 4bcb61e8…，schema 1.1，
    27 events / 1 arc / 10 beats / 10 factions / 39 characters / 29 relationships）。任何 content/ 改动都会破坏 G6 验收门。

15. **demo seed 与生产数据隔离**：seed.py 只生成 demo-* 虚构卷/角色/事件，不含 arc/beat；
    线上可见的 arc 数据只来自 v5 导入。timeline/arc 测试基线与生产内容路径一致。

## 对 Wave 1.5 的含义（一句话）

当前实现中“canonical story”缺席：既有模型擅长表达「人工导读线（arc→beat）+ 扁平事件」，
但没有任何一层表达「游戏原生任务骨架（章→篇→任务节点→子任务）」，且唯一的“篇”字段（event.part）在导入时被静默丢弃。

## 附注

- 任务引用文档 docs/CANONICAL_STORY_ALIGNMENT_PLAN.md 在仓库（含 .worktrees/T01–T04）中不存在，本次以任务书内联要求为准。
- 工作树唯一预先存在的改动是 apps/web/next-env.d.ts（自动生成文件），非本任务引入。
