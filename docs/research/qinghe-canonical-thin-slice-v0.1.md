# Qinghe Canonical Thin Slice v0.1（研究草案）

> 阶段：Wave 1.5 / Phase C1 — Thin Slice 验证
> 用途：用最小高置信主干验证 canonical-story-contract-v0.1.md 是否真的能表达现有研究结果。
> 范围（Lead scope gate）：只选 第一章·神仙不渡 + 四个高置信主篇 + 已有高置信 EXACT 节点。**不填未确认内容；所有不确定任务名称保持 UNRESOLVED。**
> 本文件是 research artifact，不是 canonical dataset；canonical_key 为草案编号。
> rev 2（C1.1）：node_type 统一 MAIN_QUEST（原 MAIN_QUEST）；link 语义 = mapping_kind（EXACT/MERGED/SPLIT；EDITORIAL_ONLY 为零 link 审计状态）；未核验名称由 verification_state 表达（无 boolean）。

## 1. 节点清单（canonical 层草案）

| provisional id | title（核验态） | node_type | parent | sort_order | provenance | confidence | StoryEvent link |
| --- | --- | --- | --- | --- | --- | --- | --- |
| csn-qh-ch1 | 第一章·神仙不渡（verified） | CHAPTER | — | 0 | 3DM 3976025；ali213 1599605；v5 | HIGH | — |
| csn-qh-prologue | 序章（任务簿名称 UNRESOLVED） | MAIN_QUEST | csn-qh-ch1 | 1 | sohu 843193673；bilibili BV1Nc6fYUEb9；v5 evt-prologue-* | HIGH（内容） | evt-prologue-escape EXACT；evt-prologue-attack EXACT |
| csn-qh-part1 | 篇一·又见新来燕（游戏内字符串 UNRESOLVED：又见新来燕/又见新燕来） | MAIN_PART | csn-qh-ch1 | 2 | ali213 第1页；3DM 3977244；bilibili BV1ZL6fYMEer | HIGH（篇存在）；UNRESOLVED（精确字符串） | — |
| csn-qh-part1-awaken | 竹林旧居线索（verified） | MAIN_QUEST | csn-qh-part1 | 1 | ali213 第1页步骤1-4 | HIGH | evt-p1-awaken EXACT |
| csn-qh-part1-bridge | 断桥（verified） | MAIN_QUEST | csn-qh-part1 | 2 | ali213 步骤5；sohu | HIGH | evt-p1-cross-bridge EXACT |
| csn-qh-part1-archery | 北竹林学射（verified；NPC 名 冯继升/冯继生 UNRESOLVED） | MAIN_QUEST | csn-qh-part1 | 3 | ali213 步骤8-10；bilibili（冯继升） | HIGH | evt-p1-archery EXACT |
| csn-qh-part1-wilderness | 百草野遇天涯客（verified） | MAIN_QUEST | csn-qh-part1 | 4 | ali213 步骤11-14 | HIGH | evt-p1-wilderness EXACT |
| csn-qh-part1-arena | 将军祠擂台（verified） | MAIN_QUEST | csn-qh-part1 | 5 | ali213 步骤15-19 | HIGH | evt-p1-arena EXACT |
| csn-qh-part2 | 篇二·匹马映林嘶（verified；副题"祸源"UNRESOLVED） | MAIN_PART | csn-qh-ch1 | 3 | 17173 162133494；3DM 271545；ali213 第8页 | HIGH | — |
| csn-qh-part2-return | 回神仙渡打听（verified；周叔叔/江叔 UNRESOLVED） | MAIN_QUEST | csn-qh-part2 | 1 | ali213 第8页步骤1-2 | HIGH | evt-p2-return-home EXACT |
| csn-qh-part2-reunion | 不羡仙与寒姨重逢 + 瓷窑/地下仓库（verified） | MAIN_QUEST | csn-qh-part2 | 2 | ali213 步骤3-8；18183 | HIGH | evt-p2-reunion MERGED（覆盖 2 个原生子节点） |
| csn-qh-part2-hospital | 活人医馆/弱水岸 + 寒姨房刺杀（内容 verified；任务归属 UNRESOLVED，可能横跨 PROVISIONAL_GROUP） | MAIN_QUEST | csn-qh-part2 | 3 | ali213 第7/8页；17173 | MEDIUM | evt-p2-hospital UNRESOLVED（link 暂存 research 层） |
| csn-qh-part2-breaktemple | 破庙救红线/广胡子 + 舞马人 BOSS（verified） | MAIN_QUEST | csn-qh-part2 | 4 | ali213 第8页步骤22-24 | HIGH | —（MISSING：当前无 event） |
| csn-qh-part3 | 篇三·菱花尘满（verified） | MAIN_PART | csn-qh-ch1 | 4 | ali213 第9页；repo src-baidu-linghua | HIGH | — |
| csn-qh-part3-depart | 酒香塔留信辞行（verified） | MAIN_QUEST | csn-qh-part3 | 1 | ali213 第9页步骤5 | HIGH | evt-p3-depart EXACT |
| csn-qh-part3-farewell | 竹隐居告别红线（篇归属 UNRESOLVED） | MAIN_QUEST | csn-qh-part3 | 2 | v5 evt-p3-farewell；攻略未定位 | MEDIUM | evt-p3-farewell UNRESOLVED |
| csn-qh-part4 | 篇四·为谁归去（verified） | MAIN_PART | csn-qh-ch1 | 5 | ali213 第10页 | HIGH | — |
| csn-qh-part4-reunion | 破庙汇合伊刀（verified） | MAIN_QUEST | csn-qh-part4 | 1 | ali213 第10页步骤1-2 | HIGH | evt-p4-reunion-yidao EXACT |
| csn-qh-part4-rescue | 回不羡仙救人（宋九/广胡子/丁巳）（verified） | MAIN_QUEST | csn-qh-part4 | 2 | ali213 步骤3-6 | HIGH | evt-p4-rescue EXACT |
| csn-qh-part4-tower | 酒香塔击败千夜（verified） | MAIN_QUEST | csn-qh-part4 | 3 | ali213 步骤7-10 | HIGH | evt-p4-tower-battle EXACT |

## 2. 明确未纳入（保持 UNRESOLVED，不填）

- 神仙不渡城镇段（朱八碗/仇越海/宋九/酒窖/玉笛/思芳歌/寻心）——PROVISIONAL_GROUP，未满足进入条件（Lead 决策 1）；相关 evt-p1-chouyuehai 在 canonical 层无 link；
- 不羡仙大火——任务边界 UNRESOLVED；红线/伊刀之死——UNRESOLVED + SOURCE_CONFLICT（Lead 决策 2），不入正式层；
- 序章任务簿名称——UNRESOLVED；
- 篇一游戏内精确字符串（又见新来燕/又见新燕来）——verification_state=UNRESOLVED/SOURCE_CONFLICT（节点 status 不得 published，G5；变体记入 provenance TITLE 角色）；
- 全部侠迹 / 镇守 / 奇遇 / 暗线——secondary narrative branch，第一版主 spine 不包含；
- evt-wangqing-battle 等解释层/对照事件在 canonical 层零 link（audit editorial-only），不产生 link 记录（G2）。

## 3. 验证结论（contract 可表达性）

1. **层级**：CHAPTER → MAIN_PART → MAIN_QUEST 三级可表达（parent_id + sort_order）。
2. **顺序**：同级 sort_order 派生 previous/next，无显式双写（Lead APPROVED）。
3. **映射**：12 EXACT（全部满足 1:1 invariant：event 恰 1 条 link 且为 EXACT）/ 1 MERGED（evt-p2-reunion 有 2 条 link 且全部 MERGED ✓）/ 2 UNRESOLVED pending（不进正式层）/ 1 MISSING（舞马人段无事件）——均可由 CanonicalStoryEventLink 表达，现有 StoryEvent 零改动。
4. **未确认名称**：verification_state（VERIFIED/PROVISIONAL/SOURCE_CONFLICT/UNRESOLVED）表达 又见新来燕/又见新燕来 冲突（SOURCE_CONFLICT + provenance TITLE 角色变体），无 boolean，不污染 published 层。
5. **研究态节点**：PROVISIONAL_GROUP 仅 research 层；SOURCE_CONFLICT 由 verification_state 承载，status 不得 published（G5）。
6. **结论**：contract v0.1 rev 2 能表达 thin slice 的全部现有高置信研究结果，且 **不要求改 v5 / StoryEvent / StoryArcBeat（C1-G6 ✓）** → 通过 thin slice 验证。

## 4. 与 v5 当前内容的覆盖对照

- thin slice 覆盖 v5 中 15 个事件的 canonical 挂载：12 EXACT（prologue-escape/attack、p1-awaken/cross-bridge/archery/wilderness/arena、p2-return-home、p3-depart、p4-reunion-yidao/rescue/tower-battle）+ 1 MERGED（p2-reunion，2 links ✓）+ 2 UNRESOLVED pending（p2-hospital、p3-farewell，正式层零 link）；
- v5 中未挂载到 thin slice 的事件（12 个）：暗线（tianying-qingfeng / tianying-fakedeath / lizhenzhen-death / lizuo-origin）、奇遇（qiyu-jingzhong / qiyu-xunxia / qiyu-diao）、历史对照（wangqing-battle：canonical 层零 link，audit editorial-only，G2）、PROVISIONAL（p1-chouyuehai）、大火/牺牲（p3-aftermath / yidao-sacrifice / hongxian-death SOURCE_CONFLICT）——均属 secondary branch 或解释层，按 scope gate 不进入第一版主 spine。
