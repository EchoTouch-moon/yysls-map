# H-NEX-003T — LT31 Instruction Framing & Sizecode Boundary

> Task-ID: H-NEX-003T · Status: **DONE** · Gate: **INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED**
> Base: `research/windows-evidence-tooling` @ `ae82a52` · Primary control：LT31[874] ONLY
> Committed tools：`verify_proto_boundary.py`（opcode table 修复）、`framing_probe.py`
> 静态只读；未做 CFG/opcode semantics；未 dump 对白；未运行时。

---

## 0. 结论（一句话）

先修 verifier opcode 表（Lua 5.4 官方 **83 个 opcode，0..82**，含 GETI/GETFIELD/SETI/SETFIELD）。LT31 的 source/header 前半段已冻结确认；在 **有限的 framing hypothesis 空间（H0/H1/H2/H3：官方 MSB varint sizecode、0-3B 对齐、大小端、一个 bounded custom field）内，无任何 candidate 得到 0 条非法 opcode** → 按 Phase D 停止条件：

> **INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED** —— instruction serialization 是私有变体，**Lua VM/body 逆向到此收口**，不再继续猜 opcode remap / 逆 VM / 推 CFG。

## 1. Verifier 修复（Lead 复核的 opcode 表错误）

- Lua 5.4 官方 `lopcodes.h`：`GETI`(13)、`GETFIELD`(14)、`SETI`(17)、`SETFIELD`(18) 四个 opcode 缺失 → `NUM_OPCODES` 应为 **83**（0..82），不是 79。
- selftest 覆盖：op 78(SETLIST)/79(CLOSURE)/82(EXTRAARG) valid，op 83 invalid。
- LT31 invalid count 重算：**51 → 46**（op ≥ 83）。第一条 candidate instruction op=96 仍非法（> 82）→ **LT31 candidate code start 或 instruction serialization 至少有一个错误**（BOUNDARY_PARTIAL 结论不变，只是数字更新）。

## 2. Phase A — LT31 冻结前半段

```text
source len      = 61        (varint 0xBE -> 62, decoded == len+1)
source raw      = @Sunshine/AI/bt2code/output/u_newplay_horserob_thin_qifen.lua
body start      = +0x005E
linedefined     = 0
lastlinedefined = 0
numparams       = 0
is_vararg       = 1
maxstacksize    = 3
```

maxstacksize 后 32B 原始字节（+0x0063 起，未先命名）：

```text
01 f5 60 00 00 00 0c 00 00 00 83 80 00 00 52 00 02 02 11 00 00 02 9d 00 00 00 61 00 00 00
```

## 3. Phase B — 有限 framing hypothesis（无全局 brute force）

| hypothesis | sizecode | code_start | count | invalid(≥83) | first_invalid | first 8 ops |
| --- | --- | --- | --- | --- | --- | --- |
| H0/H1 adj=0 (LE) | 245 | +0x0065 | 245 | 46 | +0x0065 | 96,12,3,82,17,29,97,24 |
| H1 adj=1 (LE) | 245 | +0x0066 | 245 | 47 | +0x00AE | 0,0,0,0,0,0,0,0 |
| H1 adj=2 (LE) | 245 | +0x0067 | 245 | 46 | +0x009F | 0,0,0,2,0,0,0,3 |
| H1 adj=3 (LE) | 245 | +0x0068 | 245 | 51 | +0x0098 | 0,0,0,2,2,0,0,4 |
| H2 adj=0 (BE) | 245 | +0x0065 | 245 | 51 | +0x0095 | 0,0,0,2,2,0,0,4 |
| H2 adj=1 (BE) | 245 | +0x0066 | 245 | 45 | +0x007A | 12,3,82,17,29,97,24,24 |
| H2 adj=2 (BE) | 245 | +0x0067 | 245 | 47 | +0x00AB | 0,0,0,0,0,0,0,0 |
| H2 adj=3 (BE) | 245 | +0x0068 | 245 | 46 | +0x009C | 0,0,2,0,0,0,3,5 |
| H3（1B custom field `01`，sc=117）| 117 | +0x0065 | 117 | **17** | +0x0065 | 96,12,3,82,17,29,97,24 |

- **无任何 candidate invalid_opcode_count == 0**（最好 H3 仍 17 条非法，且第一条 op=96 就非法）。
- 未用剧情 token 挑选 winner（token 不参与任何判定）。

## 4. Phase C — 结构 sanity（不适用）

- 无 candidate 达到 0 invalid → LOADKX→EXTRAARG / NEWTABLE→EXTRAARG adjacency、RETURN family、VARARGPREP 的检查**未触发**（已在 framing_probe.py 中实现，仅对 0-invalid candidate 输出）。

## 5. Phase D — 停止条件触发

在有限的 alignment（0-3B）× endianness（LE/BE）× one-bounded-framing-field 范围内，**无法得到可信的标准 Lua 5.4 instruction stream**：

> **INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED**

停止 Lua VM/body reverse engineering；不再进行 opcode remap 猜测 / VM 逆向 / CFG 构建 / custom opcode table 搜索。

## 6. Gate

> **INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED**

- LT31 source/header 前半段：CONFIRMED（确定性，frozen）。
- instruction serialization：PRIVATE VARIANT（H0-H3 全部失败）。
- 建议后续：NEX-004 改走 **RAW/STRUCTURAL Normalizer**（source/path + framed strings + stable refs + byte provenance），符合 NEX-001 的 RAW_EXTRACTED → STRUCTURALLY_VALIDATED 路径，不要求完整理解 Lua VM。

## 7. 交付物

- `tools/research/windows-static-archive/verify_proto_boundary.py`：opcode 表修复为 83（GETI/GETFIELD/SETI/SETFIELD），selftest 覆盖 op 78/79/82/83，LT31 invalid=46。
- `tools/research/windows-static-archive/framing_probe.py`：H0-H3 framing probe + Phase A 冻结输入 + Phase C 结构 sanity 钩子 + selftest PASS。
- `docs/research/evidence/windows/wave-1.6/asset-feasibility/hnex003t-lt31-framing.md`。
- 本轮 scratch 已清理。

## 8. 状态（按 Lead 决议）

```text
H-NEX-003T               CLOSED / INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED
Lua body research        收口
NEX-004                  HOLD（建议改评估 NEX-004A Raw Structural Normalizer）
Canonical v0.1           FROZEN
```
