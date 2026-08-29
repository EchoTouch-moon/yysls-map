# W-R04 — Archive Candidate Discovery

> Task-ID: W-R04 · Owner: Windows · Status: **DONE** · Gate: **NARRATIVE_CANDIDATES_FOUND**
> 范围：全部 version=3 可解析 `.mpkinfo` + matching `.mpk`。静态只读，未解包 bulk、未运行时、未研究密钥/反作弊。

---

## 0. 结论（一句话）

叙事 metadata 候选已定位：**`LT*.mpk` 系列（尤其 `LT<N>1` 单号文件）是 quest/task/story/dialog/npc/string + qinghe/qingzhou/qiyu/anchong(暗涌) + 中文（清河、江晏）的高密度载体**。`Resources.mpk` 只是着色器（format reference），`Patch100x.mpk` 是图片（JPEG/PNG）。Gate = **NARRATIVE_CANDIDATES_FOUND**。

---

## 1. Phase A — Archive Census（version=3 可解析，含 matching .mpk）

| archive 族 | 数量 | entry 数/个 | name mode | block 内容 | 判定 |
| --- | ---: | ---: | --- | --- | --- |
| `Resources.mpkinfo`（root/deploy/`yysls_fast` 三份） | 3 | 625/686 | fragment | SHADER（DXBC/DXIL）+ LZMA + TABLE | 着色器，format reference 仅此 |
| `Patch1001..1009.mpkinfo` | 9 | 11~36 | hash-only | **JPEG/PNG 图片**（`FFD8FFE0`/`89504E47`），flags 2002/2018 | 纹理，非叙事 |
| `LT*.mpkinfo`（LT1..LT322） | 62 | 10~3034 | fragment | 二进制块（flags 2/62/102/142/182/522…），含**叙事关键词** | **叙事候选** |
| `TinyFiles_*.mpkinfo` / `MpkCached_*.mpkinfo`（区域命名：bjs/hexi/jiangnan/kaifeng/pkg/qingzhou） | ~25 | 2~389136 | hash-only / mixed | **无 matching .mpk**（其数据在别处，未在本轮追踪） | index-only，待定 |

> 注意：`TinyFiles_mid_qingzhou` / `MpkCached_common_qingzhou` 等区域 index 是 **hash-only**（无语义名）且 **无同 basename .mpk**；`qingzhou=清河` 仍 **UNRESOLVED**，不当作事实。

---

## 2. Phase B — Candidate Classification

### 2.1 英文叙事关键词（ASCII，raw 扫描 .mpk）

`LT<N>1` 单号文件（LT1/11/21/31/41/51/61/71/81/91/101/111/121/131/141/151/161…）全部高信号；`LT<N>2` 双号文件低信号（assets 侧）。

| archive | quest | task | story | dialog | npc | string | qinghe | qingzhou | qiyu | anchong |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LT71 | 41 | 656 | 774 | 110 | 847 | 659 | 20 | 34 | 20 | 2 |
| LT51 | 44 | 645 | 785 | 113 | 886 | 653 | 14 | 23 | 22 | 0 |
| LT31 | 45 | 623 | 732 | 101 | 832 | 676 | 19 | 15 | 21 | 0 |
| LT81 | 35 | 614 | 732 | 101 | 835 | 637 | 18 | 32 | 17 | 1 |
| LT161 | 46 | 598 | 725 | 105 | 787 | 627 | 20 | 30 | 19 | 0 |
| LT141 | 46 | 596 | 711 | 85 | 832 | 608 | 21 | 20 | 15 | 0 |
| LT21 | 34 | 600 | 682 | 97 | 757 | 612 | 10 | 21 | 25 | 0 |
| LT11 | 42 | 553 | 683 | 98 | 722 | 573 | 15 | 19 | 11 | 1 |
| LT1 | 36 | 567 | 698 | 106 | 713 | 496 | 16 | 25 | 16 | 1 |

（`anchong` = 暗涌拼音；`qiyu` = 奇遇。`mingchao`/`localization` 仅在个别文件出现。）

### 2.2 中文关键词（UTF-8，逐 entry 定位）

| 关键词 | 命中 | 定位 |
| --- | --- | --- |
| **清河** | LT51×2、LT1×1、LT31×1、LT71×3、LT91×1 | 均落入具体 entry（如 LT71 entry[1631] flags=142、LT1 entry[2817] flags=2、LT51 entry[1178] flags=102） |
| **江晏** | LT71 entry[1768]（flags=142） | **具体角色名**出现在叙事块 |
| 神仙不渡 / 又见新来燕 / 又见新燕来 / 明潮 / 暗涌 / 红线 / 寒香寻 / 田英 / 王清 | 0 字面命中 | 以 **ID/key** 存，非明文（符合游戏文本走 localization key 的惯例） |

> 上下文：命中处周围为二进制（不可打印字节），即叙事字符串**嵌入二进制块**（非明文表），但同一 block 内可见 ASCII 字段名（quest/task/story/npc/string…）。

---

## 3. Phase C — Rank Candidates（Top 10，供 W-R05 定向 probe）

| rank | archive | 依据 |
| ---: | --- | --- |
| 1 | **LT71.mpk**（15.5MB，2862 entries） | 清河×3 + **江晏×1**（角色级证据）；task=656/story=774/npc=847/string=659 |
| 2 | **LT51.mpk**（15.9MB，3034） | 清河×2；story=785/npc=886 最高 |
| 3 | **LT31.mpk**（17.0MB，3004） | 清河×1；string=676 最高 |
| 4 | LT81.mpk | 清河×1；qingzhou=32 |
| 5 | LT161.mpk | 清河×1；qingzhou=30 |
| 6 | LT141.mpk | 清河×1；qinghe=21 |
| 7 | LT21.mpk | qiyu=25 最高 |
| 8 | LT101 / LT121 / LT151 | 高 task/story/npc 密度 |

**R05 建议切入点**：先解 LT71 的 entry[1631]（清河）与 entry[1768]（江晏），确认其 block 格式（flags=142）是否为 quest/task 表；再横向比对 LT31/51/81 的同类块。

---

## 4. 边界检查

- ✅ 全部静态只读；raw 关键词扫描未落盘 bulk payload；未解包。
- 🛑 未处理 `HEXB_` 变体、未解析 `chinaHEX_` 混淆层、未研究密钥/解密链。
- 🛑 未运行时、未 hook/inject/memory dump、未反作弊、未批量导出。

## 5. Gate

> **NARRATIVE_CANDIDATES_FOUND**

- 高密度叙事关键词（quest/task/story/dialog/npc/string + qinghe/qingzhou/qiyu/anchong）存在于 **LT*.mpk**。
- 中文**清河、江晏**字面命中并落到具体 entry，证明是叙事/世界观数据而非巧合。
- 具体任务名（神仙不渡等）未字面出现 → 预计以 ID/localization key 形式存，R05 需确认 schema。

## 6. 下一步（W-R05，待 Lead 放行）

对 LT71/LT51/LT31 的叙事块做定向 probe：判断是否含 `quest_id / task_id / chapter_id / parent_id / prerequisite / sort_order / npc_ref / story_thread / localization_key` 等结构字段；确认 LT block 格式（flags 2/62/102/142/182 语义）与是否可稳定读取。
