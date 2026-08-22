# 社区称谓总账（Character Alias Ledger）

> M-01 建骨架 · M-03 深化。字段按 M-03 最小规范。
> 原则：alias 不替代 canonical identity；meme 不进入事实字段（Wave 1.6 P5/G6）。

## 字段规范（M-03）

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

## 首批（清河核心人物，M-03 已补 provenance）

| character (v5 id) | canonical_name | alias | alias_kind | source（含 locator） | safe_for_narrative | notes / state |
| --- | --- | --- | --- | --- | --- | --- |
| protagonist | 主角 | 少东家 | COMMUNITY_COMMON | SRC-3DM-MINGAN-STORY（"当少东家完成整个明暗故事收集后"）；SRC-17173-SHAODONGJIA（《少东家身世大猜想》）；bilibili 视频标题（BV1xtcxeCEix"少东家夜枫白菽"） | 是 | 3 处独立公开使用，稳定常见 → COMMUNITY_COMMON；官方使用待核（UQ-20） |
| protagonist | 主角 | 小师父 / 少侠 | — | 无来源 | 否 | **UNRESOLVED**：未找到稳定公开使用，暂不进入叙事文案（H-M01-1） |
| han-xiangxun | 寒香寻 | 寒姨 | COMMUNITY_COMMON | SRC-ALI213-XUNXIN（"剧情开头的'寒姨'"）；SRC-ALI213-FULL-STORY（"见过寒姨"）；v5 文案 | 是 | 攻略+项目普遍使用；官方是否使用待核（UQ-20） |
| jiang-yan | 江晏 | 江叔 | COMMUNITY_COMMON | SRC-ALI213-XUNXIN（"江叔离开后寒姨抚养主角长大"）；v5 事件文案 | 是 | 攻略+项目使用；官方待核（UQ-20） |
| zhou-hongxian | 周红线 | 红线 | COMMUNITY_COMMON | 攻略/社区/官方语境普遍；v5 | 是 | 项目已用 |
| yi-dao | 伊刀 | 刀哥 | COMMUNITY_COMMON（候选） | SRC-BILIBILI-MAIN-PARTS（BV1onrcYkErP 标题"刀哥"） | 是 | 仅视频标题证据，正式度待核 |
| tian-ying | 田英 | 田英 | OFFICIAL（本名） | v5；官方叙事 | 是 | 无别名冲突 |
| wang-qing | 王清 | 王清将军 | COMMUNITY_COMMON | 社区考据标题（SRC-TOUTIAO-WANGQING） | 是 | 历史身份需与作品设定区分 |

## Provenance 状态（H-M01-1 明确表述）

> **Alias ledger skeleton 已建立；部分 alias provenance 已补齐（上表），其余待 M-03 后续与 Windows 官方文本核验（UQ-20）后再定级。**
> 现阶段不声称"alias 均带 source"——无来源条目明确标 UNRESOLVED。

## 待 M-03 后续深挖

- 少东家/寒姨/江叔是否出现在**官方文本**（游戏内对话/官方号）→ 已登记 UQ-20 [W-verify]；
- 红线/伊刀/广胡子等其它惯称；
- COMMUNITY_MEME 级称谓单独登记，不进入叙事文案。

## 规则

- 进入产品文案的 alias 必须有 source 且标记 alias_kind；
- OFFICIAL_ALIAS 优先；COMMUNITY_COMMON 需稳定长期使用；
- alias 变化不改变 canonical identity（主角 canonical 仍为 protagonist）。
