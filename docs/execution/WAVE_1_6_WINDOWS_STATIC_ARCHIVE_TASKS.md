# Wave 1.6 — Windows Static Archive Research Task Packet

> Status: **ACTIVE / SUPERSEDES WINDOWS W-01~W-07 EXECUTION ORDER**  
> Updated: 2026-08-23  
> Owner: Windows Research Station  
> Parent direction: `docs/WAVE_1_6_NARRATIVE_DIRECTION.md`  
> Parent task map: `docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md`

## 0. Lead 决议

Windows 当前主路径从：

```text
人工游戏内采集
→ W-01 / W-02 / W-03
```

调整为：

```text
静态安装目录研究
→ .mpkinfo 结构识别
→ index ↔ archive 定位
→ 资源目录筛选
→ 叙事 metadata 候选探测
→ 决定是否需要最小 extractor
```

原因：操作者当前不希望把人工采集作为主要数据生产方式；同时公开资料存在转载 lineage、任务层级与游戏内精确字符串仍有缺口，因此静态 metadata shortcut 的潜在收益已经提高。

人工采集不取消，但降为：

> **FALLBACK_ONLY：只有静态研究无法解决且确实阻塞 P0 narrative question 时才执行。**

---

# 1. 不可突破的边界

本 Task Packet 只允许对**本机已安装游戏的静态文件**做离线、只读研究。

## 允许

- 复制单个 `.mpkinfo` / 小型测试 `.mpk` 到独立研究目录；
- 读取 header / magic / version / count；
- 统计字节结构、entry 长度、字符串、扩展名；
- 推断普通 index 字段，如 path/name/offset/size/hash/type；
- 编写只读 parser；
- 使用标准压缩库处理格式中明确标识的普通压缩；
- 从 archive 中定位并提取少量**非敏感、已知类型**样本，例如 shader / 普通 metadata，用于验证映射；
- 生成资源 catalog 与文件 hash；
- 搜索 quest/task/story/localization 等资源名称或 metadata key。

## 禁止

- 破解或获取加密密钥；
- 绕过 DRM、访问控制或受保护资源；
- 注入运行中的游戏进程；
- runtime memory dump / hook；
- 读取或对抗反作弊；
- 修改客户端文件；
- patch loader / DLL injection；
- 为获得完整结果而研究受保护解密链；
- 大规模导出、发布完整对白、语音、CG、贴图、模型、脚本资产。

### Global STOP

如果下一步的必要条件变成：

```text
需要密钥
需要运行时解密
需要注入/Hook
需要绕过访问控制
需要反作弊相关操作
```

立即：

> **STOP / NO_GO**

并输出当前已知证据，不继续扩大范围。

---

# 2. 工作分支与输出范围

建议 Windows 使用：

```text
research/windows-evidence-tooling
```

Windows worker 若受 `CLAUDE.md` contract 约束，则 worker **不得 commit/push**；由操作者/Lead 在 review 后完成 Git 操作。

## 推荐 Git 目录

```text
docs/research/evidence/windows/wave-1.6/
├── README.md
├── evidence-ledger.csv
└── asset-feasibility/
    ├── install-inventory.md
    ├── mpkinfo-structure.md
    ├── archive-linkage.md
    ├── resource-catalog-summary.md
    ├── narrative-metadata-probe.md
    └── static-extraction-decision.md

tools/research/windows-static-archive/
├── README.md
├── inspect_mpkinfo.py
├── probe_archive_mapping.py
└── catalog_resources.py
```

### 不进入 Git

- 原始 `.mpk`；
- 原始 `.mpkinfo`；
- 全量 hex dump；
- 大型 extracted asset；
- raw screenshots/videos；
- 任何包含完整游戏内容的大型导出物。

---

# 3. 当前已知基线

来自 W-06 handoff，后续任务应保留但不擅自升级：

```text
Install root: E:\yysls
Resource shape: .mpk + binary .mpkinfo
Resources.mpkinfo observed version: 3
Observed entry count: 625
Observed extensions include: .ps / .vs / .cs
Plain quest/localization/string table: NOT_FOUND
patch_config / patchlist / extra_version: OPAQUE representation
Current classification: ARCHIVED_BUT_INDEXED + OPAQUE
```

额外观察：

```text
No literal qinghe patch group observed
Possible qingzhou/pkg/world grouping: UNRESOLVED
```

不得把 `qingzhou = 清河` 当作事实。

---

# 4. 新任务顺序

```text
W-R00 Baseline Freeze
   ↓
W-R01 MPKINFO Structural Inspection
   ↓
W-R02 Deterministic Index Parser
   ↓
W-R03 Index → Archive Linkage Probe
   ↓
W-R04 Resource Catalog & Narrative Filter
   ↓
W-R05 Narrative Metadata Candidate Probe
   ↓
W-R06 Static Extraction Decision Packet
   ↓
J-02R Lead Decision
```

任务必须顺序推进。前一项无法满足 Gate 时，不得为了“继续研究”跳过边界进入下一项。

---

# 5. W-R00 — Baseline Freeze & Research Copy

**Status**: READY  
**Depends on**: W-00, W-06

## 目标

冻结当前游戏版本与研究输入，避免更新后同名资源改变却无法追踪。

## 操作

1. 记录：
   - install root；
   - patching_version；
   - pkgversion；
   - 文件 mtime；
2. 对研究用 `.mpkinfo` 与其对应 `.mpk` 计算 SHA-256；
3. 复制**最小必要文件**到独立 read-only research working directory；
4. 不修改原安装目录；
5. 记录 Windows / Python 版本与研究脚本版本。

## 输出

`asset-feasibility/research-baseline.md` 或追加到 `install-inventory.md`。

## 验收

必须能回答：

> “后续 parser 结果对应哪一个确切游戏版本和哪一组确切文件？”

## STOP

无法确认输入 provenance 时停止。

---

# 6. W-R01 — MPKINFO Structural Inspection

**Status**: READY_AFTER_W-R00

## 目标

不尝试解 archive，只回答 `.mpkinfo` 到底是怎样的 index。

## 必须回答

1. magic/header 是否稳定；
2. version 字段是否能稳定读取；
3. entry count 是否能从 header 独立得到；
4. entry 是固定长度还是 variable length；
5. 是否存在：
   - UTF-8 / UTF-16 / ASCII path；
   - filename；
   - extension；
   - hash；
   - offset；
   - compressed size；
   - original size；
   - flags/type；
6. entry 间边界是否可以 deterministic 地复现。

## 允许方法

- hex viewer；
- `strings` 类扫描；
- Python `struct`；
- 字节分布/长度统计；
- 多个 entry 交叉比较；
- 对已知 shader 名称/扩展名做 locator 验证。

## 不允许

- 猜测字段后直接标成“格式已破解”；
- 为解释未知字段去研究运行时加载器；
- 扩大到游戏进程。

## 输出

`asset-feasibility/mpkinfo-structure.md`

建议表格：

```text
offset / field_candidate / width / endian / confidence / evidence / unresolved
```

## Gate R1

只有满足：

> 至少能 deterministic 枚举 entry，并识别出 path/name/type 或 offset/size 中的一组高价值字段

才进入 W-R02。

否则：

> `MPKINFO_PARSE = NO_GO`

---

# 7. W-R02 — Deterministic Index Parser

**Status**: WAITING_FOR_R1

## 目标

把 W-R01 的结构观察变成一个**只读、可重复** parser，而不是靠 hex viewer 手工判断。

## 建议脚本

`tools/research/windows-static-archive/inspect_mpkinfo.py`

## 最小 CLI

```text
python inspect_mpkinfo.py <file.mpkinfo> --summary
python inspect_mpkinfo.py <file.mpkinfo> --list --limit 50
python inspect_mpkinfo.py <file.mpkinfo> --extensions
```

## parser 输出至少包含

若格式确实存在这些字段：

```text
entry_index
name/path/hash
extension/type
offset
stored_size
original_size
flags
```

未知字段保留：

```text
unknown_0xNN
```

不要为了好看删除未知数据。

## 验收

- 同一输入多次运行结果一致；
- entry count 与 W-R01 一致；
- 至少 3 个已知可识别 entry 可回溯到原始字节位置；
- parser 对 malformed/truncated copy fail-closed，不 silent guess。

## STOP

如果 parser 必须依赖未知密钥/运行时状态才可继续，NO_GO。

---

# 8. W-R03 — Index → Archive Linkage Probe

**Status**: WAITING_FOR_R2

## 目标

验证 `.mpkinfo` 的 entry 是否能静态定位到对应 `.mpk` payload。

不是做全量 extraction。

## 优先选择样本

选择已知低风险、非剧情内容：

- shader `.ps/.vs/.cs`；
- 明显的配置/metadata；
- 小体积、类型容易判断的资源。

## 必须回答

1. entry 如何映射到哪个 `.mpk`；
2. offset 是否直接指向 payload；
3. stored_size 是否正确；
4. 是否有普通压缩；
5. 提取出的 payload 是否能由 magic/扩展名正常识别；
6. 不借助运行中游戏是否可以完成上述流程。

## 输出

`asset-feasibility/archive-linkage.md`

记录：

```text
sample_entry
source_mpkinfo
source_mpk
offset
size
payload_magic
compression
result
```

## Gate R3

### PASS

```text
index → archive → payload
```

可完全静态、确定性完成，并且 payload 未显示受保护加密。

状态：

> `STATIC_EXTRACTION_FEASIBLE`

### PARTIAL

index 可解析，但 payload 位置/普通压缩仍有少量静态格式问题：

> `STATIC_EXTRACTION_PARTIAL`

### NO_GO

payload 明显需要密钥、运行时解密或受保护访问链：

> `STATIC_EXTRACTION_NO_GO`

立即停止，不研究密钥来源。

---

# 9. W-R04 — Resource Catalog & Narrative Filter

**Status**: WAITING_FOR_R3_PASS_OR_SAFE_PARTIAL

## 目标

优先得到**资源目录**，而不是解出所有资源。

## 输出 catalog

建议：

```text
resource_id
path_or_name
extension/type
archive
size
flags
candidate_category
```

## Narrative filter 关键词

仅作为候选筛选，不等于语义事实：

```text
quest
task
story
chapter
mainstory
mission
scenario
dialog
dialogue
npc
character
localization
locale
string
text
subtitle
mingchao
anchong
hidden
qishu / qiyu
wan-shi-zhi / wanshizhi
qinghe
qingzhou
```

同时考虑：

- 英文名；
- 拼音；
- hash-only resource；
- 无明文名称但同目录/同类型聚类。

## 输出

- `resource-catalog-summary.md`
- 本地完整 catalog（默认不提交 Git，若很小且仅 metadata 可再评估）

## 验收

回答：

> “是否存在一批明显值得继续看的 narrative / localization / quest metadata candidates？”

不要批量导出内容资产。

---

# 10. W-R05 — Narrative Metadata Candidate Probe

**Status**: WAITING_FOR_R4

## 目标

只对少量 narrative candidates 做定向 probe，判断它们是不是我们真正需要的结构 metadata。

## 优先字段

```text
quest_id / task_id
quest_title_key
chapter_id
parent_id
prerequisite
sort/order
category
region
npc_ref
story_thread
unlock_condition
localization_key
```

## 核心原则

> **只证明 schema/metadata 是否存在，不建设完整剧情文本数据库。**

如果某资源同时含大量对白/脚本：

- 只记录结构字段；
- 不把全文提交 Git；
- 不把完整文本复制进项目数据集。

## 输出

`asset-feasibility/narrative-metadata-probe.md`

每个 candidate：

```text
candidate_id
resource locator
why_selected
format
observed fields
usefulness
confidence
copyright/scope note
```

## Gate R5

### HIGH VALUE

找到能直接支撑 TITLE/HIERARCHY/ORDER/PREREQUISITE 的稳定 metadata。

### LIMITED VALUE

只能看到资源名、localization key 或零散 ID，不能重建任务结构。

### NO VALUE

没有可用剧情结构 metadata。

---

# 11. W-R06 — Static Extraction Decision Packet

**Status**: WAITING_FOR_R5_OR_EARLY_STOP

## 目标

把 Windows 端结果收口成 Lead 可以直接决策的 packet。

## 输出

`asset-feasibility/static-extraction-decision.md`

必须包含：

### A. Provenance

```text
game version
input hashes
scripts used
branch/commit if applicable
```

### B. Capability Matrix

| Capability | Result |
| --- | --- |
| enumerate mpkinfo entries | YES/NO |
| recover resource names/types | YES/PARTIAL/NO |
| recover archive mapping | YES/PARTIAL/NO |
| static extract benign payload | YES/PARTIAL/NO |
| find narrative candidates | YES/PARTIAL/NO |
| find stable quest metadata | YES/PARTIAL/NO |
| requires protected bypass | YES/NO |

### C. Recommendation

只允许：

- `MINIMAL_EXTRACTOR_GO`
- `CATALOG_ONLY_GO`
- `STATIC_RESEARCH_PARTIAL`
- `NO_GO`

### D. 下一步

若 GO，只提出下一阶段 proposal；**本 task 不扩成正式 extractor 产品工程**。

---

# 12. J-02R — Lead Asset Research Decision

**Owner**: Lead  
**Status**: WAITING

Lead 只回答一个问题：

> 静态资源路线是否已经证明能以低风险、可重复方式获得产品真正需要的 canonical/narrative metadata？

## 可能结果

### 1. MINIMAL_EXTRACTOR_GO

满足：

- static only；
- 不需要 protected bypass；
- 能显著降低人工采集；
- 能输出稳定 task/story metadata；
- provenance 可重复。

之后另起 extractor proposal，不在 Windows research branch 直接产品化。

### 2. CATALOG_ONLY_GO

能稳定列目录/资源类型，但 metadata 深度不足。

用途：帮助 Mac 定向研究，不做正式 extractor。

### 3. NO_GO

需要 protected bypass，或收益明显不足。

此时人工采集仍只用于少数 P0 缺口，不恢复为全量主路径。

---

# 13. 原 Windows 任务状态调整

| Task | 新状态 | 说明 |
| --- | --- | --- |
| W-00 Baseline/Evidence Workspace | CLOSED | 已完成 |
| W-01 明潮/暗涌 UI Capture | HOLD / FALLBACK_ONLY | 暂停人工采集 |
| W-02 Qinghe Native Structure | HOLD / FALLBACK_ONLY | 静态研究优先 |
| W-03 又见新来燕 Flow Capture | HOLD / FALLBACK_ONLY | 静态研究优先 |
| W-04 Narrative Surface Inventory | HOLD | 等静态结果；必要时再做 |
| W-05 Targeted Recheck | WAITING | 仅未来 P0 unresolved 使用 |
| W-06 Installation Inventory | DONE / BASELINE | 作为 W-R00 输入 |
| W-07 old Metadata Probe | SUPERSEDED | 被 W-R01~R06 受控流程替代 |

---

# 14. Windows 当前立即执行顺序

只执行下面三项，不要提前做后续：

```text
1. W-R00 — Baseline Freeze
2. W-R01 — MPKINFO Structural Inspection
3. 若 R1 PASS → W-R02 — Deterministic Index Parser
```

完成 R2 后先回报 Lead，再决定是否进入 W-R03。

## 第一轮统一回报格式

```text
Task-ID: W-R00 / W-R01 / W-R02
Status:
Branch / Commit:
Game Version:
Input Hashes:
Changed Files:
Parser Result:
Entry Count:
Recognized Fields:
Unknown Fields:
Evidence:
Boundary Check:
Unresolved:
Risks:
Gate Result: R1_PASS | R1_NO_GO | R2_PASS | R2_NO_GO
Next:
```

---

# 15. 当前成功标准

第一轮不是“解出燕云剧情”。

第一轮只需要证明或否定：

> **`.mpkinfo` 是否是一个足够稳定、可静态解析的资源索引，能够让我们在完全离线、无需解密/注入/反作弊的情况下定位 archive 中的普通资源。**

只有这件事成立，继续做 narrative metadata extractor 才有工程意义。
