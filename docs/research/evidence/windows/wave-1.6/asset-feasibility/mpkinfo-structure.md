# W-R01 — MPKINFO Structural Inspection

> Task-ID: W-R01 · Owner: Windows · Status: **DONE** · Gate: **R1 = PASS**
> 方法：hex viewer / Python `struct` / 多文件交叉比较 / 大小-计数算术验证 / 已知 shader 扩展名 locator。
> 输入：`tools/research/windows-static-archive/samples/`（7 个 version=3 样本 + 1 个 HEXB 变体）。

---

## 0. 结论

`.mpkinfo`（version=3）是**结构确定、可静态解析**的资源索引：

```text
header  (8 B)  : uint32 LE version (=3) + uint32 LE entry_count
entries (N×20B): 固定长度 entry
trailer (16 B) : 存在但用途未知
```

**不变式（7 个文件全部满足，无例外）**：`file_size == 8 + entry_count*20 + 16`

| 文件 | size | version | count | 8+N*20+16 |
| --- | ---: | ---: | ---: | ---: |
| main_Resources.mpkinfo | 12,524 | 3 | 625 | 12,524 ✓ |
| deploy_Resources.mpkinfo | 13,744 | 3 | 686 | 13,744 ✓ |
| tiny_hexi_1.mpkinfo | 64 | 3 | 2 | 64 ✓ |
| lt261.mpkinfo | 224 | 3 | 10 | 224 ✓ |
| patch1001.mpkinfo | 264 | 3 | 12 | 264 ✓ |
| lt312.mpkinfo | 1,524 | 3 | 75 | 1,524 ✓ |
| tiny_qingzhou.mpkinfo | 2,984 | 3 | 148 | 2,984 ✓ |

> 另有 `tiny_bjs_3.mpkinfo` 以 `HEXB_` 开头（base64 混淆变体），**非** version=3 索引 → 见 §5。

---

## 1. 结构证据表

| Offset | Field | Width | Endian | Confidence | Evidence |
| --- | --- | ---: | --- | --- | --- |
| `0x00` | version | 4 | LE | **HIGH** | 7 个样本一致 = `3` |
| `0x04` | entry_count | 4 | LE | **HIGH** | `8 + count*20 + 16 == size` 全部成立 |
| `+0x00` | name_fragment | 4 | — | **HIGH**（存在）；语义 PARTIAL | 见 §2 |
| `+0x04` | hash | 4 | — | **HIGH**（存在）；算法 PARTIAL | 逐 entry 唯一（distinct == count，7/7） |
| `+0x08` | offset | 4 | LE | **HIGH** | 目录 entry 为 0；`offset+size ≤ .mpk size` 零违例（见 §3） |
| `+0x0C` | stored_size | 4 | LE | **HIGH** | 目录 entry 为 0 |
| `+0x10` | flags | 4 | LE | **HIGH** | `1` ⇔ offset=size=0（目录/空）；`0`=文件；patch 索引另有取值 |
| 末尾 16B | trailer | 16 | — | HIGH（存在）/ 用途 UNKNOWN | 所有样本均有，内容互异 |

entry 为**固定 20 字节**，边界可 deterministic 复现（entry i 起始于 `8 + i*20`）。

---

## 2. name_fragment 语义（PARTIAL，未破解到完整路径）

`+0x00` 是 4 字节字段，**不是完整路径**，观察为两种形态：

### 2a. hash-only（patch/TinyFiles/LT 索引）

4 个 ASCII 小写十六进制字符 = 16-bit hash 的十六进制表示：

```text
tiny_qingzhou: "547f" "b3ba" "5c27" "5f72" "a602" "0107" "9cb7" "3a82" "adaf" ...
tiny_hexi_1:   "4067" "c955"
```

→ 对应任务 §9 的 “hash-only resource”。

### 2b. filename-tail（main/deploy Resources 索引）

`1 字节（小值 0x05~0x38，疑似 type/hash 前缀）+ 3 字节文件名尾部`：

```text
.pPS  .ePS  .der  .her  .ial  .ing  .ake  .HPS  .ion  .rCS  .eVS  .lPS  757b  8b70
```

- 3 字节尾部含 shader 扩展名：`.ps/.vs/.cs/.hs/.ds/.ss`（大写存 `PS/VS/CS/HS/DS/SS`）。
- 扩展名直方图（main）：`PS=126, VS=48, CS=37, HS=6, DS=6, SS=4`；非扩展后缀 `ing=27, her=10, der=5, …`。
- **关键限制**：只能看到文件名**尾部 3 字符**，无法从索引重建完整路径/文件名；更无法判断哪个 entry 是 quest/task/localization 资源。

---

## 3. offset / stored_size 验证（archive-size 不变式）

以 paired `.mpk` 大小校验“`f2=offset, f3=size`”：

| 文件 | .mpk size | 违例（offset+size>mpk） | max offset |
| --- | ---: | ---: | ---: |
| main_Resources | 200,632,208 | **0** | 193,386,661 |
| deploy_Resources | 270,179,195 | **0** | 268,360,595 |

且所有 `flags==1` 的 entry（main 66 个 / deploy 74 个）其 `offset==0 && stored_size==0`（66/66、74/74），与“目录/空节点”语义一致。

---

## 4. W-R01 十问

1. magic/header 是否稳定 → **稳定**：`03 00 00 00` + count（无 ASCII magic 字符串）。
2. version 能否稳定读取 → **能**，u32 LE @ `0x00` = 3。
3. entry count 能否从 header 独立得到 → **能**，u32 LE @ `0x04`。
4. 固定 vs 变长 → **固定 20 字节**（算术不变式证明）。
5. 是否有 UTF-8/UTF-16/ASCII path → **无完整 path**；仅有 4 字节 name_fragment。
6. filename → **仅尾部片段**（2b）或 hash（2a）。
7. extension → **可识别 shader 扩展名**（PS/VS/CS/HS/DS/SS），但仅当出现在尾部。
8. hash → **存在**（`+0x04`，逐 entry 唯一；算法未确认，不标“已破解”）。
9. offset / compressed size / original size → `offset`(`+0x08`)、`stored_size`(`+0x0C`)；**未发现独立 original_size / 压缩标志字段**。
10. entry 边界能否 deterministic 复现 → **能**（`8 + i*20`）。

---

## 5. HEXB 变体（第二格式）

- `TinyFiles_common_bjs.3.mpkinfo` 等以 `48 45 58 42 5F` = `"HEXB_"` 开头，其后为 base64。
- 与 `patch_config.json`/`patchlist_*.txt`/`extra_version` 的 `HEX_`/`HEXB_` 混淆一致 → **OPAQUE**，不在本 parser 范围。
- parser 对其 fail-closed（拒绝，不猜测）。

---

## 6. Gate R1 判定

> “能够 deterministic 枚举 entry，并至少可靠识别 path/name/type 或 offset/size 其中一类高价值字段”

- deterministic 枚举 entry：✅（固定 20B，`8 + i*20`）
- 识别高价值字段：✅ **offset / stored_size / flags / hash**（offset+size 不变式零违例）

→ **R1 = PASS**（可进入 W-R02）。

## 7. 未决 / 风险

- name_fragment 的完整解码（hash 算法、首字节语义、能否反推完整路径）→ 未解；不反推。
- `+0x04` hash 的具体算法（CRC32/MD5 片段/自定义）→ 未确认。
- 16B trailer 用途（签名/校验/其他）→ 未知；不影响枚举。
- 未发现独立 `original_size` 或压缩标记 → 若 payload 有压缩，标记可能在其他结构（W-R03 才需回答）。
