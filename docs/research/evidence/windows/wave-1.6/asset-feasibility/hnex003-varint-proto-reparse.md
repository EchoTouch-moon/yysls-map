# H-NEX-003 — Lua 5.4 Varint / Proto Reparse

> Task-ID: H-NEX-003 · Status: **DONE** · Gate: **BODY_VARIANT_CONFIRMED**
> Base: `research/windows-evidence-tooling` @ `34a63c3` · 样本：LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]（4 frozen samples）
> 静态只读；未做 opcode semantics / 未做 full decompiler / 未 dump 对白 / 未运行时。

---

## 0. 结论（一句话）

Lua 5.4 的 **varuint 编码（convB：每字节 7 bit、LSB 优先、高位 SET = 末字节）** 已确认，且 **source 长度 varint、Proto header variant、string constant 编码** 三者在 >=4 样本上一致确认；但 **sizecode 之后的 code/upvalues/protos 全遍历** 仍有一处未解析（sizecode 字节二义性），因此 **constant index / owning proto 无法给出**。

## 1. Phase A — Source 长度（CONFIRMED，4/4 样本）

- source 起点固定 `0x21`（`\x1bLua` 后 12B custom tail 之后）。
- 紧邻 source 之前的 varint 在 `0x20`，**convB**（高位 SET = 末字节）：

| 样本 | varint@0x20 | decoded | source_len(=decoded-1) | source 内容 |
| --- | --- | --- | --- | --- |
| LT31[874] | `BE` | 62 | 61 | `@Sunshine/AI/bt2code/output/u_newplay_horserob_thin_qifen.lua`（**纯路径**，与 decoded-1 精确一致）|
| LT71[1768] | `C6` | 70 | 69 | `@hexm/client/storyline_data` + 段标记 + `wanfa/MSD_ST/ZDQ` + 段标记 + `dq_610900.lua` + `80 80 00 01 04` |
| LT71[1631] | `E1` | 97 | 96 | `@hexm/client/ui/windows/yankov/storage/cangpin_sub_#` + 段标记 + `homeland_display_side_page.lua` + 尾部 |
| LT51[1178] | `B7` | 55 | 54 | `@hexm/client/ui/windows/common` + 段标记 + `_player_float.lua` + `80 80 00` |

- **`decoded == source_byte_length + 1` 成立**（按 decoded-1 取 source）。
- ⚠️ 单段路径（LT31）的 source 是纯明文路径；**分段路径的 source 区域含自定义段标记**（如 `16 00 F1 01`、`07 00 F0 1F`）与尾部字节，其精确序列化语义**未解析**（需 follow-up，不影响长度读取）。

## 2. Phase B — Proto Header Variant（CONFIRMED，4/4 样本）

body 起始处的固定模式（4 样本一致）：

```text
80 80 00 01 XX 01 YY 60
│  │  │  │ └ numparams=0
│  │  │  └──── is_vararg=1
│  │  └─────── numparams=0x00
│  └────────── lastlinedefined=0  (convB varint 0x80=0)
└──────────── linedefined=0       (convB varint 0x80=0)
```

- `XX` = maxstacksize（LT31=3, LT71[1768]=4, LT71[1631]=0x1E, LT51=0x24）。
- `01` = sizecode 候选字节（convA=1；convB=`01 YY`=13825/14977 越界 → 二义）。
- ⚠️ **sizecode 之后的全遍历未解析**：若 sc=1，则 top proto 的 sizek=0、sizeupvalues=12/29/29、sizep=0，与块内大量常量矛盾；若 sc=convB 则 code 越界。该处是 H-NEX-003 的残余阻塞点。

## 3. Phase C — Constants（PARTIAL，编码确认 + 5 token 定位成功）

string constant 编码（多样本确认）：

```text
[tag 1B][len convB varint][len-1 bytes]
```

| tag | 含义（实测） |
| --- | --- |
| 0x04 / 0x05 / 0x06 / 0x07 / 0x08 / 0x14 / 0x15 / 0x16 | string |

| token | 样本 | byte offset | tag | len | len-1==值长 | 值 |
| --- | --- | --- | --- | --- | --- | --- |
| `NodeGraphData` | LT71[1768] | +0x0656 | 0x04 | 14 | ✓ | 13B |
| `江晏` | LT71[1768] | +0x06D4 | 0x06 | 7 | ✓ | 6B |
| `TextByNo` | LT71[1631] | +0x0525 | 0x04 | 9 | ✓ | 8B |
| `EXPANSION_QINGHE` | LT71[1631] | +0x0556 | 0x04 | 17 | ✓ | 16B |
| `70276` | LT31[874] | +0x17B9 | 0x04 | 6 | ✓ | 5B |
| `dq_610900` | LT71[1768] | source 段内 | — | — | — | SOURCE_STRING（非 constant）|

- **能给出**：byte offset + tag + length + value（short locator）。
- **不能给出**：constant index / owning proto（依赖 sizecode 全遍历，见 Phase B ⚠️）。

## 4. Cross-sample

- 4/4 样本同一 parser path：source varint + header variant + token 定位全部成功。
- 无 hard-coded 样本专属 offset（source 用固定 0x21；header 用固定 `80 80 00 01` 模式；token 用 tag+len 校验）。

## 5. Gate

> **BODY_VARIANT_CONFIRMED**

- Source：CONFIRMED（convB varint，decoded == len+1，4/4）。
- Header variant：CONFIRMED（`80 80 00 01 XX 01`，4/4）。
- String constants：CONFIRMED（tag + convB varint + len-1），5 token 定位成功。
- **残差**：sizecode→code→upvalues→protos 全遍历未解析（sizecode 二义性）；constant index/owning proto 未给出；分段 source 的段标记语义未解。
- 非 FAIL_CLOSED_UNRESOLVED（已确认大量 body variant 结构）。
- 非 STANDARD_PROTO_CONFIRMED / STANDARD_PROTO_WITH_HEADER_VARIANT（全遍历未通）。

## 6. 交付物

- `tools/research/windows-static-archive/probe_lua54_metadata.py`（bounded / fail-closed / provenance / synthetic selftest PASS；source varint + header variant + token 定位）。
- 验证：selftest PASS；4 样本成功；未知 version / 错误 size 字节 fail-closed。
- 已清理本轮全部 scratch（varint_test / brute_force / layout_search / dump_* 等，仅保留交付 parser）。

## 7. 下一步（待 Lead 放行）

突破残差需要一个小步：**确定 sizecode 的真实编码**（convA=1 与 convB=越界 都不通 → 可能是「sizecode 在 custom tail 中」或「code 段另有布局」）。之后才能给出 constant index / owning proto，并进入 NEX-004（Normalizer）。
