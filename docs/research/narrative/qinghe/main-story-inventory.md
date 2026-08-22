# 清河故事结构总表（Main Story Inventory）

> M-01 · Mac · 数据来源：yysls-qinghe-canonical-v0.1.json（冻结）+ Wave 1.5 inventory/mapping + 公开攻略
> 顺序与父子关系以 canonical spine 为准；本表是明潮（明线）研究坐标，暗线见 hidden-story-inventory.md。

## 1. 清河 canonical spine 总表（冻结，18 节点 / 12 links）

| canonical_key | title | node_type | parent | sort_order | linked event（mapping_kind） |
| --- | --- | --- | --- | --- | --- |
| wwm:qinghe:chapter-1 | 第一章·神仙不渡 | chapter | — | 0 | — |
| wwm:qinghe:chapter-1:part-1 | 又见新来燕 | main_part | chapter-1 | 1 | — |
| wwm:qinghe:chapter-1:part-1:awaken | 竹林旧居线索 | main_quest | part-1 | 1 | p1-awaken（exact） |
| wwm:qinghe:chapter-1:part-1:bridge | 断桥 | main_quest | part-1 | 2 | p1-cross-bridge（exact） |
| wwm:qinghe:chapter-1:part-1:archery | 北竹林学射 | main_quest | part-1 | 3 | p1-archery（exact） |
| wwm:qinghe:chapter-1:part-1:wilderness | 百草野遇天涯客 | main_quest | part-1 | 4 | p1-wilderness（exact） |
| wwm:qinghe:chapter-1:part-1:arena | 将军祠擂台 | main_quest | part-1 | 5 | p1-arena（exact） |
| wwm:qinghe:chapter-1:part-2 | 匹马映林嘶 | main_part | chapter-1 | 2 | — |
| wwm:qinghe:chapter-1:part-2:return-home | 回神仙渡打听 | main_quest | part-2 | 1 | p2-return-home（exact） |
| wwm:qinghe:chapter-1:part-2:reunion | 不羡仙与寒姨重逢 | main_quest | part-2 | 2 | p2-reunion（merged） |
| wwm:qinghe:chapter-1:part-2:cisheng | 瓷窑与地下仓库 | main_quest | part-2 | 3 | p2-reunion（merged） |
| wwm:qinghe:chapter-1:part-2:break-temple | 破庙救红线与广胡子 | main_quest | part-2 | 4 | —（零 link，MISSING event） |
| wwm:qinghe:chapter-1:part-3 | 菱花尘满 | main_part | chapter-1 | 3 | — |
| wwm:qinghe:chapter-1:part-3:depart | 酒香塔留信辞行 | main_quest | part-3 | 1 | p3-depart（exact） |
| wwm:qinghe:chapter-1:part-4 | 为谁归去 | main_part | chapter-1 | 4 | — |
| wwm:qinghe:chapter-1:part-4:reunion-yidao | 破庙汇合伊刀 | main_quest | part-4 | 1 | p4-reunion-yidao（exact） |
| wwm:qinghe:chapter-1:part-4:rescue | 回不羡仙救人 | main_quest | part-4 | 2 | p4-rescue（exact） |
| wwm:qinghe:chapter-1:part-4:tower-battle | 酒香塔击败千夜 | main_quest | part-4 | 3 | p4-tower-battle（exact） |

## 2. 「又见新来燕」已知任务节点（deep-dive 目标，E2/M-04 深化）

| # | 节点 | 主要 claim | source | source_kind | evidence_role | state |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 竹林旧居线索 | 红线唤醒主角；罐中信与灵位给出「寻找江叔」的目标 | ali213 第1页步骤1-4；v5 evt-p1-awaken | walkthrough | IDENTITY/ORDER/CHARACTER | VERIFIED（节点存在）；细节待核 |
| 2 | 断桥 | 木桥断裂，需轻功过桥 | ali213 步骤5；sohu 全主线 | walkthrough | IDENTITY/ORDER | VERIFIED |
| 3 | 北竹林学射 | 冯继升（一作冯继生）传授射术并比试 | ali213 步骤8-10；bilibili BV1ZL6fYMEer | walkthrough/player | CHARACTER/TITLE | VERIFIED（NPC 名写法 UNRESOLVED） |
| 4 | 百草野遇天涯客 | 天涯客给清河舆图；驱熊偷师太极 | ali213 步骤11-14；官方访谈（"神秘的江湖人"） | walkthrough/official | IDENTITY/CHARACTER/HIDDEN_CLUE | VERIFIED；与官方"江湖人"对应为候选（未官方点名） |
| 5 | 将军祠擂台 | 方旭/老金擂台，得听风辨位等 | ali213 步骤15-19 | walkthrough | IDENTITY/ORDER/CHARACTER | VERIFIED |

## 3. 明潮（明线）关键候选（供 E1 Narrative Model 讨论，非冻结结论）

- 主角成长线：被袭 → 寻亲 → 立足 → 承担 → 抉择 → 收束（对应 5 节点叙事功能）；
- 同伴线：红线（引导/陪伴）→ 广胡子/老金（名声）→ 伊刀（后段）；
- 物件线：镇冠珏（失玉 → 追索）为篇一驱动；
- 「天涯客 = 官方访谈的'神秘的江湖人'」为候选对应，需更强证据（M-02）。

## 4. 与 v5 事件的覆盖对照

- 篇一 5 节点均已有 EXACT event overlay（p1-awaken/cross-bridge/archery/wilderness/arena）；
- v5 中 p1-chouyuehai（神仙渡揭穿胡为）属「神仙不渡城镇段」候选（PROVISIONAL_GROUP，不在本篇）；
- 篇一范围内无零 link 节点（全挂载）。
