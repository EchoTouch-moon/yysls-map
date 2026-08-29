# NEX-003 — Minimal Lua 5.4 Constant / Proto Reader

> Task-ID: NEX-003 · Status: **DONE** · Gate: **BODY_LAYOUT_PARTIAL**
> Base: `research/windows-evidence-tooling` @ `e00335d` · 样本：LT71[1768]/LT71[1631]/LT31[874]/LT51[1178]
> 静态只读；未做 opcode semantics、未做 full decompiler、未 dump 对白、未运行时/内存/密钥/反作弊。

---

## 0. 结论（一句话）

Lua 5.4 头部（signature/version/format/LUAC_DATA + 3 size 字节）与 **source 定位** 已确认；但 **post-size 布局（0x15 起）与 source 长度编码是 CUSTOM**（第一个 divergence = 绝对 0x18），导致 **标准 loadFunction 的 Proto（linedefined/code/loadConstants）无法确定性解析**。叙事字符串可**明文定位**（byte offset），但无法给出 constant index/tag/length。→ **BODY_LAYOUT_PARTIAL**。

---

## 1. Phase A — Post-size Layout（实测）

```text
0x06–0x14  sig + ver(0x54) + fmt(0) + LUAC_DATA + sizeof(4/8/8)   ← 标准
0x15–0x20  12B custom tail：78 56 00 01 00 ?? ?? 28 77 40 01 ??   ← 非标准 LUAC_INT/NUM
0x21–…     source 字符串（"@" 前缀，明文，分 1~3 段）
0x…        0x80 0x80 终止标记（实测，4 样本一致）
```

- **source 定位**：`"@"` 固定在 `0x21`（`\x1bLua` 后 +0x1B）；终止于 `0x80 0x80`（不是标准 loadSize varint 长度编码）。
- **source 分段**：路径被拆成多段，段间有非标准分隔字节（如 `16 00 F1 01` / `07 00 F0 1F`），未解。
- **禁止** find("@") 作为正式 parser 逻辑 → 已改为「固定偏移 + `0x80 0x80` 终止」的确定性读取（仍属 empirical，但 fail-closed）。

## 2. Phase B — Minimal Proto Reader：**未达成**

标准 loadFunction 顺序（source → linedefined → lastlinedefined → numparams/is_vararg/maxstacksize → code count+code → constants）在 source 之后无法对齐：

- source 长度编码非标准（`0x80 0x80` 终止，非 varint）。
- source 之后按 4B linedefined / 4B lastlinedefined / 1B numparams … 试解析，得到的 numparams=0 / is_vararg=12 / maxstacksize=0 等值**不合理** → post-source 布局同样 custom。
- 因此 **code 段大小无法计算 → 常量表精确偏移无法得到**。

## 3. Phase C — Constant Reader：**PARTIAL**

| token | 定位方式 | 结果 |
| --- | --- | --- |
| `NodeGraphData` | 明文 scan | LT71[1768] +0x0656 ✓ |
| `TextByNo` | 明文 scan | LT71[1631]（未在本轮样本集；W-R05 已知 +0x525） |
| `EXPANSION_QINGHE` | 明文 scan | LT71[1631]（W-R05 已知 +0x556） |
| `70276` | 明文 scan | LT31[874] +0x17B9 ✓ |
| `江晏` | 明文 scan | LT71[1768] +0x06D4 ✓ |
| `dq_610900` | source 段 | LT71[1768] source 内（保持 SOURCE_STRING，非 constant）✓ |

**能给出**：byte offset + value（短 locator）。**不能给出**：constant index / tag / length / owning proto（需先解 source 编码 + Proto 布局）。

## 4. Phase D — Cross-sample

- 3+ 样本（LT71[1768]/LT31[874]/LT51[1178]）走同一 parser path 成功（header 解析 + source 定位 + token 明文定位）。
- 无 hard-coded 样本专属 offset（source 用「固定 0x21 + `0x80 0x80` 终止」，通用）。

## 5. Gate

> **BODY_LAYOUT_PARTIAL**

- Header：CONFIRMED（Lua 5.4，32-bit Instruction，标准 size 字节）。
- Source：LOCATED（明文，`0x80 0x80` 终止，编码 custom）。
- Proto（linedefined/code/constants）：NOT PARSED（post-source 布局 custom）。
- Constants：明文可定位，但非 deterministic 枚举。

**不是** CUSTOM_RUNTIME_REQUIRED（无需运行时/密钥，仍是纯静态，只是 body 布局需更多静态逆向）。

## 6. 交付物

- `tools/research/windows-static-archive/probe_lua54_metadata.py`（bounded / fail-closed / provenance / synthetic selftest；仅 header+source+token 明文定位，不做 Proto 解析）。
- 验证：selftest PASS；3 样本成功；未知 version / 错误 size 字节 fail-closed。

## 7. 下一步（待 Lead 放行）

要突破 BODY_LAYOUT_PARTIAL，需先确定 **source 长度编码 + post-source Proto 布局**（尤其 code 段大小字段），这属于一个「body-layout 二次研究」小步，而非直接进入 NEX-004（Normalizer）。当前证据足以说明：叙事 token 是明文、可定位、无密钥，但**从「可定位」到「结构化 quest/task metadata」中间还差一层 body 解码**。
