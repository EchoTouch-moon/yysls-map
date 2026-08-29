# RawNarrativeObservation — Schema v2

> Task: NEX-004A / H-NEX-004A · `schema_version = "raw-narrative-observation-2"`
> 由 `tools/research/windows-static-archive/nex004a_normalizer.py` 生成（selftest 覆盖）。
> 原则：observation only；`framing_tag_raw` 为原始字节，**绝不称 Lua constant tag**；
> 所有值受 `MAX_LOCATOR_BYTES = 64`（**UTF-8 bytes，非字符数**）约束；无 canonical 写入。

## 字段

```text
provenance:
  schema_version            "raw-narrative-observation-2"
  extractor_commit          生成记录的 extractor 的精确 Git commit（必须可 checkout 复现）
  extractor_source_sha256   extractor 源文件 SHA-256（双保险）
  game_version              来自 Patch/patching_version.txt；缺失则 FAIL
  archive                   archive 文件名
  archive_sha256            archive 全文件 SHA-256（流式）
  mpkinfo_sha256            mpkinfo 全文件 SHA-256
  entry_index
  entry_offset
  entry_stored_size
  flags_raw
  block_sha256              该 entry 块的 SHA-256

container:
  lua_version               "5.4"
  source_status             EXACT | SEGMENTED_PARTIAL | UNAVAILABLE
  source_locator            EXACT=observed path；SEGMENTED_PARTIAL=lossy candidate
  source_segments[]         {value, truncated}（可打印段，逐段 bounded）
  source_reconstruction     SEGMENTED_PARTIAL 时为 "PRINTABLE_RUN_JOIN"（人工 "/" 连接，
                            不是 observed bytes）；EXACT 为 null
  source_truncated          bool

strings[]（每个目标字符串）:
  byte_offset
  framing_tag_raw           原始 framing 字节（hex），无 Lua constant 语义
  encoded_length            长度 varint 解码值
  value_byte_length         UTF-8 字节数
  short_value               ≤64 UTF-8 bytes 的 locator
  value_truncated           bool
  framing_status            FRAMED_PLAINTEXT | FRAMED_CANDIDATE | SOURCE_PATH_TEXT

references[]:
  raw_value                 ≤64 UTF-8 bytes
  value_truncated           bool
  byte_offset
  source_kind               source_path | block_string
  pattern_kind              TASK_REF_CANDIDATE | REGION_REF_CANDIDATE |
                            SCRIPT_FAMILY_CANDIDATE | FIELD_KEY_CANDIDATE |
                            TEXT_LOOKUP_KEY_CANDIDATE | TEXT_REF_CANDIDATE |
                            CHARACTER_TOKEN | UNKNOWN
  confidence                MEDIUM（framing 完全匹配）| LOW

warnings[]:
  INSTRUCTION_SERIALIZATION_VARIANT    H-NEX-003T 冻结结论
  CONSTANT_OWNERSHIP_UNKNOWN
  PROTO_OWNERSHIP_UNKNOWN
  SEMANTIC_ROLE_UNVERIFIED
  SOURCE_SEGMENTED_SERIALIZATION      （仅 SEGMENTED_PARTIAL）
```

## Taxonomy（H-NEX-004A 固定，证据语义）

```text
dq_*                TASK_REF_CANDIDATE
EXPANSION_*         REGION_REF_CANDIDATE
storyline_data      SCRIPT_FAMILY_CANDIDATE
MSD_ST              SCRIPT_FAMILY_CANDIDATE
NodeGraphData       FIELD_KEY_CANDIDATE
TextByNo            TEXT_LOOKUP_KEY_CANDIDATE
70276               TEXT_REF_CANDIDATE
江晏                 CHARACTER_TOKEN
```

全部保留 `SEMANTIC_ROLE_UNVERIFIED`。

## Fail-closed（H6）

- `game_version` 缺失/UNKNOWN → 非零退出。
- `extractor_commit` 缺失/unknown → 非零退出。
- mpkinfo：version==3、size == 8+count*20+16、entry raw 恰好 20B。
- block：`\x1bLua`、version 0x54、format 0、LUAC_DATA 精确、size 4/8/8。

## MAX_LOCATOR_BYTES 语义（H5）

`locator(value, 64)`：UTF-8 encode → 截到 64 bytes → 修剪被切断的多字节码点尾部 → decode。
selftest 覆盖 ASCII cap / CJK cap / UTF-8 边界（不残留 dangling lead byte）。
