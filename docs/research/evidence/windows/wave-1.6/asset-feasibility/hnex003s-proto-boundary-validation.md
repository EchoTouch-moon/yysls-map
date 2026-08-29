# H-NEX-003S — Proto Boundary & Post-Code Section Validation

> Task-ID: H-NEX-003S · Status: **DONE** · Gate: **BOUNDARY_PARTIAL**
> Base: `research/windows-evidence-tooling` @ `492e5a7` · 样本：LT31[874]（control）+ LT71[1768]/LT71[1631]/LT51[1178]
> Committed verifier：`tools/research/windows-static-archive/verify_proto_boundary.py`（selftest PASS）
> 静态只读；未做 CFG/opcode semantics；未 dump 对白；未运行时。

---

## 0. 结论（一句话）

LT31 pure-source control 的 **source / header 已确定性确认**（varint 定长，无 find("@")/token/guessed marker），但 **code 区域在官方 79-opcode enum 下有 51 条非法指令**，且 **sizek @ code_end 解析失败**。segmented 样本 varint body 处无 header → **SOURCE_SERIALIZATION=PARTIAL**。四个 candidate code_end 的 raw32 无稳定 section marker、无立即标准 sizek；LT71[1631]/LT51 的 raw32 开头是 "nsts"/"consts"（"constants" 字符串尾部）→ 候选 sizecode 越界进入字符串数据。→ **BOUNDARY_PARTIAL**。

## 1. Phase A — LT31 pure-source control（确定性，无 find("@")/token/guessed marker）

由 committed verifier 确定性产出（source 长度来自 `0x20` varint，body = `0x21 + decoded - 1`）：

```text
source len      = 61        (varint 0xBE -> 62, decoded == len+1)
linedefined     = 0         (varint 0x80)
lastlinedefined = 0         (varint 0x80)
numparams       = 0
is_vararg       = 1
maxstacksize    = 3
sizecode        = 245       (varint 01 F5, 官方 MSB-first)
code_start      = +0x0065
code_end        = +0x0439
```

LT31 的 source 区域 = `@Sunshine/AI/bt2code/output/u_newplay_horserob_thin_qifen.lua`（61B，纯路径），varint 定长与 header 位置精确一致。

## 2. Phase B — 官方 opcode enum 校验（不再用 opcode ≤ 127）

Lua 5.4 官方 enum：79 个 opcode（0-78，`NUM_OPCODES=79`）。校验结果：

| 样本 | candidate sizecode | instruction_count | invalid (op ≥ 79) | first_invalid |
| --- | --- | --- | --- | --- |
| LT31[874] | 245 | 245 | **51** | +0x0065 (op 96) |
| LT71[1768] | 202 | 202 | 45 | +0x0068 |
| LT71[1631] | 220 | 220 | 33 | +0x0080 |
| LT51[1178] | 236 | 236 | 62 | +0x005C |

- 四样本 candidate code 均含非法 opcode → **code 边界非标准 Lua 5.4 confirmed**。
- 另测 sc=`60`(=96, 1-byte)：LT51 code 0 invalid，但四样本 sizek 仍失败（见 §4）→ 不作为确认依据。

## 3. Phase C — Post-code sizek 尝试（reproducible）

code_end → loadInt(sizek)：

| 样本 | code_end | raw32 @ code_end | decoded | 结果 |
| --- | --- | --- | --- | --- |
| LT31[874] | +0x0439 | `0a 22 04 8f 2a 00 a3 4f 44 45 53 5f 4e 55 4d 03 73 92 04 20 04 90 14 00 f0 12 5f 44 41 54 41 5f` | 21529103 | FAIL (>500k) |
| LT71[1768] | +0x0390 | `35 12 00 21 45 78 12 00 25 73 5a 12 00 20 48 57 12 00 30 53 34 79 48 00 fd 0a 66 52 49 7a 33 5a` | — | FAIL |
| LT71[1631] | +0x03F0 | `6e 73 74 73 22 00 02 10 00 22 04 b0 24 00 01 26 04 56 2e 75 74 69 6c 22 00 e0 62 6c 6f 63 6b 5f` | — | FAIL |
| LT51[1178] | +0x040C | `63 6f 6e 73 74 73 07 00 22 04 b7 1b 00 01 13 04 f0 03 2e 75 69 2e 67 65 6e 65 72 61 74 65 64 5f` | — | FAIL |

→ **无立即标准 sizek**（四样本均失败）。

## 4. Phase D — Cross-sample + SOURCE_SERIALIZATION

| 样本 | varint body | header 位置 | 状态 |
| --- | --- | --- | --- |
| LT31[874] | +0x005E | +0x005E（一致）| HEADER_OK |
| LT71[1768] | +0x0066 | +0x0061（首个 0x80 0x80 在 varint body 之前）| HEADER_FAIL → **SOURCE_SERIALIZATION=PARTIAL** |
| LT71[1631] | +0x0081 | +0x0079 | HEADER_FAIL → **SOURCE_SERIALIZATION=PARTIAL** |
| LT51[1178] | +0x0057 | +0x0055 | HEADER_FAIL → **SOURCE_SERIALIZATION=PARTIAL** |

- segmented 样本的 **logical source length（varint）≠ proto body start**：varint 区域内含分段标记与额外字节（含 `80 80 00 01` 模式），**serialized boundary 未能证明** → 按 Lead 规则标记 SOURCE_SERIALIZATION=PARTIAL，**未用 logical length 强行推进 body**。

## 5. Phase E — Boundary classification（四个 candidate code_end）

- **无稳定 section marker**：四 raw32 无共同前缀。
- **无 fixed-width field / 无 varint sizek**：均非立即标准 sizek。
- **LT71[1631]/LT51**：raw32 开头 `nsts`/`consts` = 字符串 `constants` 的尾部 → **候选 code 越界进入字符串数据**（`01 YY` sizecode 过大）。
- **LT31/LT71[1768]**：raw32 含 `04` tag + 字符串片段（"ODES_NUM"/"_DATA_CACHE"）或 `12 00` 重复对 → 非干净边界。
- 允许以已知 token 作为 research oracle 的交叉验证已完成（token 均在候选 code 区域之外），但正式 verifier 不依赖 token。

## 6. Gate

> **BOUNDARY_PARTIAL**

- LT31 control：source/header **CONFIRMED**（确定性）；sizecode=245；**code 有 51 条非法 opcode（官方 enum）；sizek@+0x0439 FAIL** → proto/code 边界仅部分解析。
- segmented 样本：**SOURCE_SERIALIZATION=PARTIAL**（varint logical length ≠ body start，serialized boundary 未证明）。
- 非 STANDARD_PROTO_CONFIRMED（code/sizek 均未对齐）。
- 非 POST_CODE_VARIANT_CONFIRMED（post-code variant 结构尚未解码确认）。

## 7. 交付物

- `tools/research/windows-static-archive/verify_proto_boundary.py`（committed verifier）：
  - 确定性 source/header/sizecode/code 解析（varint 定长，无 find("@")/token/guessed marker）。
  - 官方 Lua 5.4 79-opcode enum 校验（instruction_count / invalid_count / first_invalid_offset）。
  - sizek @ code_end 尝试（raw32 + decoded + failure reason）。
  - candidate（首个 0x80 0x80）边界交叉对比。
  - guardrails：entry bounds / archive bounds / seek+bounded read / version 0x54 / format 0 / sizes 4/8/8 / fail closed。
  - synthetic varint + opcode validation regression（selftest PASS）。
- 本轮 scratch 已清理。

## 8. 下一步（待 Lead 放行）

残差两个点：
1. **sizecode 真实编码**：`01 YY`（MSB 官方）越界进入字符串；`60`（1-byte 96）sizek 仍失败。可能 sizecode 是多段/变长或藏在 custom tail。
2. **segmented source serialization**：varint logical length ≠ body start，需先解段标记序列化。

两者任一突破后可进 NEX-004。
