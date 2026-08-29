# W-R05 — Narrative Metadata Schema Probe

> Task-ID: W-R05 · Owner: Windows · Status: **DONE** · Gate: **R5_SCHEMA_AND_JOIN_FOUND**
> Scope：LT71 为主，LT51/LT31 交叉核对。静态只读，未 dump 完整对白、未运行时、未研究密钥/反作弊。
> Git 证据仅保留 schema/offset/ID/hash/短 locator，不提交游戏原文。

---

## 0. 结论（一句话）

叙事数据 = **`"LuaT"` 容器包裹的编译后 Lua 脚本**。LT 块是游戏客户端 Lua（storyline_data 剧情数据 / MSD_ST 主线 / AI 行为树 / UI），内含**中文字符串常量**（清河、江晏、天泉、红线…）与**稳定 ID**（`EXPANSION_QINGHE`、`70276`、`dq_610900`），且 **ID/命名空间可跨 entry 重现** → Schema 与 Join 均已找到。

---

## 1. 关键格式发现（Phase A）

LT 块头（4 个样本 + LT1/LT261 一致）：

```text
+0x00  u32            变值（非 block 大小，语义待定）
+0x07  "LuaT"         容器 magic（4 字节）
+0x0B  固定头(~11B)   + 变值字节 + 固定尾(~7B)
+0x21  源码路径字符串  如 hexm/client/storyline_data / wanfa/MSD_ST/ZDQ/dq_610900.lua
+…     编译后 Lua 内容  字符串常量表（中文 + ID）+ 函数/标识符
```

- 内容为**编译后 Lua**（常量表 + 代码，非纯文本源码）；magic 为 `LuaT`（非标准 `\x1bLua`/`\x1bLJ`，属自定义封装）。
- 中文与 ID 以**字符串常量**形式内联，非外部 localization 表。

### 样本证据（短 locator 仅此）

| 样本 | 内容类别 | 关键字符串（短 locator） |
| --- | --- | --- |
| LT71[1631] flags=142 | UI 脚本 | `hexm/client/ui/…/cangpin_…lua`；`area_name`/`TextByNo`/`expansion_id`/`EXPANSION_QINGHE` |
| LT71[1768] flags=142 | **storyline_data** | `hexm/client/storyline_data`、`wanfa/MSD_ST/ZDQ/dq_610900.lua`、`NodeGraphData`、`name` + 江晏/天泉/线… |
| LT51[1178] flags=102 | UI 脚本 | `hexm/client/ui/windows/common/_player_float.lua`；清河命中处为「…级（繁…度）…清河…」 |
| LT31[874] flags=62 | **AI 行为树** | `Sunshine/AI/bt2code/output/u_newplay_horserob_thin_qifen.lua`；`TREE_NAME`/`NODES_NUM`/`StartDialog`/`ShowSubtitle`/`NpcCall`；**`70276` + 对话文本** |

---

## 2. Phase B — flags 相关性

- flags_raw 实测 = **2 × LT 归档号**：LT1→2、LT31→62、LT51→102、LT71→142、LT91→182、LT261→522。
- 结论：**flags 是 per-archive 常量，不预测 schema**（同一 archive 内所有 entry 同值）。不得给 flags 赋 quest/npc 语义。

## 3. Phase C — repeated record schema（字段状态）

| 字段/结构 | 状态 |
| --- | --- |
| `LuaT` 容器头（magic+固定头+源码路径） | **CROSS_ENTRY_CONFIRMED** |
| Lua 常量表（字符串常量 + 中文 + 数字串） | **CROSS_ENTRY_CONFIRMED** |
| `EXPANSION_QINGHE` | **SEMANTIC_CANDIDATE**（区域/扩展 ID） |
| `storyline_data` / `MSD_ST` / `wanfa/…` | **SEMANTIC_CANDIDATE**（剧情命名空间） |
| `70276`（紧邻清河对话）、`dq_610900` | **SEMANTIC_CANDIDATE**（对白/任务 ID 字符串） |
| `name` / `area_name` / `TextByNo` / `expansion_id` | **FIELD_CANDIDATE**（schema 字段名） |
| `NodeGraphData` / `get_variables` / `StartDialog` / `ShowSubtitle` | **FIELD_CANDIDATE**（剧情图/对话触发字段） |

## 4. Phase D — Join 证据

| ref | 重现范围 | 结论 |
| --- | --- | --- |
| `EXPANSION_QINGHE` | LT71×4、LT51×7、LT31×2（13 entry / 3 archive） | **CROSS_ENTRY_CONFIRMED** |
| `storyline_data` | LT71 × **671** entry | **CROSS_ENTRY_CONFIRMED** |
| `MSD_ST` | LT71 × 43 entry | CROSS_ENTRY_CONFIRMED |
| `StartDialog` | LT71 × 14 entry | CROSS_ENTRY_CONFIRMED |
| `70276` → 清河对话文本 | LT31[874] 单 entry（`70276` 后紧接「清河这般大…」） | **ID↔文本 join（entry 内）** |

---

## 5. 六个必答

1. **江晏所在 entry 是什么结构** → `LuaT` 容器 + 编译 Lua：`storyline_data`（`wanfa/MSD_ST/ZDQ/dq_610900.lua`），含 `NodeGraphData`（剧情图）+ 常量表（`name`→江晏、天泉、线…）。即**主线剧情脚本**。
2. **清河多个 entry 是否共享 schema** → **是**。LT71/LT51/LT31 的清河 entry 均为 `LuaT` 容器 + 编译 Lua 常量表结构，仅内容（UI/剧情/AI）不同。
3. **文字附近是否有稳定 ID/ref** → **是**。`70276`（对白 ID 字符串）紧邻清河对话；`dq_610900`（任务 ID）；`EXPANSION_QINGHE`（区域）；`name`/`area_name`/`TextByNo`/`expansion_id`（字段键）。
4. **相同 ref 能否跨 entry 重现** → **是**。`EXPANSION_QINGHE` 13 entry/3 archive；`storyline_data` 671 entry；`MSD_ST` 43；`StartDialog` 14。
5. **flags_raw 是否预测 schema** → **否**。flags = 2×归档号（per-archive 常量）。
6. **是否存在 localization/string table join** → **部分**。文本内联于 Lua 常量表（未见独立 localization 表），但 `TextByNo` + 数字字符串 ID（`70276`）提示存在「按编号取文本」机制，可能是 localization 间接层（需后续确认）。

---

## 6. Gate

> **R5_SCHEMA_AND_JOIN_FOUND**

- Schema：`LuaT` 容器 + 编译 Lua 常量表 → CROSS_ENTRY_CONFIRMED。
- Join：`EXPANSION_QINGHE` / `storyline_data` / `MSD_ST` / `StartDialog` 跨 entry 重现 + `70276`↔对话文本。

## 7. 对项目目标的影响（供 Lead 决策，非本轮任务）

- 游戏原生任务/剧情结构在**客户端 Lua 脚本**里（`storyline_data`、`MSD_ST`、AI 树 `StartDialog/ShowSubtitle/NpcCall`），含任务 ID、区域常量、角色/地点名、对白文本。
- 要得到**干净的 quest/task 结构化 metadata**，需解析 `LuaT` 容器 + 编译 Lua 常量表（比 `.mpkinfo` 索引更深一层，但仍是**纯静态**；保护/加密为 **NOT_OBSERVED_IN_TESTED_SCOPE**）。
- 注意版权边界：Lua 内含大量对白原文，**只提结构字段/ID/hash，不批量导出文本**。

## 8. 下一步（W-R06 决策包，待 Lead 放行）

综合 R03–R05，形成 static-extraction-decision packet：`MINIMAL_EXTRACTOR_GO` / `CATALOG_ONLY_GO` / `STATIC_RESEARCH_PARTIAL` / `NO_GO`。
