# 清河叙事研究总账（Qinghe Narrative Research Index）

> Wave 1.6 · E0 · Mac（Research / Product Hub）· M-01
> 状态：IN_PROGRESS（M-02/M-03/M-04 继续汇入）
> 上游：docs/WAVE_1_6_NARRATIVE_DIRECTION.md · docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md

## 目的

把清河第一章（尤其「又见新来燕」）的**公开资料研究**集中到单一总账，
不再散落于 Wave 1.5 的研究文档。Windows（Game Evidence Station）的现场采集
与本总账的 Mac 分析严格分离：**本目录只放 reviewed claim / conclusion，
raw evidence（截图/录像）不提交 GitHub。**

## 目录

| 文件 | 内容 |
| --- | --- |
| README.md | 本说明 |
| source-ledger.md | 公开资料来源总表（能证明什么、不能证明什么） |
| main-story-inventory.md | 清河故事结构总表（canonical spine + 明潮节点） |
| hidden-story-inventory.md | 明/暗线（暗涌）关联候选 |
| unresolved-questions.md | Unresolved registry（含需 Windows 现场核实清单） |
| character-aliases.md | 社区称谓总账（M-03 深化） |
| interpretation/part-1-you-jian-xin-lai-yan.md | 「又见新来燕」六层解析骨架（E2/M-04 填充） |
| reconciliation/README.md | NEX-006 输入 provenance、冻结边界与交付索引 |
| reconciliation/qinghe-part1-evidence-map.md | Mac claim × Windows cluster × canonical v0.1 逐 claim 对账 |
| reconciliation/windows-followup-evidence-list.md | 第二轮 Windows 定向补证任务 |

## 冻结基础（不重开）

- Canonical Contract v0.1 rev 2 与 yysls-qinghe-canonical-v0.1（sha256 4b1919f0…）继续冻结；
- canonical spine 18 节点（1 CHAPTER + 4 MAIN_PART + 13 MAIN_QUEST）顺序与父子关系以冻结数据集为准；
- 解释层不得再次创造第二条权威剧情顺序。

## Claim 验收格式（M-01 起所有高价值 claim 遵守）

```text
claim
source            # URL / 来源标识
source_kind       # official | walkthrough | wiki | player | in_game
evidence_role     # IDENTITY|TITLE|HIERARCHY|ORDER|PREREQUISITE|CHARACTER|HIDDEN_CLUE|MOTIVATION|FORESHADOWING|COMMUNITY_ALIAS|GENERAL
confidence / state# HIGH|MEDIUM|LOW 或 canonical 状态 VERIFIED|PROVISIONAL|SOURCE_CONFLICT|UNRESOLVED
notes
```

## Evidence role 词表（Wave 1.6 §6）

IDENTITY / TITLE / HIERARCHY / ORDER / PREREQUISITE / CHARACTER /
HIDDEN_CLUE / MOTIVATION / FORESHADOWING / COMMUNITY_ALIAS / GENERAL

## 与 Windows 的接口

- unresolved-questions.md 中 [W-verify] 的问题**优先走 Windows 静态路线**（W-R04/R05 资源探测）；
  静态无法解决且阻塞 P0 narrative claim 时才回退 W-01 人工采集（2026-08-23 supersede）；
- Windows 的 raw evidence 结论经 Mac reconciliation（M-05/NEX-006）后才成为 reviewed claim；
- 本目录任何条目不得凭二手攻略把未确认节点升级为 VERIFIED（执行协议 0.4.2）。

## 证据职责分工（2026-08-23，extractor supersede — Lead §7）

Windows 静态研究已证明可确定性定位剧情结构 metadata（LT/LuaT narrative data，W-R00→R06
TECHNICAL PASS，方向 MINIMAL_EXTRACTOR_GO）；Mac 路线相应更新：

| 证据类型 | 主来源 |
| --- | --- |
| native task identity / task IDs / 结构 / region / story refs | **Extractor**（Windows 静态，NEX 系列） |
| character identity | Extractor + public |
| exact UI presentation | 人工 fallback（W-01~03 FALLBACK_ONLY） |
| motivation / causality / foreshadowing / historical interpretation | **Mac research**（本总账） |

即：**Windows 自动回答"游戏数据里是什么"；Mac 回答"玩家应该怎样理解它"。**
本总账聚焦后四类叙事理解证据；native title/order/identity 类 TODO 优先由 Extractor 输出关闭
（NEX-006 reconciliation 时对账；CANONICAL_CANDIDATE 只经 promotion policy 产生，自动覆盖 canonical 禁止）。

## NEX-006 状态

NEX-006 已在独立 reconciliation 层完成首轮对账；结果不修改本目录原 claim state，也不修改
canonical v0.1。输入分支/提交、关键文件 SHA、7 个 Windows clusters 的完整去向与后续补证门槛见
[`reconciliation/README.md`](reconciliation/README.md)。
