# W-R06 — Static Extraction Decision Packet

> Task-ID: W-R06 · Owner: Windows · Status: **DONE**
> 本轮不做新格式研究、不解析 Lua dialect、不实现 extractor。

---

## A. Provenance

| 项 | 值 |
| --- | --- |
| Game version | `patching_version=20260820220319` · `pkgversion=0-1783500887` · 注册表 `1.0.0` |
| Install root | `E:\yysls` |
| Research branch | `codex/mvp-platform` @ `ca7988a`（产物未 commit，待 Lead review 后 Git） |
| Scripts | `tools/research/windows-static-archive/inspect_mpkinfo.py`、`probe_archive_mapping.py` |

### 关键输入哈希（SHA-256）

**归档级（format reference + 叙事候选）**

| 文件 | size | SHA-256 |
| --- | ---: | --- |
| `Resources.mpkinfo` | 12,524 | `DC98DF817E390414B7FD89FDD6A0BDA764826938AB585B0E493CF8D41730468F` |
| `Resources.mpk` | 200,632,208 | `31C309B06FD8A4FAA15B37C3B076D7215FF4B7A28C78038E291F7F2FFF532E01` |
| `Win32\deploy\Resources.mpk` | 270,179,195 | `3C8E059BC7810A6EC24286D5ECAADA9D160EBCE976587F4244BFBF5C6EE24D9F` |
| `LT71.mpkinfo` / `LT71.mpk` | 57,264 / 15,490,766 | `F5F8F157…82CFCDB` / `42C9D328…6174B60` |
| `LT51.mpkinfo` / `LT51.mpk` | 60,704 / 15,950,227 | `65A53CCE…B6C6359D` / `A98EBFEA…E1BF9826` |
| `LT31.mpkinfo` / `LT31.mpk` | 60,104 / 17,012,957 | `4AE32CEF…B34AC97A` / `280639E8…D10CFA96` |

**块级（R05 探针样本，短 locator）**

| 样本 | offset / size / flags | SHA-256 |
| --- | ---: | --- |
| LT71[1631]（清河） | 12,382,428 / 11,784 / 142 | `D3C2930D…8848BFD5` |
| LT71[1768]（江晏） | 4,750,441 / 11,168 / 142 | `3504BD0C…B88B47FB` |
| LT51[1178]（清河） | 12,760,804 / 24,873 / 102 | `8AE24367…F3E13EC4` |
| LT31[874]（清河） | 1,996,455 / 11,718 / 62 | `DA4DCE48…667ACDCE` |

---

## B. Capability Matrix

| Capability | Result | Evidence |
| --- | --- | --- |
| mpkinfo parse | **YES** | version=3，`size == 8 + N×20 + 16` 全样本成立；deterministic、fail-closed |
| archive addressing | **YES** | `offset`/`stored_size` 绝对寻址，`offset+size ≤ mpk` 零违例 |
| LZMA decompress | **YES** | 标准 LZMA（`LZMA`+u32 size+props+dict），无密钥，已解压验证 |
| container classification | **YES** | 已区分 `LuaT` / LZMA / SHADER(ZZZ4+DXBC) / TABLE / EMPTY / OTHER |
| LT discovery | **YES** | `LT*.mpk` 为叙事候选；`LT<N>1` 高信号、`LT<N>2` 低信号 |
| LuaT container | **YES** | magic `LuaT` + 源码路径 + 编译 Lua，跨 entry 一致 |
| narrative strings | **YES** | 清河/江晏/天泉/红线 + quest/task/story/dialog/npc/string |
| stable refs | **YES** | `EXPANSION_QINGHE`、`storyline_data`、`MSD_ST` |
| cross-entry joins | **YES** | `EXPANSION_QINGHE` 13 entry/3 archive；`storyline_data` 671；`MSD_ST` 43；`70276`↔对话 |
| quest hierarchy | **NO（未解）** | `NodeGraphData`/`get_variables` 提示存在，但层级/父/序未解析 |
| Lua dialect | **UNKNOWN** | `LuaT` 非标准 `\x1bLua`/`\x1bLJ`；5.x / LuaJIT / 自定义未确认 |
| protected bypass / runtime | **NONE** | 全程静态、只读、无密钥/无解密链/无运行时/无反作弊 |

---

## C. Final Recommendation

> **MINIMAL_EXTRACTOR_GO**

依据：`mpkinfo → archive → LuaT block → narrative strings/stable refs` 链路**完全静态、确定性、无加密、无需运行时**已闭环；存在可跨 entry 重现的任务/区域/命名空间引用（`EXPANSION_QINGHE` / `storyline_data` / `MSD_ST` / `dq_*` / `70276`），具备产出稳定 quest/task metadata 的工程基础。

---

## D. Minimal Extractor Boundary

**只做**：`LT` / `LuaT` narrative metadata 的结构字段提取 ——

```text
quest_id / task_id / chapter_id / parent_id / prerequisite
sort_order / category / region / npc_ref / story_thread
localization_key / 稳定引用标识（EXPANSION_QINGHE、dq_*、数字 ID）
```

**不做**：
- 批量 dump 对白/脚本全文、语音、CG、贴图、模型、音频；
- 解析 `Resources.mpk` shader / `Patch100x` 图片；
- 处理 `HEXB_` 混淆变体、`chinaHEX_` 头部、密钥/解密链；
- 运行时、hook/inject、memory dump、反作弊。

---

## E. Known Unknowns

1. **Lua bytecode dialect**：`LuaT` 的具体字节码方言（Lua 5.1/5.3/LuaJIT/自定义）未确认 —— 决定常量表与代码段的解析方式。
2. **exact quest hierarchy schema**：`NodeGraphData` 如何编码 chapter/parent/prerequisite/sort_order 未解析。
3. **TextByNo 间接 localization 层**：`TextByNo` + 数字 ID（`70276`）是否指向外部文本表未确认。
4. **canonical mapping**：提取出的 native ID 如何映射到冻结的 `CanonicalStoryNode` v0.1（csn-qh-*）未定义。
5. **version drift**：`patching_version` 更新后，`.mpkinfo`/`.mpk`/LuaT 偏移与内容可能变化，需 provenance 重锚。

---

## F. STOP / Copyright

- 🛑 **不 bulk dump 完整对白或内容资产**；只产出结构字段、ID、hash、短 locator。
- 🛑 不发布/建设完整对白、脚本、语音、CG、模型、原画数据库。
- 🛑 不绕过加密/DRM/反作弊；发现需 protected bypass 时 **NO_GO**。

---

## 状态

W-R06 完成即停。**不开始 extractor implementation**，等待 Lead 对 `MINIMAL_EXTRACTOR_GO` 的最终决议与 extractor proposal 授权。
