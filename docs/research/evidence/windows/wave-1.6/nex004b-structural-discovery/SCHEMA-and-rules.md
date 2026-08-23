# NEX-004B — Structural Discovery: Frozen Schema, Rules & Blind Manifest

> Task: NEX-004B Structural Discovery & Generalization Pilot
> 本文件在 **Commit A** 冻结（引擎 + 规则 + blind manifest + selftest），之后不得修改并仍称同一轮 blind validation。
> Committed engine：`tools/research/windows-static-archive/discovery_engine.py`（selftest PASS）

## 1. Frozen classifier rules（R1..R5，ordered，first match wins）

```text
R1  ^dq_[0-9]+$                    -> TASK_REF_CANDIDATE
R2  ^EXPANSION_[A-Z0-9_]+$         -> REGION_REF_CANDIDATE
R3  ^[0-9]{4,10}$                  -> TEXT_REF_CANDIDATE
R4  ^[A-Za-z_][A-Za-z0-9_]{2,47}$  -> IDENTIFIER_TOKEN_CANDIDATE
R5  ^[\u4e00-\u9fff]{2,4}$         -> SHORT_CJK_TERM_CANDIDATE
```

- **不** generic-classify CJK 为 CHARACTER_TOKEN；**不** generic-classify identifier 为 FIELD_KEY。
- confidence：TASK_REF/REGION_REF/TEXT_REF/SHORT_CJK_TERM = MEDIUM；IDENTIFIER = LOW（generic 类，噪声风险高）。

## 2. Discovery methods（generic，无 TARGETS allowlist）

```text
FRAMED_STRING_SCAN  块内扫描 [tag in {04,05,06,07,08,14,15,16}][len varint][len-1 bytes]
                    可打印值，用 R1-R5 分类。framing_tag_raw 为原始字节，无 Lua constant 语义。
SOURCE_PATH_SCAN    对观察到的 source path 分量（按 '/' 与 '.' 切分）用 R1-R5 分类。
```

## 3. Record schema（`raw-structural-observation-1`）

```text
provenance : schema_version, extractor_commit, extractor_source_sha256,
             game_version, archive, archive_sha256, mpkinfo_sha256,
             entry_index, entry_offset, entry_stored_size, flags_raw, block_sha256
container  : lua_version, source_status, source_locator, source_segments[],
             source_reconstruction, source_truncated
observations[] :
  byte_offset, framing_tag_raw, encoded_length, value_byte_length,
  raw_value, value_truncated, discovery_rule_id, discovery_method,
  pattern_kind, confidence,
  provenance {schema_version, extractor_commit, archive, entry_index, block_sha256}
observation_limits : max_locator_bytes=64, max_per_entry=32, per_class_cap=8
warnings[] : INSTRUCTION_SERIALIZATION_VARIANT, CONSTANT_OWNERSHIP_UNKNOWN,
             PROTO_OWNERSHIP_UNKNOWN, SEMANTIC_ROLE_UNVERIFIED,
             (+SOURCE_SEGMENTED_SERIALIZATION if segmented)
```

## 4. Blind manifest（冻结，metadata-only selection）

- 规则：排除已知 pilot/evidence entries（LT71: 1768,1631；LT51: 1178；LT31: 874）；`stored_size ∈ [512, 1048576]`（index metadata）；按 `sha256("{arch}:{idx}:{offset}:{size}:{flags}")` 排序取前 N。
- **选择时未查看任何选中 entry 的内容**。

```text
LT71 ×4 : [534, 2766, 1490, 165]
LT51 ×2 : [861, 873]
LT31 ×2 : [552, 2876]
```

- 与 excluded 集合零重叠（已验证）。

## 5. Limits

```text
MAX_LOCATOR_BYTES        = 64（UTF-8 bytes，非字符数）
MAX_OBSERVATIONS_PER_ENTRY = 32
PER_CLASS_CAP            = 8
无 prose/dialogue dump；无 full script dump。
```

## 6. Regression（rules 冻结后对旧 4 pilot 运行，见 Commit B）

```text
期望：dq_610900 -> TASK_REF_CANDIDATE
      EXPANSION_QINGHE -> REGION_REF_CANDIDATE
      70276 -> TEXT_REF_CANDIDATE
允许：NodeGraphData/TextByNo -> IDENTIFIER_TOKEN_CANDIDATE
      江晏 -> SHORT_CJK_TERM_CANDIDATE
无语义升级（无 CHARACTER_TOKEN/FIELD_KEY 的 generic 赋予）。
```
