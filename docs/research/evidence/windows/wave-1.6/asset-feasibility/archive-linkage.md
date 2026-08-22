# W-R03 — Index → Archive Linkage Probe

> Task-ID: W-R03 · Owner: Windows · Status: **DONE** · Gate: **STATIC_EXTRACTION_PARTIAL**
> 范围：仅 main Resources（`E:\yysls\Resources.mpk` ↔ `Resources.mpkinfo`），5 个低风险 `.ps` 样本。
> 未批量导出、未碰剧情资源、未处理 HEXB、未研究密钥、未进运行时、未 hook/inject/memory dump、未反作弊。

---

## 0. 结论

`.mpkinfo` entry 可以**完全静态、确定性**地定位到 `.mpk` 内的数据块，且**存在普通 LZMA 压缩（NOT_OBSERVED_IN_TESTED_SCOPE：已测样本内无需加密/密钥）**：

```text
mpkinfo entry
   → source .mpk（同 basename 配对）
   → offset（绝对字节偏移，指向“块”而非裸 payload）
   → stored_size（有效读取边界，读满不短）
   → block：
        type A = "LZMA" + u32 uncompressed_size + props(1) + dict_size(4) + LZMA 数据  → 可解压
        type B = 小 u32 头（1/3/6）+ …                                   → 未解码（静态格式待查）
```

已实测：type A 块用 Python `lzma`（FORMAT_ALONE，重建 13 字节头）解压成功，输出字节数与 `uncompressed_size` 精确一致。

**Gate = PARTIAL** 的原因（非 NO_GO）：
1. index → archive → payload 链路静态、确定性成立，**NOT_OBSERVED_IN_TESTED_SCOPE**（已测样本 LZMA 为普通压缩，未见 protected bypass）；
2. 但存在**第二类块格式（小 u32 头）尚未解码**，且解压后的 shader 内容是自定义容器（非标准 DXBC）——属于“普通压缩/静态格式仍有少量问题”，需后续（W-R04 或小步跟进）补完，而不是“需要密钥/解密”。

---

## 1. 样本记录

source_mpkinfo SHA-256：`DC98DF817E390414B7FD89FDD6A0BDA764826938AB585B0E493CF8D41730468F`
source_mpk SHA-256：`31C309B06FD8A4FAA15B37C3B076D7215FF4B7A28C78038E291F7F2FFF532E01`
mpk 前 16 字节：`63 68 69 6e 61 48 45 58 5F 46 72 2f 66 67 7a 4e` = `"chinaHEX_Fr/fgzN"`（`.mpk` 本体也带 `china`+`HEX_` 前缀）

| entry_index | resource_tag_raw | hash_candidate | offset | stored_size | flags | payload first bytes | payload SHA-256 | actual_read_size | format/compression | result |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| 1 | `\x1apPS` | `F6AEA615` | 110,384,487 | 21,018 | 0 | `06 00 00 00 14 cf a5 00…` | `03BA907F…ADF6A5` | 21,018 | u32 头(=6)，未解码 | PAYLOAD_READ |
| 2 | `\x14ePS` | `80A151C4` | 120,609,155 | 766,806 | 0 | `4c 5a 4d 41…` = `LZMA` | `A064FAA7…2103B` | 766,806 | **LZMA**（已解压） | PAYLOAD_READ |
| 5 | ` lPS` | `D29D6F69` | 112,458,399 | 1,896 | 0 | `01 00 00 00 2c fa…` | `02200C56…B7BA5A` | 1,896 | u32 头(=1)，未解码 | PAYLOAD_READ |
| 7 | `\x15ePS` | `00FD7B7C` | 91,785,543 | 17,871 | 0 | `03 00 00 00 21 61…` | `07C96CC6…1E1C0D` | 17,871 | u32 头(=3)，未解码 | PAYLOAD_READ |
| 10 | `\x1cePS` | `DA32D14A` | 111,933,168 | 2,450 | 0 | `01 00 00 00 d6 3e…` | `1996627B…7A1B6B` | 2,450 | u32 头(=1)，未解码 | PAYLOAD_READ |

> 5 个样本全部 `actual_read_size == stored_size`（读满），说明 `stored_size` 是有效边界。

### 样本 2 解压结果（LZMA 块格式已破解）

```text
block 头：
  +0x00 "LZMA"            (4 B magic)
  +0x04 uncompressed_size  u32LE = 3,452,000
  +0x08 props              = 0x5D (lc=3 lp=0 pb=2)
  +0x09 dict_size          u32LE = 0x00400000 (4 MiB)
  +0x0D LZMA raw stream

解压：用标准 lzma FORMAT_ALONE，重建 13 字节头（props + dict + 8B size）后解压成功
  → 输出 3,452,000 字节（与 uncompressed_size 精确一致）
  → payload SHA-256: 5B6CF379F46DEAFDCE4416C4C0E22A100B742B7F1A3CECABED02387D39831310
  → payload 首字节: fb 00 00 00 b4 d4 88 51 0c fc 4e 00 …（自定义容器，非 DXBC/DXIL）
```

---

## 2. 六个必答

1. **mpkinfo 如何对应 mpk** → 同 basename 配对（`Resources.mpkinfo` ↔ `Resources.mpk`）；entry 的 `offset` 是 `.mpk` 内的**绝对字节偏移**（W-R01 已证 `offset+size ≤ mpk size` 零违例）。
2. **offset 指向 payload 还是 block header** → **指向 block**（不是裸 payload）。块首要么是 `LZMA` magic（压缩块），要么是小 u32 头（1/3/6，另一类块）。
3. **stored_size 是否是有效读取边界** → **是**。5/5 样本读满不短；对 LZMA 块，`stored_size` = 块总长（magic+头+压缩数据）。
4. **payload 是否可静态识别** → **部分**。块头可识别（`LZMA`）；解压后是自定义容器（首字节 `fb 00 00 00`），**不是**标准 shader magic（DXBC/DXIL），内层格式待查。
5. **是否存在普通压缩** → **是**，LZMA（标准，样本内无需密钥），已用标准库解压成功。
6. **是否出现需要 protected bypass 的迹象** → **NOT_OBSERVED_IN_TESTED_SCOPE**（仅限已测样本；不得据此推断所有 archive 无保护）。

---

## 3. Gate 判定

| Capability | Result |
| --- | --- |
| mpkinfo entry → archive 定位 | **YES（静态、确定性）** |
| stored_size 作为读取边界 | **YES** |
| 普通压缩识别 | **YES（LZMA，已解压验证）** |
| 解压得到裸资源字节 | **YES（type A 块）** |
| 全块类型解码 | **PARTIAL（type B 小 u32 头未解码）** |
| 解压后资源可识别为标准格式 | **NO（自定义容器，非 DXBC）** |
| 需要 protected bypass | **NOT_OBSERVED_IN_TESTED_SCOPE** |

→ **STATIC_EXTRACTION_PARTIAL**

---

## 4. STOP / 边界记录

- ✅ 仅读 `.mpk` 指定 offset/size 区间，未批量导出。
- ✅ 仅解压 1 个 LZMA 样本到内存验证，未落盘、未导出。
- 🛑 未处理 `HEXB_` 变体；未研究 `.mpk` 头 `chinaHEX_` 的编码层（视为混淆，不进入解码边界）。
- 🛑 未研究密钥/解密链；未进运行时；未 hook/inject/memory dump；未反作弊。

## 5. 下一步（需 Lead 放行）

- 若要继续：W-R04 前先补齐 **type B 块头格式**（小 u32 1/3/6 语义）与 `.mpk` 头 `chinaHEX_` 是否只是前缀、数据区起点在哪 —— 仍是纯静态格式问题，不含加密。
- 本次停在 R3，不执行 W-R04 及以后。
