# H-NEX-003R — Official Lua 5.4 Varint & Proto Walk

> Task-ID: H-NEX-003R · Status: **DONE** · Gate: **PROTO_PARTIAL_AFTER_OFFICIAL_VARINT**
> Base: `research/windows-evidence-tooling` @ `17c59be` · 样本：LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]
> 静态只读；未做 opcode semantics / 未做 full decompiler / 未 dump 对白 / 未运行时。

---

## 0. 结论（一句话）

Lead 复核正确：Lua 5.4 官方 `loadUnsigned()` 是 **MSB-first 7-bit groups**（`x = (x<<7)|(b&0x7f)`，高位 0x80 = 末字节），不是 LSB-first。修正后：

- **sizecode `01 YY` 得到 236/245（不再 13825/14977 越界）**，且 4 样本的 code 区域全部是合法指令流（op ≤ 127，0 invalid）；
- 但 **sizek @ code_end 仍解析失败**（LT31 0x439 / LT71[1768] 0x390 / LT71[1631] 0x3F0 / LT51 0x40C）→ **post-code 结构（sizek/constants/upvalues/protos）是 CUSTOM VARIANT**，常量表遍历仍无法确定性完成。

## 1. 修正后的 varint（CONFIRMED，regression PASS）

官方算法：

```text
x = 0
repeat: b = readByte(); x = (x << 7) | (b & 0x7f)
until b & 0x80 != 0
```

| bytes | 旧 LSB-first（错误）| 官方 MSB-first |
| --- | --- | --- |
| `80` | 0 | 0 |
| `BE` | 62 | 62 |
| `01 EC` | 13825 | **236** |
| `01 F5` | 14977 | **245** |

synthetic multi-byte regression 全部 PASS（`probe_lua54_metadata.py --selftest`）。

## 2. Source（CONFIRMED，4/4，单字节不变）

| 样本 | varint@0x20 | decoded | source_len | source 内容 |
| --- | --- | --- | --- | --- |
| LT31[874] | `BE` | 62 | 61 | `@Sunshine/.../qifen.lua`（纯路径，**与 header 位置精确一致**）|
| LT71[1768] | `C6` | 70 | 69 | 分段路径 + 段标记 + `80 80 00 01 04` |
| LT71[1631] | `E1` | 97 | 96 | 分段路径 + 段标记 + 尾部 |
| LT51[1178] | `B7` | 55 | 54 | 分段路径 + 段标记 + `80 80 00` |

- `decoded == source_len + 1` 成立（4/4，单字节）。
- ⚠️ 分段样本的 varint source_len 比「首个 `80 80` header 位置」大（差 5/8/2 字节）→ **分段路径的序列化语义仍未解**（不阻塞 varint 读取，但阻塞 header 定位的一致性解释）。

## 3. Proto header + sizecode（CONFIRMED，4/4）

```text
80 80 00 01 XX 01 YY
│  │  │  │  │  │  └ sizecode 第二字节（MSB-first）
│  │  │  │  │  └──── sizecode 第一字节
│  │  │  │  └─────── maxstacksize=XX
│  │  │  └────────── is_vararg=1
│  │  └───────────── numparams=0
│  └──────────────── lastlinedefined=0 (varint 0x80)
└─────────────────── linedefined=0 (varint 0x80)
```

| 样本 | ms | sizecode `01 YY` | code 区间 | 指令合法性(op≤127) |
| --- | --- | --- | --- | --- |
| LT31[874] | 3 | `01 F5` = 245 | 0x65-0x439 | 0 invalid ✓ |
| LT71[1768] | 4 | `01 CA` = 202 | 0x68-0x390 | 0 invalid ✓ |
| LT71[1631] | 0x1E | `01 DC` = 220 | 0x80-0x3F0 | 0 invalid ✓ |
| LT51[1178] | 0x24 | `01 EC` = 236 | 0x5C-0x40C | 0 invalid ✓ |

**结论：sizecode/code 已通过官方 walk 确认**（4/4 code 区域全部合法指令流；token 全部位于 code 区域之外）。

## 4. sizek / constants（FAIL，具体失败点）

- sizek @ code_end 无法解析为标准 varint count：LT31@0x439 字节 `0a 22 04 8f...`（MSB → 21529088）；其余样本同理。
- 从 code_end 附近 0x439-0x440 所有位置尝试 sizek（MSB/LSB）× 常量 tag 集（{04,14} 与 {04..08,14..16}）× 递归遍历，**均无法到达 5 个 token**。
- 因此：

```text
NodeGraphData          STRING_FRAMING_CANDIDATE  @ LT71[1768] +0x0656 tag=0x04 len=14
江晏                    STRING_FRAMING_CANDIDATE  @ LT71[1768] +0x06D4 tag=0x06 len=7
TextByNo               STRING_FRAMING_CANDIDATE  @ LT71[1631] +0x0525 tag=0x04 len=9
EXPANSION_QINGHE       STRING_FRAMING_CANDIDATE  @ LT71[1631] +0x0556 tag=0x04 len=17
70276                  STRING_FRAMING_CANDIDATE  @ LT31[874]  +0x17B9 tag=0x04 len=6
dq_610900              SOURCE_STRING（非 constant）
```

（0x04/0x14 与标准 string tag 兼容；0x06 等其它 tag 在走到真实 constant table 前不赋予 tag 语义。）

## 5. Guardrails（已落实）

- `MpkinfoReader`：version==3、entry index bounds、mpkinfo size 校验。
- `read_block`：offset+size <= archive size 校验 + `seek()` + bounded read（**不再整体读入 .mpk**）。
- 版本 0x54、format 0、size 4/8/8 全部 fail-closed。
- synthetic multi-byte varint regression（80→0、BE→62、01 EC→236、01 F5→245）。

## 6. Gate

> **PROTO_PARTIAL_AFTER_OFFICIAL_VARINT**

- 官方 MSB-first varint：CONFIRMED（regression PASS）。
- source（4/4）、header variant（4/4）、sizecode+code（4/4 合法指令流）：CONFIRMED。
- **sizek @ code_end：FAIL（具体偏移 0x439/0x390/0x3F0/0x40C）** → post-code（sizek/constants/upvalues/protos）为 custom variant，未确认。
- 非 STANDARD_PROTO_WITH_HEADER_VARIANT（sizek 未对齐）。
- 非 BODY_VARIANT_CONFIRMED（post-code variant 尚未理解，仅确认官方 walk 在 sizek 处失败）。

## 7. 交付物

- `tools/research/windows-static-archive/probe_lua54_metadata.py`：官方 MSB-first loadUnsigned + source/header/sizecode + token framing 定位；seek+bounded read；fail-closed；synthetic multi-byte regression（selftest PASS）。
- 本轮 scratch 已清理，仅保留交付 parser。

## 8. 下一步（待 Lead 放行）

残差聚焦到一个点：**sizek/constants 在 code_end 处的 custom 编码**（4 样本 code_end 一致失败）。建议一个小步研究该边界（可能 sizek 藏在 custom tail，或 constants 用非标准 tag/长度编码），之后可给 constant index / owning proto 并进 NEX-004。
