# Canonical Qinghe Story Inventory（研究草稿）

> 阶段：Wave 1.5 / Canonical Story Alignment — Task 2+3
> 性质：**research artifact，非 frozen content**。仅记录建立剧情骨架所需的 metadata 与原创摘要；不复制游戏对白/攻略原文。
> 规则：所有无法从公开资料确认的信息一律标 UNRESOLVED；禁止猜测。不修改 content/、不修改 schema。

> **Lead 决议修正（2026-08-22，Wave 1.5 Phase A/B ACCEPTED 后）**：
> 1. 「神仙不渡城镇段」仅标 PROVISIONAL_GROUP / UNRESOLVED，**不得进入正式 Canonical Story Layer**；
> 2. 红线/伊刀之死统一标 **UNRESOLVED + SOURCE_CONFLICT**，不设计剧情分支、不采"多数表述"；
> 3. "16 年 vs 三年"标 **TEMPORAL_WORDING_REVIEW**，除非出现真正互斥证据，不称为 factual contradiction；
> 4. 第一版 canonical scope = **清河主章主线**；侠迹/镇守/奇遇/明暗故事为 secondary narrative branch，不进第一版主 spine。

## 0. 方法学与置信度约定

- 来源分级：OFFICIAL（官方站/官方访谈）> WALKTHROUGH（可验证任务/攻略目录，游侠/3DM/游民/17173）> WIKI/DB（灰机 wiki 等公共数据库）> PLAYER（玩家公开流程/视频标题）> REPO-SRC（仓库现有 v5 sources 内文）。
- 置信度：HIGH（≥2 个独立来源一致，且含官方或主流攻略）；MEDIUM（1 个主流来源，或 2 个来源有细节出入）；LOW（单一弱来源或来源间冲突）；UNRESOLVED（无法确认，禁止猜测）。
- 命名变体（如"又见新燕来/又见新来燕"）一律并列记录并标 UNRESOLVED，不作为结论。
- 主线顺序以可验证攻略目录为准（ali213《全剧情流程图文攻略汇总》1599605 第 1–10 页；3DM《清河主线主章侠迹残章》3977244；游民星空《主线及残章支线任务图文攻略》1864988）。

## 1. 顶层骨架（已确认部分）

| 层级 | 值 | 确认度 | 来源/证据 |
| --- | --- | --- | --- |
| 游戏 | 燕云十六声（Where Winds Meet） | HIGH | 官方站 yysls.cn；v5 dataset.game |
| 章节 | 第一章·神仙不渡 | HIGH | v5 dataset.content_scope；3DM 3976025（"清河区域的主线任务名为神仙不渡"）；17173（"第一章神仙不渡第二篇·匹马映林嘶"）；bilibili 系列标题"第一章 神仙不渡（一）（二）" |
| 区域 | 清河 | HIGH | v5 chapters；多攻略 |
| 清河子区域 | 百草野（含 4 小块）、隐月山、神仙渡（疑似共 3 块，含竹林旧居） | MEDIUM | 游民星空 1864988（"百草野是清河地区的三块区域之一…百草野又内含四块区域"）；红尘无眼攻略（隐月山）；神仙渡攻略页；竹林旧居见 9game 10752129。**UNRESOLVED：清河子区域确切清单与数量** |
| 主线任务名 | 神仙不渡（清河主线 = 一条长主线，分四篇） | HIGH | 3DM 3976025 原文："清河区域的主线任务名为神仙不渡…每个阶段主线分别是又见新来燕、匹马映林嘶、菱花尘满和为谁归去" |
| 下一章节 | 第二章·开封新客（开封区域） | HIGH | 游民星空 1864988 导航"第二章-开封新客"；ali213 1599605 第 11 页起 |
| 序章 | 游戏开场教学段：江晏携婴出逃（QTE）→ 陈子奚（玉山君）断后 → 无相皇（教学 Boss）→ 时间跳转 16 年 → 捏脸 → 黑衣人袭击夺玉 | HIGH（内容） | 搜狐《全主线流程图文攻略》843193673；bilibili BV1Nc6fYUEb9（"序章（江晏 陈子奚 无相皇 白发男）"）；v5 evt-prologue-escape/attack。**UNRESOLVED：序章在武林录中的任务名称** |
| 任务簿分类 | 主线（主章）/ 侠迹（残章）/ 奇遇 / 明暗故事；游历另含：镇守 / 据点 / 众生 / 万事知 / 野外首领 | HIGH | 游民星空 1864988（"地图上的书本标志是残章支线任务，对应武林录中的'侠迹'"）；3DM 3976138（游历七小节）；bilibili"明暗故事·清河" |
| 叙事结构 | 主线 + 暗线（暗线铺在世界探索玩法中） | HIGH（官方） | 官方访谈《大剧透！燕云没有主线剧情？》（yysls.cn 20230112）：清河主线=少年遇江湖人；暗线基于历史"清风驿之变"；主角身世关联"中渡桥之战" |
| 暗线锚点 | 清风驿之变（田英/悬剑），经井中人奇遇见证 | HIGH | 官方访谈；v5 evt-tianying-qingfeng（其 impact 自述由井中人奇遇见证） |

## 2. 主线（神仙不渡）四篇节点清单

### 2.1 序章（节点 qh-00）
- 名称：序章（游戏内任务簿名称 UNRESOLVED）｜node_type: prologue｜parent: 第一章·神仙不渡（前置）｜order: 0｜prev: —｜next: qh-01
- 稳定剧情节点：①江晏携婴+镇冠珏逃离绣金楼（了结义父王清/梦傀情节，作品设定）②陈子奚同行并为主角挡刀（玉山君）③无相皇阻击（教学 Boss，被蓝色小虫操控复活）④16 年后黑衣人袭击夺玉（竹林小屋）
- 来源：搜狐 843193673；v5 evt-prologue-escape / evt-prologue-attack；官方访谈（身世关联中渡桥之战）
- 置信度：HIGH（内容）；UNRESOLVED（任务簿名称、时间线"16 年"与 v5"三年后（主角十六岁）"措辞不一致）

### 2.2 第一篇·又见新来燕（节点 qh-01；命名变体：又见新燕来）
- node_type: main_quest（篇一）｜parent: 第一章·神仙不渡｜order: 1｜prev: qh-00｜next: qh-01b
- 命名变体：ali213/3DM/bilibili 作"又见新来燕"；v5 冻结集作"又见新燕来"；9game 两式混用 → **UNRESOLVED 游戏内精确字符串**
- 稳定剧情节点（sub-nodes，parent=qh-01）：
  - qh-01a 竹林旧居线索：红线唤醒、罐中信、灵位（对应 v5 evt-p1-awaken）— HIGH
  - qh-01b 断桥（桥断，轻功过桥；对应 v5 evt-p1-cross-bridge）— HIGH
  - qh-01c 北竹林学射（NPC 冯继升/冯继生，射术心得+比试；对应 v5 evt-p1-archery）— HIGH（NPC 名写法 UNRESOLVED）
  - qh-01d 百草野遇天涯客（清河舆图、驱熊偷师太极；对应 v5 evt-p1-wilderness）— HIGH
  - qh-01e 将军祠擂台（方旭/老金，听风辨位、手套、新外观；对应 v5 evt-p1-arena）— HIGH
- 来源：ali213 1599605 第 1 页；sohu 843193673；bilibili BV1ZL6fYMEer（"第一章 神仙不渡（一）又见新来燕（江晏 红线 冯继升 广胡子 老金）"）；v5 事件
- 置信度：HIGH

### 2.3 神仙渡城镇段（节点 qh-01b，ali213 称"神仙不渡「主章」"）
- node_type: **PROVISIONAL_GROUP**（Lead 决策 1：不得进入正式 Canonical Story Layer；ali213 单列"神仙不渡「主章」"，3DM/游民未单列——是否独立任务节点 UNRESOLVED；进入条件：游戏内任务簿观察 / 明确任务目录 / 第二个独立可信来源）｜parent: 第一章·神仙不渡｜order: 1.5（位于又见新来燕与匹马映林嘶之间）｜prev: qh-01｜next: qh-02
- 稳定剧情节点：朱八碗集碗/换碗（王阙）→ 仇越海对话 → 隔空取物揭穿胡为（对应 v5 evt-p1-chouyuehai）→ 宋九（北盟遗址学话术）→ 酒窖探查 → 医馆后院井（火箭/火盆/石室）→ 无名玉笛 → 解谜"思芳歌"（无脸人/无面人）→ 学武（泥犁三垢、积矩九剑）→ 击败 BOSS 寻心
- 来源：ali213 1599605 第 7 页；ali213 1598677（神仙不渡主线攻略）；v5 evt-p1-chouyuehai
- 置信度：MEDIUM（内容 HIGH；是否独立任务节点 UNRESOLVED）

### 2.4 第二篇·匹马映林嘶（节点 qh-02；17173 称"第二篇祸源：匹马映林嘶"）
- node_type: main_quest（篇二）｜parent: 第一章·神仙不渡｜order: 2｜prev: qh-01b（或 qh-01）｜next: qh-03
- 稳定剧情节点（sub-nodes，parent=qh-02）：
  - qh-02a 回神仙渡打听（NPC 周叔叔；对应 v5 evt-p2-return-home）— HIGH（"打听对象是周叔叔还是江叔"UNRESOLVED）
  - qh-02b 不羡仙与寒姨重逢（刘三爷/陆瘦子上酒；对应 v5 evt-p2-reunion）— HIGH
  - qh-02c 瓷窑/地下仓库（宋九、瘦老弟、地下仓库与伊刀交战；对应 v5 evt-p2-reunion 尾部）— HIGH
  - qh-02d 鬼寺暗道（伺机逃脱、暗道回不羡仙）— HIGH
  - qh-02e 活人医馆/弱水岸（医馆二楼、井、无面人首领石门、"字迹模糊的信"、窦豆豆；对应 v5 evt-p2-hospital 的医馆/暗道部分）— HIGH
  - qh-02f 寒姨房间刺杀与伊刀（跟踪黑衣人、石像机关、推石门、破庙屋顶；对应 v5 evt-p2-hospital 的遭遇/伊刀部分）— HIGH（17173 3976025/271545 段落）
  - qh-02g 破庙救红线与广胡子、主殿 BOSS 舞马人 — HIGH
- 来源：ali213 1599605 第 8 页；17173 162133494（"第一章神仙不渡 第二篇匹马映林嘶攻略"）；3DM 271545（匹马映林嘶任务攻略）；bilibili BV1onrcYkErP（"第一章 神仙不渡（二）匹马映林嘶（寒姨 千夜 刀哥 无面人 舞马人）"）；v5 事件
- 置信度：HIGH（"祸源"是否为官方篇名 UNRESOLVED；"千夜"于本篇首次现身，见 18183 全任务汇总）

### 2.5 第三篇·菱花尘满（节点 qh-03）
- node_type: main_quest（篇三）｜parent: 第一章·神仙不渡｜order: 3｜prev: qh-02｜next: qh-04
- 稳定剧情节点：酒香塔（塔底/缆车/钥匙）→ 回屋留信（对应 v5 evt-p3-depart）→ 梳妆台解锁新发型；另有竹隐居告别红线（v5 evt-p3-farewell，攻略未明确定位 → 篇归属 UNRESOLVED）
- 不羡仙大火（v5 evt-p3-aftermath / evt-yidao-sacrifice / evt-hongxian-death 的背景）：大火发生的确切任务边界（菱花尘满尾部？为谁归去开头？）**UNRESOLVED**；ali213 攻略文本未含大火桥段。
- **Lead 决策 2**：红线/伊刀之死统一标 **UNRESOLVED + SOURCE_CONFLICT**（v5 与攻略流程矛盾，且 v5 内部自相矛盾），不设计分支、不采"多数表述"；等待游戏内观察或更强证据。
- 来源：ali213 1599605 第 9 页；百度知道 2130051928167805427（菱花尘满主线任务攻略，repo src-baidu-linghua）；v5 事件
- 置信度：MEDIUM（篇存在 HIGH；大火归属与告别红线定位 UNRESOLVED）

### 2.6 第四篇·为谁归去（节点 qh-04）
- node_type: main_quest（篇四）｜parent: 第一章·神仙不渡｜order: 4｜prev: qh-03｜next: 第二章·开封新客
- 稳定剧情节点：破庙汇合伊刀（对应 v5 evt-p4-reunion-yidao）→ 回不羡仙救人（宋九/广胡子/丁巳；杜乔仙、袁金刚登高；对应 v5 evt-p4-rescue）→ 带红线赴酒香塔、协助伊刀、与老者入塔 → 击败幕后之人"千夜"→ 带"滴答"回神仙渡（对应 v5 evt-p4-tower-battle）
- 来源：ali213 1599605 第 10 页；v5 事件
- 置信度：HIGH（"滴答"身份 UNRESOLVED）

## 3. 侠迹/残章（清河）节点清单

来源：3DM 3977244 导航（侠迹·卷一~卷七+终卷）；游民星空 1864988；18183 6886638；ali213 1599605 第 2–5 页；3DM 3976138（侠迹定义=次主线，补暗潮故事）。
"残章任务=武林录中的侠迹"（游民星空 1864988）→ 两词同指，ali213 用"残章"、3DM/游民用"侠迹·卷N"。

| 节点 | node_type | order（侠迹卷号） | prev/next | 关键内容（原创摘要） | 置信度/备注 |
| --- | --- | --- | --- | --- | --- |
| qh-xj-01 河山如故 | side_quest（侠迹·卷一） | 1 | — / qh-xj-02 | 百草野南部遗址，救烈不灭，点火炬、地下将军雕像、字谜机关；引出燕北盟 | HIGH（3DM 3976138 文+18183） |
| qh-xj-02 荒祠暗影 | side_quest（侠迹·卷二） | 2 | qh-xj-01 / qh-xj-03 | 将军祠，小石头，千斤顶入洞取蹴鞠 | HIGH（ali213 第 2 页；18183） |
| qh-xj-03 金玉手 | side_quest（侠迹·卷三） | 3 | qh-xj-02 / qh-xj-04 | 严奇人解穴，学奇术金玉手 | HIGH（ali213 第 3 页；18183） |
| qh-xj-04 红尘无眼 | side_quest（侠迹·卷四） | 4 | qh-xj-03 / qh-xj-05 | 隐月山，天涯客地图，燕陌陌/天不收，湖底机关、寒玉匣眼睛、月神夙愿 | HIGH（ali213 第 5 页） |
| qh-xj-05 暮云何物 | side_quest（侠迹·卷五） | 5 | qh-xj-04 / qh-xj-06 | 内容未获取；ali213 将其列于开封段（1599605 第 22 页）→ 区域归属 UNRESOLVED | MEDIUM |
| qh-xj-06 阴阳如影 | side_quest（侠迹·卷六） | 6 | qh-xj-05 / qh-xj-07 | 内容未获取；同上有区域归属疑点 | MEDIUM |
| qh-xj-07 千佛残墟 | side_quest（侠迹·卷七） | 7 | qh-xj-06 / qh-xj-08 | 千佛村、夜梦僧、天火；bilibili 标"清河"，ali213 序列表置于开封段 → **区域 UNRESOLVED** | MEDIUM |
| qh-xj-08 长夜有虹 | side_quest（侠迹·终卷） | 8 | qh-xj-07 / — | 佛光塔顶调时、塔底机关、佛像光线解谜；与镇守·佛光顶（田英）相邻 | HIGH |
| qh-xj-09 独行杀手 | side_quest（侠迹/残章） | UNRESOLVED | — | 游民/18183 列入清河；ali213 置于开封段 → 区域 UNRESOLVED | MEDIUM |
| qh-xj-10 皮影幕起（皮影师） | side_quest（残章？奇遇？） | UNRESOLVED | — | 皮影师 BOSS 战（皮影召唤/龙卷风）；ali213 第 4 页列为残章；3DM/18183 未列 → 分类 UNRESOLVED | MEDIUM（名称"皮影幕起/皮影幕启"UNRESOLVED） |

## 4. 镇守（清河）节点清单

来源：3DM 3977244 导航；游民星空 1864988；ali213（部分页标注）。node_type: garrison。

| 节点 | 关联主线/内容 | 置信度 |
| --- | --- | --- |
| 镇守·弱水岸 | 匹马映林嘶 关联（3DM 第 2 页同页） | HIGH |
| 镇守·不羡仙 | 为谁归去 关联（3DM 第 4 页同页） | HIGH |
| 镇守·佛光顶 | 田英线（bilibili BV1c8rnYuELj）；与侠迹·终卷长夜有虹同页 | HIGH |
| 镇守·菩提苦海 | 3DM 第 13 页 | HIGH |
| 镇守·春秋别馆 | 3DM 第 15 页 | HIGH |
| 镇守·荧渊 | 3DM 第 14 页 | HIGH |
| 镇守·神秘巨像 | 游民星空列为镇守；ali213 列为残章 → 分类 UNRESOLVED | MEDIUM |

## 5. 奇遇（清河）

- 清河奇遇总数：游民星空称 **50** 个（对应文章 2062714），9game 称 38 个 → **UNRESOLVED**（两攻略统计口径不同）。
- 已确认名称（与 v5 相关）：花海无颜（ali213 第 6 页；丑娘/螳螂/姚药药）、井中人（v5 evt-qiyu-jingzhong；见证清风驿之变）、寻侠之路（v5 evt-qiyu-xunxia）、清河有雕（v5 evt-qiyu-diao）、酒逢知己（神仙渡酒摊独饮客）。
- v5 仅收录 3 条奇遇事件 → 覆盖率为个位数百分比（UNRESOLVED 是否统计漏项）。

## 6. 暗线（明暗故事·清河）

| 节点 | node_type | 内容（原创摘要） | 来源/置信度 |
| --- | --- | --- | --- |
| 清风驿之变 | hidden_line_anchor | 田英执行悬剑任务：护契丹使入南唐，驿馆刺杀嫁祸南唐；官方确认清河暗线由此延伸 | 官方访谈；v5 evt-tianying-qingfeng — HIGH |
| 绣金楼 | hidden_faction/据点 | 追杀主角的暗势力（总部为据点）；主角身世与镇冠珏的关联方 | v5 factions/events；360game/9game"绣金楼总部据点" — HIGH |
| 田英假死北上 | hidden_line_node | 田英借主角之手假死，换脸化名黎中兑北上契丹 | v5 evt-tianying-fakedeath — MEDIUM（单一来源，社区分析） |
| 黎蓁蓁（月神） | hidden_line_node | 湖底殉情（v5 evt-lizhenzhen-death）；与红尘无眼侠迹（月神）疑似同一意象 → 关联 UNRESOLVED | v5；ali213 红尘无眼 — MEDIUM |
| 李祚/柳青衣前史 | hidden_line_node（前史） | 唐哀帝李祚与柳青衣旧事（900–943 年），绣金楼渊源 | v5 evt-lizuo-origin；repo src-toutiao-lizuo — MEDIUM |
| 中渡桥之战（作品化） | work_history_node | 946 年王清/杜重威桥战史实 + 作品虚构（王清=主角生父、梦傀、江晏了结王清）；v5 以 evt-wangqing-battle 表达，并配 3 张历史卡 | v5；官方访谈（身世关联）；STORY_GUIDE_SPEC 历史卡 — HIGH（史实）/ MEDIUM（作品细节） |

## 7. 必须标注 UNRESOLVED 的清单（汇总）

1. 序章在任务簿中的任务名称；序章与第一章的精确归属边界。
2. "又见新来燕" vs "又见新燕来" 的游戏内精确字符串（v5 冻结集为后者，两份攻略目录为前者）。
3. ali213 单列的"神仙不渡「主章」"（朱八碗→寻心）是否为独立任务节点（3DM/游民未单列）→ PROVISIONAL_GROUP（Lead 决策 1，不得进入正式 Canonical Story Layer）。
4. 不羡仙大火的精确任务边界（菱花尘满尾部 / 为谁归去开头）；v5 中红线/伊刀之死标 **UNRESOLVED + SOURCE_CONFLICT**（v5 与攻略流程矛盾：为谁归去中红线仍随队赴酒香塔；Lead 决策 2：不设计分支）。
5. 菱花尘满篇内各节点的任务内顺序（竹隐居告别红线、留信、梳妆台）。
6. 暮云何物/阴阳如影/千佛残墟/独行杀手/神秘巨像/皮影幕起的区域归属与任务分类（清河 vs 开封；残章 vs 镇守 vs 奇遇）。
7. 清河子区域清单与数量（疑似百草野/隐月山/神仙渡 3 块）；清河奇遇总数（38 vs 50）。
8. "祸源"（17173）、"追缉"（bilibili）是否为匹马映林嘶的官方篇名/副标题。
9. 时间线措辞：v5"三年后（主角十六岁）" vs 攻略"16 年后" → 标 **TEMPORAL_WORDING_REVIEW**（Lead 决策 3：十六年前出逃与三年前失踪可同时成立，暂不判定事实冲突；待查是否存在"三年后归来"等相对时间参照）。
10. 千夜首次登场的确切任务节点（18183 称匹马映林嘶中"见过千夜"，v5 将最终战置于为谁归去——两者不矛盾，但首次登场节点未确认）。
11. "滴答"身份（为谁归去结尾带回神仙渡的对象）。
12. 冯继升/冯继生 人名写法。

## 8. 来源与可追溯性

### 8.1 本次调研引用的公开来源（URL）
- 官方访谈（主线+暗线、清风驿之变、中渡桥之战）：https://www.yysls.cn/news/official/20230112/37780_1063057.html（repo src-official-narrative-interview）
- ali213 全剧情流程图文攻略汇总（第 1–10 页）：https://app.ali213.net/gl/1599605.html 及 _2.._10.html（repo src-ali213-all）
- ali213 神仙不渡主线攻略：https://app.ali213.net/gl/1598677.html
- 3DM 清河主线主章侠迹残章任务做法介绍（16 页导航）：https://www.3dmgame.com/gl/3977244.html 及 _2.._16.html（repo src-3dm-qinghe）
- 3DM 清河神仙不渡主线流程分享：https://www.3dmgame.com/gl/3976025.html（及 _3/_4 页）
- 3DM 游历侠迹介绍：https://www.3dmgame.com/gl/3976138.html
- 游民星空 主线及残章支线任务图文攻略：https://wap.gamersky.com/gl/Content-1864988.html
- 游民星空 清河奇遇触发条件与位置整理（50 个）：https://wap.gamersky.com/gl/Content-2062714.html（repo src-gamersky-qiyu）
- 18183 全任务图文攻略汇总：https://m.18183.com/xinyou/6886638.html
- 搜狐 全主线流程图文攻略（序章细节）：https://www.sohu.com/a/843193673_258858
- 17173 第一章神仙不渡第二篇·匹马映林嘶：https://news.17173.com/z/yy16s/content/11132024/162133494.shtml（repo src-17173-qinghe2）
- 9game 第一章通关攻略（第一章=神仙不渡）：https://a.9game.cn/yyslskfsjwx/10771502.html
- 9game 又见新燕来 / 又见新来燕 两式页面（命名变体证据）：https://www.9game.cn/yyslskfsjwx/10756501.html / https://www.9game.cn/yyslskfsjwx/10773761.html
- bilibili 视频标题（篇序与人物）：BV1ZL6fYMEer（篇一）、BV1onrcYkErP（篇二）、BV1Nc6fYUEb9（序章）、BV1c8rnYuELj（镇守·佛光顶/田英）、BV1L26zYjEz3（千佛残墟）、BV1aW6eYdEEJ（杀神出庙）
- 灰机 wiki（yy16s.huijiwiki.com）：存在"序章"等词条，但 Cloudflare 拦截无法抓取正文 → 只能作为存在性证据，正文待本地网络环境核验

### 8.2 与仓库既有 sources 的对应
- src-ali213-all / src-3dm-qinghe / src-gamersky-qiyu / src-17173-qinghe2 / src-official-narrative-interview 均被本次调研复核，结论一致。
- src-baidu-pima / src-baidu-linghua / src-toutiao-qinghe-full 未逐字复核（百度知道页面抓取受限），引用其标题级信息。

## 9. 本地游戏资源研究可行性注记（feasibility note，非行动）

当前缺口：任务簿精确名称、篇内任务边界、奇遇完整清单、区域划分、精确时间线——这些字段在公开资料中**互相冲突或缺失**（见 §7）。
目前**尚未出现**"必须研究本地游戏资源（解包/客户端文件）"的决定性证据：所有骨架级信息（章节、四篇主线、侠迹卷、镇守、暗线锚点）都能由 ≥1 个公开来源支撑，
缺口集中在精确字符串与边界细节。若后续需要把 canonical 节点精确到"任务簿条目级"（如确认'神仙不渡'是否独立成章、确认 50 个奇遇的官方名册），
公开资料将触顶，届时才进入解包/本地资源研究评估。本阶段不采取任何解包动作。
