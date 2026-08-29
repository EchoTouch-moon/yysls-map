# NEX-002 — LuaT Dialect Identification（H-NEX-002 修订版）

> Task-ID: NEX-002 · Status: **REVIEW_REQUIRED → 修正后 DONE** · Gate: **DIALECT_PARTIAL_CONSTANTS_READABLE**
> Base: `research/windows-evidence-tooling` @ `ba0dbf7` · 样本：LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]
> 修订原因：初版把 Lua 5.3 的 5-size-field 模型套到了 Lua 5.4 上，误判 64-bit Instruction。

---

## 0. 修订结论（替换初版）

「LuaT」= **6 字节自定义前缀 + 标准 Lua 5.4 binary chunk**：

```text
+0x00  u32 (变值)             自定义前缀
+0x04  u16 = 0x03F6           自定义前缀（固定）
+0x06  "\x1bLua"              标准 Lua magic
+0x0A  0x54                   Lua 5.4
+0x0B  0x00                   format = official
+0x0C  19 93 0D 0A 1A 0A      LUAC_DATA（精确匹配标准）
+0x12  04                     sizeof(Instruction) = 4   ← 标准 32-bit 指令
+0x13  08                     sizeof(lua_Integer) = 8
+0x14  08                     sizeof(lua_Number) = 8
+0x15  …（12B，见 §2）        修改版头尾（LUAC_INT/NUM 区域，非标准）
+0x21  "@" + 源码路径         标准 Lua source 前缀
```

**初版错误**：把 `04 08 08` 读成 `sizeof(int)=4 / sizeof(size_t)=8 / sizeof(Instruction)=8`（Lua 5.3 模型），并据此判 `64-bit Instruction`。**这是错的**——Lua 5.4 在 LUAC_DATA 后只有 3 个 size byte。

---

## 1. 标准兼容性验证（逐字段）

| 字段 | 偏移（绝对） | 观测 | 判定 |
| --- | --- | --- | --- |
| signature | 0x06 | `1B 4C 75 61` | 标准 |
| version | 0x0A | `0x54` | **Lua 5.4** |
| format | 0x0B | `0x00` | 标准 |
| LUAC_DATA | 0x0C–0x11 | `19 93 0D 0A 1A 0A` | 精确匹配 |
| sizeof(Instruction) | 0x12 | `04` | 标准（32-bit） |
| sizeof(lua_Integer) | 0x13 | `08` | 标准 |
| sizeof(lua_Number) | 0x14 | `08` | 标准 |
| LUAC_INT | 0x15–0x1C | `78 56 00 01 00 ?? ?? 28` | **DIVERGES**（标准 `78 56 00 00 00 00 00 00`） |
| LUAC_NUM | 0x17–0x1E（若对齐 370.5） | `00 01 00 ?? ?? 28 77 40` | **DIVERGES**（标准 `00 00 00 00 00 28 77 40`） |

**关键**：`sizeof(Instruction)=4` → **标准 32-bit 指令**；`LUAC_INT/LUAC_NUM` 区域与标准值**不匹配**，第一个 divergence 在 **绝对偏移 0x18**（LUAC_INT 第 4 字节：观测 `01`，标准 `00`）。

---

## 2. Header 尾（0x15–0x20，12B）——修改版

四样本一致模式：

```text
78 56 00 01 00 ?? ?? 28 77 40 01 ?? 40
├─ 78 56        = 0x5678 片段（LUAC_INT 头）
├─ 00 01 00     固定
├─ ?? ??        变值（非标准、非固定）→ 疑似自定义字段
├─ 28 77 40     370.5 尾部（LUAC_NUM 尾）
├─ 01           固定
├─ ??           变值
└─ 40           = "@"（source 前缀，0x21）
```

结论：**size 字段标准、指令 32-bit；但 LUAC_INT/LUAC_NUM 完整性常量被修改（且含变值字段）**。这不是「标准 Lua 5.4」也不是「modified dialect 64-bit」，而是：

> **Lua 5.4 chunk（32-bit Instruction） + 6-byte 外层前缀 + 修改版 header 尾（自定义完整性常量/字段）**。

---

## 3. source 字符串（H3）

- `"@"` 前缀在 **0x21**（绝对），后接 `hexm/…` 或 `Sunshine/…`。
- 标准 Lua 5.4 的 source 经 `loadSize()`（7-bit varint 长度）+ 字节；但本格式 source 前的字节（0x20，变值）不构成有效 varint 长度 → **source 长度编码与标准不一致，需 NEX-003 确认**。
- 删除初版的 fixed-offset 假设 `source = sig_pos + 0x1B`（那是碰巧对，但非由标准布局推导）。

## 4. 六个 locator 重新分类（H4）

未解析 `loadConstants` 前，**不得**把字符串一律标为 STRING_CONSTANT/key-value：

| locator | 新分类 | 理由 |
| --- | --- | --- |
| `dq_610900` | **SOURCE_STRING** | 属 source path 段 `…/ZDQ/dq_610900.lua` |
| `江晏` | **CHUNK_STRING_CANDIDATE** | 邻近 key `name`，但 constant 归属未定 |
| `EXPANSION_QINGHE` | **CHUNK_STRING_CANDIDATE** | 邻近 key `expansion_id`，未定 |
| `TextByNo` | **CHUNK_STRING_CANDIDATE** | 字段名样，未定 |
| `NodeGraphData` | **CHUNK_STRING_CANDIDATE** | 标识符样，未定 |
| `70276` | **CHUNK_STRING_CANDIDATE** | 邻近对话文本，未定 |

（初版把它们全部升为「结构化 constant/key」是**过度推断**。）

---

## 5. Gate（H6）

> **DIALECT_PARTIAL_CONSTANTS_READABLE**

- Dialect：**IDENTIFIED**（Lua 5.4，标准 32-bit Instruction，标准 size 字段）。
- Constants：**PARTIAL READABLE** —— 字符串明文可定位，但 header 尾（0x18 起）与 source 长度编码非标准，body/constant 的确定性解析需 NEX-003 先确认 body 布局。

**第一个 divergence**：绝对偏移 **0x18**，字段 = LUAC_INT 区域第 4 字节（观测 `01`，标准 `00`）。

## 6. 对 NEX-003 的影响

- **32-bit 指令已确认** → NEX-003 无需研究「64-bit code 段」，可按官方 loader 顺序（header → upvalue → Proto{source, …, code, constants, …}）做 **Lua 5.4 metadata reader subset**。
- 需 NEX-003 先确认：header 尾（0x15–0x20）的确切字段、source 长度编码、body 起点。
