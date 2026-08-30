# NEX-006 — Windows second-pass targeted evidence list

> Purpose: turn current `PARTIALLY_SUPPORTED` / `CONFLICT` / `UNRESOLVED` rows into auditable native evidence without changing canonical.
>
> Input packet: builder `6c47256be6f42b33826341bf217469be03d4c7ab`, extractor `204c97f0d1a6039860f49a9c4b9232c51ae8d8fa`, game `20260829165912`.
>
> Rule: static first; manual fallback only where explicitly allowed below. No raw asset, full dialogue, or script is committed.

## Priority model

- `P0`：直接关闭 required conflict/UQ 或建立篇一 native identity/hierarchy/order。
- `P1`：关闭角色/隐藏线索解释缺口；不阻塞 frozen canonical 展示。
- 成功产物只保留 bounded observation、hash、archive/entry、byte offset、typed ownership/edge 与最小必要文字片段摘要。
- 静态 `NOT_FOUND` 只有在记录 search universe、term/ID 规范化、工具版本、覆盖 archive 与可复现 query 后才算失败证据；普通 grep miss 不算。

## P0-1 — UQ-02 native title arbitration

- **target claim**：`NEX006-UQ-002`；「又见新来燕」vs「又见新燕来」。
- **required evidence type**：owned localization/task-title record，包含精确 UTF-8 value、string/text ID、task/part ID、region/parent link；若只能确认 UI 呈现则最小任务簿截图。
- **candidate archive / entry / cluster**：优先全量 LT71/LT51/LT31 localization 与 task metadata 索引；现有 12 entries / 7 clusters 均为 negative seed（没有两式字符串），`cluster_id=NONE`，不得在 `qinghe_end_task` 中强配。
- **static procedure**：同时检索两式、去标点/Unicode 规范化值及其 text ID；由命中值反查 owning task record 与 parent part，而非只返回字符串命中。
- **success criterion**：至少一个可重放 owned record 将唯一精确 title 绑定到篇一 task/part；若两式分别属于 UI/旧版本/别处，必须分别给出 scope/version。
- **failure criterion**：覆盖三 archive 的 localization/task universe 后，两式及反向 ID 均无 owned hit，或只有 orphan string/path token。
- **manual fallback**：`YES, conditional` — 静态失败且 UQ-02 阻塞 P0 精确展示时，采集当前 game version 的任务簿标题截图/短录屏；否则保持 `CONFLICT`。

## P0-2 — 篇一 5-node identity / hierarchy / order

- **target claim**：`NEX006-P1-001..005`（5 个 claim 作为同一 parent/sequence graph 验证）。
- **required evidence type**：五个 native task IDs/titles、共同 parent part ID、typed parent-child edges、sequence/prerequisite/sort fields；角色/步骤只作为附加字段。
- **candidate archive / entry / cluster**：LT71/LT51/LT31 task/quest/localization tables；从 P0-1 得到的篇一 part ID 向下反查。现有 `QH_SOURCE/*end*` 是清河终章 surface，不作为篇一 seed；current candidate entry `NONE`。
- **static procedure**：先用 part title/text ID 锁定 owner，再枚举 typed children；对每个 child 返回 archive/index/offset/block hash 与 field ownership。禁止按 byte/entry 顺序填 sort_order。
- **success criterion**：五个 child 与 frozen keys 一一对应，且 parent/order 均来自 typed fields；允许 title 与 editorial canonical title 不同，但需显式记录 mapping。
- **failure criterion**：只能复现 path/token/NodeGraphData，无法分配 owner 或 typed edges；或 child 数/顺序与 frozen spine 冲突。
- **manual fallback**：`YES, conditional` — 静态失败且这些结构阻塞 P0 时，最小任务簿层级/任务接续录屏；若出现冲突，记录 `CONFLICT`，不得以 canonical 覆盖。

## P0-3 — UQ-19 寻心 ↔ 寒姨/寒香寻 identity

- **target claim**：`NEX006-UQ-019`。
- **required evidence type**：character/NPC ID ↔ display name/alias ↔ 寻心 task/BOSS record 的 owned link；换脸身份需明确 variant/form/effect field 或受限剧情上下文。
- **candidate archive / entry / cluster**：全量 LT71/LT51/LT31 character/task/localization；current packet `cluster_id=NONE`, entry `NONE`（没有目标词）。可从篇二/神仙不渡城镇段 task owner 反查，而不是从篇一/end_task 猜测。
- **static procedure**：分别检索 `寻心`、`寒姨`、`寒香寻` 与可能的 text/character IDs；建立 ID graph，保留 negative branches。
- **success criterion**：同一 authoritative record 或可验证 typed edge 明确绑定两身份/形态，且有 game version 与 owner。
- **failure criterion**：仅名字共现、攻略文本镜像、source path 或无 owner 的 string hit；这些均维持 `UNRESOLVED`。
- **manual fallback**：`YES, conditional` — 静态失败且 identity 阻塞 E1/P0 解释时，采集最小 BOSS 名牌/任务文本/过场片段；不提交完整对话。

## P0-4 — UQ-21 mechanism / final-unlock graph

- **target claim**：`NEX006-UQ-021-A`。
- **required evidence type**：明潮/暗涌 resource identity、collection categories、membership edges、completion prerequisite 与 final cutscene/task target。
- **candidate archive / entry / cluster**：
  - `QH_SOURCE/guanqia/qinghe_end_task`: `LT71[502]`, `LT51[2597]`, `LT71[318]`, `LT51[86]`, `LT51[322]`；
  - `QH_SOURCE/guanqia/qinghe_end_task#2`: `LT31[2415]`；
  - `QH_SOURCE/guanqia/qinghe_end_boss_fight`: `LT71[1919]`；
  - `QH_SOURCE/guanqia/qinghe_end_boss_fight/bxx`: `LT51[2232]`；
  - 扩展检索三 archive 的 `明潮`/`暗涌`/collection/localization catalog。
- **static procedure**：先对 8 entries 恢复 owning proto/constant indices 与 typed refs；再用 derived IDs 反查 catalog/localization。`NodeGraphData` 和 `autoStartList` 只能作为结构入口。
- **success criterion**：可重放的 typed graph 同时给出 collection identity、至少一种成员类别、completion predicate 与 final target；部分命中只可将 claim 拆分后标 `PARTIALLY_SUPPORTED`。
- **failure criterion**：只有 `end_task`/`boss_fight` source path、identifier token 或无 owner 的 constants；或无任何明潮/暗涌/collection linkage。
- **manual fallback**：`YES, conditional` — 静态失败且机制阻塞 E1，采集明暗故事 UI 的分类、进度与解锁条件；不采集/提交完整剧情内容。

## P1-1 — UQ-20 official alias occurrence

- **target claim**：`NEX006-UQ-020`。
- **required evidence type**：`少东家`、`寒姨`、`江叔` 各自的 owned localization/dialogue occurrence，含 speaker/addressee 或 quest context；三词独立判定。
- **candidate archive / entry / cluster**：LT71/LT51/LT31 localization/dialogue/text tables；current packet `cluster_id=NONE`, entry `NONE`。
- **static procedure**：精确 term search → text ID → owning record → character/quest context；输出每词 hit count 与 bounded locators，避免摘录完整对白。
- **success criterion**：某称谓至少一个 official in-game owned occurrence即可只提升该词的 evidence role；不能把单词结果扩展到另外两词。
- **failure criterion**：只有 repo/community/walkthrough 使用，或 orphan string 无游戏 owner。
- **manual fallback**：`NO` by default — 该项不阻塞 P0；保持 `COMMUNITY_COMMON` + official usage `UNRESOLVED`。仅 Lead 另行认定为产品阻塞时再启用人工采集。

## P1-2 — UQ-21 Qinghe hidden-thread membership

- **target claim**：`NEX006-UQ-021-B`；燕北盟、换脸术、妙善/田英三组是否属于清河暗涌。
- **required evidence type**：target character/faction/event IDs 与 dark-story collection entries 的 typed membership/story refs；官方清风驿 anchor 单列，不外推整组。
- **candidate archive / entry / cluster**：`QH_SOURCE/task` → `LT51[1943]` (`NodeGraphData@538`, `nodeID@808`)；`QH_SOURCE/task/lizehao` → `LT31[972]` (`NodeGraphData@346`, `nodeID@496`, `is_only_once@574`)；并从 P0-4 的 collection IDs 反查三 archive。现有 filenames 不是 semantic hit。
- **static procedure**：目标词/别名/ID 双向检索；将每组分别绑定 collection member，输出 typed edge 与 owner；未命中组显式 `NONE`。
- **success criterion**：每一组独立出现 owned membership；只命中田英/清风驿不得宣称燕北盟或换脸术也成立。
- **failure criterion**：只有 target term、同文件共现、cluster proximity 或 community claim；维持对应原子项 `UNRESOLVED`。
- **manual fallback**：`YES, conditional per group` — 仅静态失败且该组阻塞 E1 时，采集明暗故事 UI 对应条目；不因另一组成功而补齐本组。

## P1-3 — 冯继升/冯继生与天涯客 identity hardening

- **target claim**：`NEX006-P1-003`, `NEX006-P1-004` 的 character 子项。
- **required evidence type**：native display name + character ID + owned task link；天涯客与「神秘的江湖人」若要等同，还需 explicit alias/identity/story reference。
- **candidate archive / entry / cluster**：由 P0-2 的 archery/wilderness task IDs 反查 character/localization；current packet `cluster_id=NONE`, entry `NONE`。
- **static procedure**：同时检索两种冯姓名写法；分别记录天涯客与官方描述的 IDs/refs，禁止按叙事位置合并。
- **success criterion**：精确 native 人名关闭 spelling conflict；只有 explicit typed relation 才关闭天涯客等同候选。
- **failure criterion**：无 owner string、同场共现或仅 public title；分别保留 `SOURCE_CONFLICT` / `HIGH-CANDIDATE`。
- **manual fallback**：`NO` by default；若 P0-2 已需人工任务簿采集，可顺带记录同一画面可见名字，但不得扩大采集范围。

## Run-level stop / report criteria

第二轮 Windows run 必须逐任务返回：`Task-ID / target claim / archive-entry / observation-offset / evidence type / success-or-failure / limitations / fallback decision`。满足以下任一即停止该任务：

1. 获得满足 success criterion 的 owned evidence；
2. 获得直接冲突证据并登记 `CONFLICT`（不自动覆盖）；
3. 完成定义的 static universe 且满足 failure criterion，按本表决定是否人工 fallback；
4. 遇到 provenance/ownership 不完整，标记 `PROVENANCE_INCOMPLETE`，不得继续作语义解释。
