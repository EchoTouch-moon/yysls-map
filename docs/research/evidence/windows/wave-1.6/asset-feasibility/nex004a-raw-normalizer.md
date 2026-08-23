# NEX-004A — Raw Narrative Observation Normalizer

> Task-ID: NEX-004A · Status: **DONE** · Gate: **RAW_NORMALIZATION_PASS**
> Base: `research/windows-evidence-tooling` @ `ed5d9ad`
> Precondition：H-NEX-003T = INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED（Lua VM/body research CLOSED）
> Committed tool：`tools/research/windows-static-archive/nex004a_normalizer.py`（selftest PASS）

---

## 0. 结论（一句话）

不依赖私有 instruction serialization，将 4 个 frozen pilot 块的可静态观察 narrative metadata 规范化为 **RawNarrativeObservation** 记录：完整 provenance（archive/mpkinfo/block SHA-256 全部与 frozen ledger 吻合）、source 观察（EXACT / SEGMENTED_PARTIAL）、目标字符串观察（7/7 按样本出现处全部恢复）、带 pattern_kind/confidence 的 reference 观察、四类强制 warning。**RAW observation ≠ canonical，未写 canonical。**

## 1. 工具与 schema

`nex004a_normalizer.py`：

```text
RawNarrativeObservation v1:
  provenance : schema_version, extractor_commit, game_version, archive,
               archive_sha256, mpkinfo_sha256, entry_index, entry_offset,
               entry_stored_size, flags_raw, block_sha256
  container  : lua_version, source_status(EXACT|SEGMENTED_PARTIAL|UNAVAILABLE),
               source_path_observed
  strings    : byte_offset, framing_tag_raw, encoded_length, value_byte_length,
               short_value, framing_status
  references : raw_value, byte_offset, source_kind, pattern_kind, confidence
  warnings   : [INSTRUCTION_SERIALIZATION_VARIANT, CONSTANT_OWNERSHIP_UNKNOWN,
                PROTO_OWNERSHIP_UNKNOWN, SEMANTIC_ROLE_UNVERIFIED,
                (+SOURCE_SEGMENTED_SERIALIZATION if segmented)]
```

- `game_version` = `20260820220319`（`Patch/patching_version.txt`）。
- `extractor_commit` = 运行时 `git rev-parse HEAD`（ed5d9ad，本任务产出前）。
- 哈希：archive/mpkinfo 流式 SHA-256；block 直接计算。**全部与 frozen ledger 一致**。
- **`framing_tag_raw` 为原始字节，绝不称为 Lua constant tag。**
- **MAX_LOCATOR_BYTES = 64**：所有 value/locator 截断到 64B；无 bulk string dump / 无完整对白 / 无完整脚本。

## 2. Pilot 结果（4 样本）

| entry | source_status | source_path_observed | 恢复的目标 |
| --- | --- | --- | --- |
| LT71[1768] | SEGMENTED_PARTIAL | `@hexm/client/storyline_data/wanfa/MSD_ST/ZDQ/dq_610900.lua` | dq_610900、storyline_data、MSD_ST（source）、NodeGraphData、江晏 |
| LT71[1631] | SEGMENTED_PARTIAL | `@hexm/client/ui/windows/yankov/storage/cangpin_sub_#homeland_display_side_page.lua` | EXPANSION_QINGHE、TextByNo |
| LT31[874] | **EXACT** | `@Sunshine/AI/bt2code/output/u_newplay_horserob_thin_qifen.lua` | 70276 |
| LT51[1178] | SEGMENTED_PARTIAL | `@hexm/client/ui/windows/common/_player_float.lua` | （7 个目标均不存在，符合预期）|

**目标恢复 7/7（按样本出现处）**：

| 目标 | 样本 | source_kind | pattern_kind | confidence |
| --- | --- | --- | --- | --- |
| dq_610900 | LT71[1768] | source_path | SCRIPT_FAMILY_CANDIDATE | LOW |
| storyline_data | LT71[1768] | source_path | SCRIPT_FAMILY_CANDIDATE | LOW |
| MSD_ST | LT71[1768] | source_path | SCRIPT_FAMILY_CANDIDATE | LOW |
| NodeGraphData | LT71[1768] | block_string | FIELD_KEY_CANDIDATE | MEDIUM |
| 江晏 | LT71[1768] | block_string | CHARACTER_TOKEN | MEDIUM |
| EXPANSION_QINGHE | LT71[1631] | block_string | TEXT_LOOKUP_KEY_CANDIDATE | MEDIUM |
| TextByNo | LT71[1631] | block_string | FIELD_KEY_CANDIDATE | MEDIUM |
| 70276 | LT31[874] | block_string | TASK_REF_CANDIDATE | MEDIUM |

- confidence = MEDIUM 仅当 framing 完全匹配 `tag + len(varint) == value_len + 1`（FRAMED_PLAINTEXT）；source 内文本为 LOW（无 framing 语义）。
- 所有 reference 均带 `SEMANTIC_ROLE_UNVERIFIED`。

## 3. Hash 交叉验证（frozen ledger）

| entry | block_sha256 匹配 |
| --- | --- |
| LT71[1768] | ✓ `3504BD0C...` |
| LT71[1631] | ✓ `D3C2930D...` |
| LT31[874] | ✓ `DA4DCE48...` |
| LT51[1178] | ✓ `8AE24367...` |

archive / mpkinfo SHA-256 亦与 ledger 一致（LT71.mpk `42C9D328...`、LT71.mpkinfo `F5F8F157...` 等）。

## 4. Gate

> **RAW_NORMALIZATION_PASS**

- 4/4 pilot 记录完整、可复现（固定 schema + 固定 provenance + 哈希可验证）。
- 目标 7/7 按样本出现处恢复。
- 未做任何语义化越级：无 constant index / 无 owning proto / 无 CFG / 无 opcode 工作。
- **STRUCTURAL_NORMALIZATION_PASS 未声明**（source 仅 LT31 为 EXACT；segmented serialization 未解码）。
- PROVENANCE 完整（game_version、commit、三组哈希均在）→ 非 PROVENANCE_INCOMPLETE。

## 5. 交付物

- `tools/research/windows-static-archive/nex004a_normalizer.py`（selftest PASS；bounded read + fail closed + MAX_LOCATOR_BYTES=64）。
- `docs/research/evidence/windows/wave-1.6/nex004a-raw-observations/LT{71,31,51}-entry{1768,1631,874,1178}-raw-observation.json`（4 条记录，UTF-8）。
- `docs/research/evidence/windows/wave-1.6/asset-feasibility/nex004a-raw-normalizer.md`（本报告）。
- 无 canonical 写入；canonical v0.1 保持 FROZEN。

## 6. 状态

```text
NEX-004A                 CLOSED / RAW_NORMALIZATION_PASS
NEX-004A 记录            RAW observations（非 canonical）
Canonical v0.1           FROZEN
下一步（如 Lead 放行）    STRUCTURAL_NORMALIZATION 评估 / canonical 更新
```
