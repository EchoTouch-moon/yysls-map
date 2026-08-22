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

## 首批（清河核心人物）

| character (v5 id) | canonical_name | alias | alias_kind | source | safe_for_narrative | notes |
| --- | --- | --- | --- | --- | --- | --- |
| protagonist | 主角 | 少东家 | COMMUNITY_COMMON（候选） | 17173 专区《少东家身世大猜想》 | 待定 | 需确认社区使用时长与稳定度；M-03 深挖 |
| protagonist | 主角 | 小师父 / 少侠 | COMMUNITY_COMMON（候选） | 待查 | 待定 | M-03 |
| han-xiangxun | 寒香寻 | 寒姨 | COMMUNITY_COMMON | 攻略/社区普遍使用；v5 文案 | 是 | 已进入项目文案；官方是否使用待核 |
| jiang-yan | 江晏 | 江叔 | COMMUNITY_COMMON | v5 事件文案（"江叔"）；攻略 | 是 | 养父称谓；官方称谓待核 |
| zhou-hongxian | 周红线 | 红线 | COMMUNITY_COMMON | 攻略/社区/官方语境普遍 | 是 | 项目已用 |
| yi-dao | 伊刀 | 刀哥 | COMMUNITY_COMMON（候选） | bilibili BV1onrcYkErP 标题"刀哥" | 是 | 视频标题证据；正式度待核 |
| tian-ying | 田英 | 田英 | OFFICIAL（本名） | v5；官方叙事 | 是 | 无别名冲突 |
| wang-qing | 王清 | 王清将军 | COMMUNITY_COMMON | 社区考据标题 | 是 | 历史人物身份需与作品设定区分 |

## 待 M-03 深挖

- 少东家称谓的首次出处与使用分布；
- 寒姨/江叔是否出现在官方文本（游戏内/官方号）；
- 红线/伊刀/广胡子等角色在社区的其它惯称；
- COMMUNITY_MEME 级称谓（若存在）单独登记，不进入叙事文案。

## 规则

- 进入产品文案的 alias 必须有 source 且标记 alias_kind；
- OFFICIAL_ALIAS 优先；COMMUNITY_COMMON 需稳定长期使用；
- alias 变化不改变 canonical identity（主角 canonical 仍为 protagonist）。
