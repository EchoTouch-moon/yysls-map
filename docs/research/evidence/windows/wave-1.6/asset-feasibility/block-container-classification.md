# W-R03.5 — Block & Container Classification

> Task-ID: W-R03.5 · Owner: Windows · Status: **DONE** · Gate: **CONTENT_CLASSIFICATION_READY**
> 范围：main Resources（`.mpkinfo` ↔ `.mpk`）静态分类。未运行时/未 hook/未内存/未反作弊/未研究密钥/未批量导出。

---

## 0. 结论（一句话）

`.mpk` 资源块被完整分类：**主体是 DirectX 着色器容器（`ZZZ4` + `DXBC`/`DXIL` 字节码）**，有未压缩与 LZMA 压缩两种封装；另有空块与表格块。全程**无加密、无 protected bypass、无需运行时**，`chinaHEX_` 头不影响 offset 遍历。

---

## 1. 目标 1 — Type B（small-u32 头）已解码

small-u32 块首的 u32 是**子着色器数量 N**。块结构（确定性）：

```text
+0x00  u32 N                    子着色器数量（0 = 空块，size=4）
+0x04  N × 20B 子条目           与 .mpkinfo entry 同构：name_fragment + hash + offset + stored_size + flags
+0x04+N*20  "ZZZ" + 版本字节     即 "ZZZ4"
+0x0E+N*20  "DXBC" / "DXIL"     DirectX 着色器字节码（编译后 HLSL）
```

**验证**：`ZZZ` 偏移恒等于 `4 + N*20`，对 N=1..11 全部成立（143+45+21+8+2+4+3+3+3+1+2 = 235 个块）；`DXBC` 位于 `ZZZ+10`。

| 首 u32 N | 块数 | 结构 | 说明 |
| ---: | ---: | --- | --- |
| 0 | 6 | 仅计数，size=4 | 空/占位 |
| 1 | 143 | 1 个子着色器 → ZZZ4+DXBC | 未压缩着色器容器 |
| 2 | 45 | 2 个子着色器 | 同上 |
| 3 | 21 | 3 个 | 同上 |
| 4 | 8 | 4 个 | 同上 |
| 5 | 2 | 5 个 | 同上 |
| 6 | 4 | 6 个 | 同上 |
| 7–11 | 3+3+3+1+2 | 7–11 个 | 同上 |
| 24 / 28 | 4 / 2 | u16 offset 表（`14 00 20 00 04 00 08 00…`） | 另一类表格容器，非着色器 |
| `"LZMA"` | 14（首60内） | LZMA 压缩 | 见目标 2 |
| ≥100（other） | 19（首60内） | 各异 | 未解码，非着色器 |

---

## 2. 目标 2 — LZMA 后 custom container：**ONE_ENTRY_CONTAINER_OF_MANY**

LZMA 块解压后得到**与目标 1 完全相同的着色器容器**：

```text
entry 2（'.ePS'，LZMA 块）解压 → 3,452,000 B
  首 u32 N = 251
  "ZZZ4" @ 5024  （== 4 + 251*20）  ✓
  "DXBC" @ 5034  （== ZZZ + 10）     ✓
  "DXIL" @ 5423                     ✓（DX 中间语言，更新字节码）
```

→ 一个 `.mpkinfo` entry 映射到一个容器，容器内是 **N 个子着色器（permutations）**。
→ 分类：**ONE_ENTRY_CONTAINER_OF_MANY**（非 ONE_ENTRY_ONE_RESOURCE，非 LIKELY_CHUNK）。

> 推论：small-u32 块 = 小着色器**未压缩**；LZMA 块 = 大着色器**压缩**后存同一容器格式。两套封装同构。

---

## 3. 目标 3 — MPK global header：**OPAQUE / NON_BLOCKING**

- 文件头（offset 0）：`"chinaHEX_"` + base64（~85 B，以 `=` 结尾）+ `"CCCCEZST"`（8 B）+ 二进制。
- 所有数据块 offset ≥ 63 MB，远超头部；在字面 offset 处读到的是干净块（`LZMA`/u32 头），不是 `chinaHEX_` 垃圾。
- 结论：**header 是文件前缀，不影响 absolute-offset traversal**。按任务要求**停止研究 header**（标 OPAQUE）。

---

## 4. 边界检查

- ✅ 全部静态只读；解压仅 1 个 LZMA 块到内存验证，未落盘/未导出。
- 🛑 未解码 `chinaHEX_`/`HEX_`/`HEXB_` 混淆层；未研究密钥/解密链。
- 🛑 未运行时、未 hook/inject/memory dump、未反作弊、未批量导出。

---

## 5. Gate

> **CONTENT_CLASSIFICATION_READY**

| 能力 | 结果 |
| --- | --- |
| block 类型分类（LZMA / 着色器容器 / 空块 / 表格块 / other） | YES（静态、确定性） |
| payload 内容识别（`ZZZ4` + `DXBC`/`DXIL` = DirectX 着色器） | YES |
| 解压（LZMA） | YES（普通压缩，无密钥） |
| header 影响 offset | NO（NON_BLOCKING） |
| 需要 protected / runtime | NO |

## 6. 对叙事目标的直接含义（供 Lead 参考，非本轮任务）

`Resources.mpk` 内容**以 DirectX 着色器字节码为主体**（PS/VS/CS/HS/DS/SS 扩展名 + DXBC/DXIL）。name 片段中**未观察到 quest/task/story/chapter/localization/text/dialog/npc/qinghe 等叙事关键词**（仅 `ion/tor/tem/sel` 等歧义后缀）。即：本 archive 的静态目录是“着色器 + 二进制表格”，**不直接承载叙事/任务元数据**。是否在区域 patch（qingzhou 等）的 `.mpk` 中存在叙事 metadata，属 W-R04 判定。
