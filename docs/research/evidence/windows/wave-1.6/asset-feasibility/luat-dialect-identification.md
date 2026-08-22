# NEX-002 — LuaT Dialect Identification

> Task-ID: NEX-002 · Owner: Windows · Status: **DONE** · Gate: **DIALECT_PARTIAL_CONSTANTS_READABLE**
> Base: `research/windows-evidence-tooling` @ `42086a7` · 样本：LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]
> 静态只读；未做 full decompiler、未 dump 完整对白、未运行时/内存/密钥/反作弊。

---

## 0. 结论（一句话）

「LuaT」**不是自定义 magic**，而是 **标准 Lua 5.4 bytecode 的 magic `\x1bLua` + 版本字节 `0x54`（= Lua 5.4）**，前面加了 6 字节自定义 envelope 前缀；且 `sizeof(Instruction)=8`（64-bit 指令，标准 Lua 5.4 为 4）——即 **modified Lua 5.4**。叙事字符串（江晏/清河/EXPANSION_QINGHE/…）以**明文、长度定界**形式内联在 bytecode 内容里，可定位、可部分结构化关联，但**常量表的完整 deterministic 枚举需 NEX-003**（因 64-bit 指令 + 修改版头部）。

---

## 1. Phase A — LuaT envelope 解析

```text
+0x00  u32            变值（语义未定；非 block 大小）
+0x04  u16 = 0x03F6   固定（envelope 标志/版本）
+0x06  "\x1bLua"      标准 Lua magic（4B）   ← 之前误读为 "LuaT"
+0x0A  0x54           LUAC_VERSION = Lua 5.4
+0x0B  0x00           LUAC_FORMAT = official
+0x0C  19 93 0D 0A 1A 0A   LUAC_DATA（与标准 Lua 5.x 完全一致）
+0x12  04             sizeof(int)
+0x13  08             sizeof(size_t)
+0x14  08             sizeof(Instruction) = 8  ← 修改版（标准=4，即 64-bit 指令）
+0x15  78 56 00 01 00 ?? ?? 28 77 40 01 ?? 40   ← 修改版头尾（LUAC_INT/NUM 区域，非标准值）
+0x21  "@"            标准 Lua source 前缀
+0x22  源码路径字符串   hexm/client/storyline_data/… 或 Sunshine/AI/bt2code/…
+…      bytecode 内容  字符串常量表（中文+ID）+ 代码段
```

**源码路径分段**（LT71[1768]）：`@hexm/client/storyline_data` + len `16` + `wanfa/MSD_ST/ZDQ` + `dq_610900.lua` —— 即路径按段长度定界。

---

## 2. Phase B — Fingerprint（基于结构证据，非猜测）

| 证据 | 观察 | 判定 |
| --- | --- | --- |
| magic | `1B 4C 75 61` = `\x1bLua`（4 样本一致 @ +0x06） | **标准 Lua** |
| version byte | `0x54` = 84 | **Lua 5.4**（5.1=0x51 / 5.2=0x52 / 5.3=0x53 / 5.4=0x54） |
| format byte | `0x00` | official |
| LUAC_DATA | `19 93 0D 0A 1A 0A`（精确匹配） | 标准 Lua 完整性数据 |
| sizeof(int)/(size_t) | `04` / `08` | 标准 |
| sizeof(Instruction) | `08` | **modified**（标准=4 → 64-bit 指令） |
| envelope 前缀 | `u32 + u16 0x03F6` | 自定义封装 |
| 头尾 | `78 56…` / `28 77 40…` 非标准完整值 | 修改版（LUAC_INT/NUM 自定义或字段重排） |

→ **结论：modified Lua 5.4**（非 LuaJIT `\x1bLJ`，非 5.1/5.2/5.3，非纯自定义序列化）。

---

## 3. Phase C — 六个 locator 是否结构化 constant/key

| locator | 位置（样本） | 结构化证据 |
| --- | --- | --- |
| `EXPANSION_QINGHE` | LT71[1631] +0x556 | 紧邻 key `expansion_id`（+0x548），key→value 结构 |
| `dq_610900` | LT71[1768] +0x54 | 源码路径段 `…/ZDQ/dq_610900.lua`，属 source 字符串 |
| `NodeGraphData` | LT71[1768]（+0x656 区域） | 剧情图标识符（字段名） |
| `TextByNo` | LT71[1631] +0x525 | 字段名（key） |
| `70276` | LT31[874] +0x17B6 | 紧邻对话文本「清河这般大…」（+0x17C6），**ID↔文本** |
| `江晏` | LT71[1768] +0x06D4 | 紧邻 key `name`（+0x06C9），key→value 结构 |

**判定**：这些 locator **属于 bytecode 内的结构化字符串常量/键**（表构造 key→value 或 source 字符串），非游离文本；但**常量表的逐条 deterministic 枚举**仍依赖 NEX-003 解码修改版 proto/constant 编码（见 §4）。

---

## 4. Phase D — proto/constant boundaries（未做 opcode semantics）

- 源码路径（source 字符串）可确定性定位（`@` @ +0x21，段长定界）。
- 叙事字符串为**明文长度定界**（如 `name`→`江晏`、`expansion_id`→`EXPANSION_QINGHE`、`70276`→对话文本），在 bytecode 内容中，无需密钥即可读取。
- **未完成**：因 `sizeof(Instruction)=8`（64-bit 指令）与修改版头尾，尚未确定 code 段大小 → 常量表精确偏移；完整 constant/proto 枚举留待 NEX-003（Minimal Constant/Proto Reader）。

---

## 5. Gate

> **DIALECT_PARTIAL_CONSTANTS_READABLE**

- Dialect：**IDENTIFIED**（modified Lua 5.4，证据充分）。
- Constants：**PARTIAL READABLE** —— 字符串明文可定位、可部分 key↔value 关联；完整确定性枚举需 NEX-003（不改 dialect 结论，仅补 proto/constant 边界）。

## 6. 边界 / 未做

- ✅ 仅 4 个样本静态只读；未 bulk 扫描、未 dump 对白全文。
- 🛑 未做 full Lua decompiler、未做 opcode semantics、未运行时/内存/hook、未研究密钥/反作弊。
- 🛑 未开始 NEX-003（Minimal Constant/Proto Reader），未改 canonical dataset。

## 7. 下一步（待 Lead 放行）

NEX-003 只需在「modified Lua 5.4」基础上：确认 64-bit 指令的 code 段大小计算 → 定位常量表 → 逐条读 tag+length+bytes。风险低（明文、无密钥），工程量小。
