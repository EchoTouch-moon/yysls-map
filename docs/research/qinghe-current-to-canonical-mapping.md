# Qinghe Current → Canonical Mapping（现状 → 游戏原生任务映射）

> 阶段：Wave 1.5 / Canonical Story Alignment — Task 4
> 性质：research artifact，非 frozen content。不修改 content/。
> 状态枚举：EXACT / MERGED / SPLIT / EDITORIAL_ONLY / MISSING / UNRESOLVED（定义见下）。
> 映射对象：v5 冻结集 27 个 StoryEvent + 1 个 StoryArc（qinghe-main-journey）10 个 beat。
> Canonical 参照：docs/research/qinghe-canonical-story-inventory.md（节点 ID 前缀 qh-）。

> **Lead 修正（2026-08-22）**：「神仙不渡城镇段」= PROVISIONAL_GROUP（非 canonical node）；红线/伊刀之死 = UNRESOLVED + SOURCE_CONFLICT；"16 年 vs 三年" = TEMPORAL_WORDING_REVIEW；第一版 canonical scope = 清河主章主线。

## 0. 状态定义

- EXACT：当前节点与某个游戏原生任务/剧情节点一一对应（内容层面）。
- MERGED：当前节点把 ≥2 个游戏原生节点合并表达。
- SPLIT：当前节点被拆成多个条目，与一个原生节点不完整对应（本数据集无此情形）。
- EDITORIAL_ONLY：当前节点是项目策展/解读产物，不对应任何游戏任务节点（历史对照、编辑导读）。
- MISSING：游戏原生节点在当前数据集完全缺失。
- UNRESOLVED：映射关系存在来源冲突，无法确认。

## 1. StoryArc 层级映射

| 当前对象 | 值 | Canonical 对应 | 判定 |
| --- | --- | --- | --- |
| chapter | 第一章·神仙不渡（清河，progress=qinghe, rank=10） | 游戏第一章·神仙不渡（清河区域） | EXACT |
| story_arc qinghe-main-journey | "清河主线：从失玉到离乡"（12 分钟导读） | 游戏主线任务"神仙不渡"（四篇） | **EDITORIAL_ONLY**：arc 是项目自撰导读线（标题/核心问题/幕次文案），不是游戏任务；顺序与游戏四篇大体一致但不等于任务簿结构 |
| arc 的 10 个 beat | 幕次（role=setup/clue/escalation/…） | 四篇主线中的稳定剧情节点 | 见 §2 逐条判定 |
| progress 语义 | start / qinghe（全章通关可见） | 游戏内进度 = 章节级（全章通关） | EXACT（粒度粗：无篇级/任务级进度） |

## 2. 10 个 beat 的逐条映射

| # | beat | event | 叙事角色 | Canonical 节点 | 判定 | 证据/说明 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | beat-prologue-attack | evt-prologue-attack | setup | qh-00 序章④黑衣人袭击夺玉（竹林小屋） | **EXACT** | sohu 843193673：捏脸后竹林小屋被袭夺玉；内容一一对应。任务簿名称 UNRESOLVED 不影响内容映射 |
| 2 | beat-p1-awaken | evt-p1-awaken | clue | qh-01a 竹林旧居线索（红线唤醒/罐中信/灵位） | **EXACT** | ali213 第 1 页步骤 1–4 |
| 3 | beat-p1-arena | evt-p1-arena | escalation | qh-01e 将军祠擂台（方旭/老金） | **EXACT** | ali213 第 1 页步骤 15–19 |
| 4 | beat-p2-return-home | evt-p2-return-home | clue | qh-02a 回神仙渡打听 | **EXACT** | ali213 第 8 页步骤 1–2（打听对象"周叔叔"vs v5"江叔"——人名细节 UNRESOLVED） |
| 5 | beat-p2-reunion | evt-p2-reunion | turning_point | qh-02b 寒姨重逢 + qh-02c 瓷窑/地下仓库（瘦老弟/伊刀） | **MERGED** | 一个 event 合并了篇二的两个原生子节点；guide 文案以"家的幻象+地下仓库异常"双主题覆盖两者 |
| 6 | beat-p2-hospital | evt-p2-hospital | escalation | qh-02e 活人医馆/弱水岸 或 qh-01b 神仙不渡段·医馆井 | **UNRESOLVED** | ali213 第 7 页（神仙不渡段）与第 8 页（匹马映林嘶）都进入医馆井区域；v5 event 的"寒姨房刺杀/伊刀/破庙屋顶"又对应 qh-02f → 该 event 实际横跨两个原生段（其中"神仙不渡段"为 PROVISIONAL_GROUP，Lead 决策 1） |
| 7 | beat-p3-aftermath | evt-p3-aftermath | consequence | 不羡仙大火·劫后余生 | **UNRESOLVED** | 大火任务边界未定（见 inventory §2.5）；ali213 攻略文本未含大火桥段，v5 为主要来源 |
| 8 | beat-wangqing-battle | evt-wangqing-battle | turning_point | 中渡桥之战（作品化历史对照，暗线身世锚点） | **EDITORIAL_ONLY** | 游戏无名为"中渡桥之战"的任务节点；这是项目策展的历史—作品对照节点（含 3 张历史卡），用于解释王清/江晏前史 |
| 9 | beat-p4-rescue | evt-p4-rescue | resolution | qh-04 为谁归去·回不羡仙救人（宋九/广胡子/丁巳） | **EXACT** | ali213 第 10 页步骤 1–6 |
| 10 | beat-p4-tower-battle | evt-p4-tower-battle | resolution | qh-04 为谁归去·酒香塔击败千夜 | **EXACT** | ali213 第 10 页步骤 7–10 |

**Beat 统计：EXACT 6 / MERGED 1 / SPLIT 0 / EDITORIAL_ONLY 1 / MISSING 0 / UNRESOLVED 2。**

> 注：SPLIT=0 是因为 10 个 beat 全部有对应事件；真正的问题不是"拆分过度"，而是 **beat 覆盖不到游戏任务全貌**（见 §4 MISSING）。

## 3. 27 个 StoryEvent 的逐条映射

| event（slug） | part | Canonical 节点 | 判定 | 说明 |
| --- | --- | --- | --- | --- |
| prologue-escape | 0 | qh-00 序章①–③（江晏出逃/陈子奚/无相皇） | EXACT | 内容对应；但一个 event 合并了三个原生场景（粒度粗，见 §5） |
| prologue-attack | 0 | qh-00 序章④ 黑衣人袭击夺玉 | EXACT | |
| p1-awaken | 1 | qh-01a 竹林旧居线索 | EXACT | |
| p1-cross-bridge | 1 | qh-01b 断桥 | EXACT | |
| p1-archery | 1 | qh-01c 北竹林学射 | EXACT | NPC 名（冯继升/冯继生）UNRESOLVED |
| p1-wilderness | 1 | qh-01d 百草野遇天涯客 | EXACT | 粒度粗（见 §5） |
| p1-arena | 1 | qh-01e 将军祠擂台 | EXACT | |
| p1-chouyuehai | 1 | qh-01b（神仙不渡段·揭穿胡为） | EXACT（内容） | **v5 part=1 但 canonically 属于篇一与篇二之间的神仙不渡段** → part 归属与攻略目录不一致 |
| p2-return-home | 2 | qh-02a 回神仙渡打听 | EXACT | |
| p2-reunion | 2 | qh-02b + qh-02c | MERGED | 寒姨重逢 + 瓷窑/地下仓库/伊刀战 合并 |
| p2-hospital | 2 | qh-02e（医馆/弱水岸）+ qh-02f（寒姨房刺杀/伊刀） | UNRESOLVED | 或含 qh-01b 医馆井段；ali213 两个篇都进医馆井 |
| p3-aftermath | 3 | 不羡仙大火·劫后余生 | UNRESOLVED | 任务边界未定 |
| p3-farewell | 3 | 竹隐居告别红线 | UNRESOLVED | 攻略未明确定位到篇 |
| p3-depart | 3 | qh-03 菱花尘满·酒香塔留信辞行 | EXACT | ali213 第 9 页步骤 5（"回屋留信"） |
| p4-reunion-yidao | 4 | qh-04 破庙汇合伊刀 | EXACT | |
| p4-rescue | 4 | qh-04 救人（宋九/广胡子/丁巳/杜乔仙/袁金刚） | EXACT | 粒度粗（见 §5） |
| p4-tower-battle | 4 | qh-04 酒香塔击败千夜 | EXACT | |
| qiyu-jingzhong | 0 | 奇遇·井中人 | EXACT | 奇遇类 |
| qiyu-xunxia | 0 | 奇遇·寻侠之路 | EXACT | 奇遇类 |
| qiyu-diao | 0 | 奇遇·清河有雕 | EXACT | 奇遇类 |
| tianying-qingfeng | 0 | 暗线·清风驿之变（井中人奇遇见证） | EXACT | 暗线锚点（官方确认） |
| tianying-fakedeath | 4 | 暗线·田英假死北上（黎中兑） | EXACT | 跨章伏笔（v5 归入 part 4） |
| lizhenzhen-death | 0 | 暗线·黎蓁蓁（月神）湖底殉情 | EXACT（内容） | 任务锚点 UNRESOLVED（与红尘无眼"月神"意象疑似相关） |
| yidao-sacrifice | 3 | 不羡仙大火·伊刀舍身 | **UNRESOLVED + SOURCE_CONFLICT** | v5 表述与攻略流程存在矛盾（为谁归去中伊刀仍在协助）；死亡时点/是否分支未确认 |
| hongxian-death | 3 | 不羡仙大火·红线中箭 | **UNRESOLVED + SOURCE_CONFLICT** | v5 内部自相矛盾（p4-tower-battle 说"带红线去酒香塔"）；需游戏内验证 |
| wangqing-battle | 0 | 中渡桥之战（作品化历史对照） | EDITORIAL_ONLY | 非任务节点 |
| lizuo-origin | 0 | 暗线·李祚/柳青衣前史 | EXACT（内容） | 前史 lore 节点 |

**Event 统计：EXACT 20 / MERGED 1 / SPLIT 0 / EDITORIAL_ONLY 1 / UNRESOLVED 5。**

## 4. 当前完全缺失的游戏原生节点（MISSING）

1. **神仙不渡城镇段完整流程**：朱八碗集碗、王阙换碗、仇越海传授（摄星拿月）、宋九/北盟遗址话术、酒窖探查、无名玉笛、解谜"思芳歌"、武学（泥犁三垢/积矩九剑）、BOSS 寻心——v5 仅以 evt-p1-chouyuehai（揭穿胡为）覆盖其中一小段。
2. **菱花尘满 酒香塔段**：塔底/缆车/钥匙/梳妆台流程（仅留信被 evt-p3-depart 覆盖）。
3. **全部侠迹/残章（≥8–10 个）**：河山如故、荒祠暗影、金玉手、红尘无眼、暮云何物、阴阳如影、千佛残墟、长夜有虹、独行杀手、皮影幕起——v5 全部缺失。
4. **全部镇守（≥6–7 个）**：弱水岸、不羡仙、佛光顶（田英线主载体）、菩提苦海、春秋别馆、荧渊、神秘巨像——v5 全部缺失。
5. **绝大部分奇遇**：清河奇遇 38–50 个，v5 仅 3 个（井中人/寻侠之路/清河有雕），覆盖率约 6–8%。
6. **序章细节节点**：无相皇教学战、陈子奚挡刀（并入 evt-prologue-escape，未独立）。
7. **篇二收尾**：舞马人 BOSS 战、破庙救红线/广胡子。
8. **篇四收尾**："滴答"带回神仙渡。

## 5. StoryEvent 粒度评估

### 过粗（一个 event 横跨多个原生节点）
- evt-prologue-escape：江晏出逃 + 陈子奚同行挡刀 + 无相皇阻击（3 个原生场景）。
- evt-p2-reunion：寒姨重逢 + 刘三爷/陆瘦子 + 瓷窑宋九 + 地下仓库 + 伊刀战。
- evt-p2-hospital：医馆二楼/井暗道 + 寒姨房刺杀 + 伊刀推石门 + 破庙屋顶逃脱（横跨 qh-02e/qh-02f，甚至可能涉及 qh-01b）。
- evt-p1-wilderness：天涯客舆图 + 驱熊 + 偷师太极 + 宝箱 + 五音启太平前置。
- evt-p3-aftermath：大火后与红线/广胡子/寒姨/伊刀的多段对话合并。
- evt-p4-rescue：救人 + 杜乔仙 + 袁金刚登高。

### 粒度问题小结
- 主线节点：以"剧情功能"切分（导火索/线索/转折），**不以任务目标切分**，导致一个 event 常跨多个任务步骤。
- 暗线/奇遇节点：以 lore 单元切分，粒度适中，但完全没接任务簿（无 quest 引用）。
- 结论：StoryEvent 的切分轴是"叙事段落"，不是"游戏任务目标"——这是与 canonical 对齐时最核心的粒度错位。

## 6. 当前 event slug 是否足以作为未来 canonical deep-link anchor？

**结论：不足（但可作次级锚点）。**

- 已成立：event slug 稳定、唯一，且已被 /timeline?beat={event_slug} 使用；人物页、历史页、e2e 均依赖它。
- 不足点：
  1. deep link 解析依赖"事件出现在某 arc beat 中"（TimelineExplorer 逐个请求 arc 详情比对）；27 个 event 只有 10 个在 beat 中 → 其余 17 个事件无法被 /timeline?beat= 定位到幕次。
  2. canonical 节点（篇、任务、侠迹、镇守、奇遇、暗线锚点）没有自己的 slug；大量原生节点（寻心、舞马人、朱八碗、思芳歌、酒香塔缆车……）在数据集中没有对应 event。
  3. 一个 event 可跨多个原生节点（§5），反向"event→canonical 节点"不是单射。
- 建议（仅提案，不实施）：未来 canonical 层应有自己的 slug 体系（如 quest/quest-node slug），event slug 保留为次级锚点；deep link 语法可升级为 /timeline?node={canonical_slug} 并向后兼容 ?beat=。

## 7. 三个特别问题的直接回答

1. **哪些 beat 能明确落到游戏原生任务节点？** 6 个：prologue-attack（序章）、p1-awaken / p1-arena（篇一·又见新来燕）、p2-return-home（篇二·匹马映林嘶）、p4-rescue / p4-tower-battle（篇四·为谁归去）。
2. **哪些 beat 是项目策展的解释节点？** 1 个明确：wangqing-battle（中渡桥之战，历史—作品对照）。另 5 个 beat 的"为什么重要/下一问"文案属于编辑解读，但事件本体在游戏内存在；beat 5（p2-reunion）的"家的幻象"叙事框架是编辑组织方式，事件本体为篇二真实节点。
3. **哪些游戏剧情节点完全缺失？** 见 §4：神仙不渡城镇段（寻心；该段本身为 PROVISIONAL_GROUP）、菱花尘满大部分、全部侠迹、全部镇守、绝大部分奇遇、舞马人、序章细分节点。

## 8. 与 v5 part 字段的一致性检查

| v5 part | 内容 | 与 canonical 篇对齐 |
| --- | --- | --- |
| 0 | 序章 + 暗线 + 奇遇 + 历史对照 | 非篇（混合桶）——与任何"篇"不对应 |
| 1 | p1-* + 揭穿胡为 | ≈ 篇一·又见新来燕，但揭穿胡为 canonically 属于篇一/篇二之间的神仙不渡段 |
| 2 | p2-* | ≈ 篇二·匹马映林嘶 |
| 3 | p3-* + 红线/伊刀之死 | ≈ 篇三·菱花尘满（含未决的牺牲节点） |
| 4 | p4-* + 田英假死 | ≈ 篇四·为谁归去 |

part 大体对应四篇，但 (a) part 0 是混合桶，(b) 揭穿胡为归入 part 1 与攻略目录不符，(c) 该字段在导入 DB 时被丢弃（见 architecture reality summary #2）。
