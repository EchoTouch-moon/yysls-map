# windows-static-archive — 静态资源索引研究工具（Windows / Wave 1.6）

> 用途：离线、只读地研究本机已安装《燕云十六声》的 `.mpkinfo` 资源索引格式。
> 边界：不解析/不解包 `.mpk` payload，不接触密钥、不运行时注入、不反作弊。见
> `docs/execution/WAVE_1_6_WINDOWS_STATIC_ARCHIVE_TASKS.md` §1。

## 文件

```text
tools/research/windows-static-archive/
├── README.md                 ← 本文件
├── inspect_mpkinfo.py        ← W-R02 deterministic index parser（已交付）
├── probe_archive_mapping.py  ← W-R03 index→archive→payload linkage probe（已交付）
├── probe_luat_dialect.py     ← NEX-002 LuaT bytecode dialect fingerprint（已交付）
├── probe_lua54_metadata.py   ← H-NEX-003R official Lua 5.4 varint/proto walk（已交付）
├── verify_proto_boundary.py   ← H-NEX-003S/T proto boundary & post-code verifier（83-opcode enum）
├── framing_probe.py           ← H-NEX-003T LT31 instruction framing probe（已交付）
├── probe_instruction_layout.py← H-NEX-003U bytewise 4B record layout probe
├── probe_semantic_fields.py   ← H-NEX-003V semantic field validation probe
├── probe_postcode_framing.py  ← H-NEX-003W post-code framing classifier
├── probe_segment_split.py     ← H-NEX-003X post-code segment split probe
├── probe_varint_walk.py       ← H-NEX-003Y varint-led record walk probe
├── probe_tag_grammar.py       ← H-NEX-003Z full-tail tag-grammar walk probe
├── nex004a_normalizer.py      ← NEX-004A raw narrative observation normalizer（已交付）
├── discovery_engine.py        ← NEX-004B generic structural discovery engine（已交付）
├── blind_manifest.json        ← NEX-004B frozen blind manifest（Commit A 冻结）
├── narrative_holdout_selector.py ← NEX-004C holdout selector（C0 冻结）
├── qinghe_packet_builder.py    ← NEX-005 Qinghe evidence packet builder（P0 冻结）
└── samples/                   ← 本地研究样本（.mpkinfo 副本，gitignored，不进 Git）
```

## 用法

```bash
python inspect_mpkinfo.py <file.mpkinfo> --summary
python inspect_mpkinfo.py <file.mpkinfo> --list --limit 50
python inspect_mpkinfo.py <file.mpkinfo> --extensions

python probe_archive_mapping.py <file.mpkinfo> <file.mpk> --limit 5 --ext PS,VS,CS
```

## 已知格式摘要（W-R01 结论）

```text
header  : uint32 LE version(=3) + uint32 LE entry_count   (8 B)
entry   : 20 B fixed × entry_count
  +0x00 name_fragment u32   (部分名 / 16-bit hex hash；非完整路径)
  +0x04 hash          u32   (逐 entry 唯一)
  +0x08 offset        u32   (在 .mpk 内字节偏移；目录=0)
  +0x0C stored_size   u32   (存储大小；目录=0)
  +0x10 flags         u32   (1=目录/空，0=文件；patch 索引另有取值)
trailer : 16 B（用途未知）
```

另有 `HEXB_` 前缀 + base64 的**混淆变体** `.mpkinfo`（非 version=3），parser 对其 fail-closed 拒绝。

## 验证（H-NEX-001）

```bash
python inspect_mpkinfo.py --selftest
#   → selftest PASS（exit 0）

python inspect_mpkinfo.py samples/main_Resources.mpkinfo --summary
#   → version 3 / entry_count 625（exit 0）

# fail-closed（均 exit 1，REJECT）：
#   截断（truncated）           → ERROR: fail-closed: truncated ...
#   额外尾随字节（extra bytes） → ERROR: fail-closed: unexpected trailing data ...
#   version≠3（unknown）        → ERROR: fail-closed: unsupported version ...
#   HEXB 变体                  → ERROR: fail-closed: unsupported version ...（"HEXB_" 被读作非法 version）
#   count 不符（size mismatch） → ERROR: fail-closed: truncated/unexpected trailing ...

python probe_archive_mapping.py samples/main_Resources.mpkinfo E:\yysls\Resources.mpk --limit 1 --ext PS
#   → 正常 probe（exit 0）；含 bounds check + MAX_PROBE_BYTES=1MiB + streaming SHA-256 + LZMA magic 识别

python probe_archive_mapping.py samples/main_Resources.mpkinfo E:\yysls\Resources.mpk --ext ZZ
#   → ERROR: no matching samples ...（exit 1，显式失败）
```

## 状态

- W-R00 Baseline Freeze：DONE
- W-R01 MPKINFO Structural Inspection：DONE（R1 = PASS）
- W-R02 Deterministic Index Parser：DONE（`inspect_mpkinfo.py`，R2 = PASS）
- W-R03 Index→Archive Linkage Probe：DONE（`probe_archive_mapping.py`，Gate = **STATIC_EXTRACTION_PARTIAL**）
- W-R03.5 Block & Container Classification：DONE（Gate = **CONTENT_CLASSIFICATION_READY**）
- W-R04 Archive Candidate Discovery：DONE（Gate = **NARRATIVE_CANDIDATES_FOUND**；叙事候选 = `LT*.mpk`）
- W-R05 Narrative Metadata Schema Probe：DONE（Gate = **R5_SCHEMA_AND_JOIN_FOUND**；叙事 = `LuaT` 容器 + 编译 Lua）
- W-R06 Static Extraction Decision：DONE（建议 = **MINIMAL_EXTRACTOR_GO**，边界 = LT/LuaT narrative metadata only）
- NEX-002 LuaT Dialect Identification：DONE（Gate = **DIALECT_PARTIAL_CONSTANTS_READABLE**；Lua 5.4 32-bit Instruction + 修改版 header 尾，见 H-NEX-002 修订）
- NEX-003 Minimal Constant/Proto Reader：DONE（Gate = **BODY_LAYOUT_PARTIAL**；header/source 定位成功，Proto/constant 确定性解析被 custom body 布局阻塞）
- H-NEX-003 Varint/Proto Reparse：DONE（Gate = **BODY_VARIANT_CONFIRMED**；source varint(convB) + header variant + string constant 编码确认，5 token 定位成功；sizecode→code→protos 全遍历残留未解析）
- H-NEX-003R Official Varint/Proto Walk：DONE（Gate = **PROTO_PARTIAL_AFTER_OFFICIAL_VARINT**；官方 MSB-first loadUnsigned 确认；sizecode `01 YY`=236/245，4/4 code 区域合法指令流；**sizek @ code_end 失败（custom post-code variant）**）
- H-NEX-003S Proto Boundary & Post-Code Validation：DONE（Gate = **BOUNDARY_PARTIAL**；LT31 control source/header 确定性确认；**code 官方 79-opcode enum 下 51 条非法**；sizek@code_end 四样本全失败；segmented = SOURCE_SERIALIZATION_PARTIAL）
- H-NEX-003T LT31 Instruction Framing：DONE（Gate = **INSTRUCTION_SERIALIZATION_VARIANT_CONFIRMED**；opcode 表修复为 83；LT31 invalid=46；H0-H3 framing hypotheses 全部失败 → Lua body research 收口）
- H-NEX-003U bytewise layout follow-up：**CANDIDATE**（四样本及三组归档复核显示稳定的 `[opcode,A,B,C]` 4B 记录；不等同于已恢复 opcode 语义或 Lua VM）
- H-NEX-003V Semantic Field Validation：DONE（Gate = **SEMANTIC_FIELD_VALIDATION_PARTIAL**；跨版本稳定的操作码条件操作数族：双向位移族 0x5C/0x5D/0xDC(+0xDD/0x9F) 与索引/计数族 0x60/0x8C/0x1D/0x0C/0x61；无 EXTRAARG 式强耦合；code 后为非官方 string-like framing）
- H-NEX-003W Post-Code Framing Classification：DONE（Gate = **POSTCODE_FRAMING_PARTIAL**；code_end 后为密集交错的标识符风格文本（空格占比 0.005），无固定头部、无边界对齐长度前缀；0x04 为跨版本稳定的分隔符/标签候选（42-44% 最长游程以其终止））
- H-NEX-003X Segment Split on Delimiter Candidates：DONE（Gate = **SEGMENTATION_PARTIAL**；0x04 强分隔符假设被证伪（D0 纯可打印段仅 2.9-3.0%，D2 最高 13.1%）；非纯段首字节稳定落在 0x85-0x91（varint 终止字节特征），`83 01` 为各归档最高频首二元组 → 工作假设改为 varint-led record grammar，0x04 可能是 varint 续字节）
- H-NEX-003Y Varint-Led Record Walk：DONE（Gate = **VARINT_WALK_PARTIAL**；naive `[varint][v-1 payload]` 行走在首条记录即失败，但尾部 +0 处 varint 值呈稳定双族结构：小值族 {5..13,17,30}（8/17 领先）与 512+k 族（520=512+8、529=512+17、542=512+30，续字节 0x04）→ 定量确认 0x04 为 varint 续字节而非分隔符；值更像 tag/类型 ID 而非字符串长度）
- H-NEX-003Z Tag-Grammar Record Walk：DONE（Gate = **TAG_GRAMMAR_PARTIAL**；全块尾部消除 256B 窗口伪影（512+k 首记录完成率 0.91-0.93）；判别式回答为否——v 与 v+512 不共享 payload 形态：裸 tag 8/17 的 payload 可打印率 0.71-0.85（字符串样），512+k 全部 0.0（二进制），tag 值预测 payload 类型；首单元可消费但 record-2 边界是瓶颈，全尾行走覆盖 ≈0；N 嵌套形状被拒）
- 2026-08-28 baseline drift：LT31/LT51/LT71 patch 文件被 launcher 重写（count/sha256 变化，已重新冻结为 WIN16-AF-017..022）；H-NEX-003U 的逐 entry 计数对应更新前文件集，不直接可比
- NEX-004A Raw Narrative Observation Normalizer：DONE（Gate = **RAW_NORMALIZATION_PASS**；4 pilot 记录完整 provenance + 哈希与 ledger 吻合；目标 7/7 恢复；RAW ≠ canonical）
- H-NEX-004A Provenance & Encoding Hardening：DONE（schema v2；两阶段 provenance freeze；UTF-8-safe 输出；byte cap；taxonomy 修正；fail-closed）
- 下一阶段（NEX-004B Structural Discovery / canonical 更新）：WAITING_FOR_LEAD_AUTHORIZATION

## W-R03 关键结论

`.mpk` 块可静态定位；存在普通 LZMA 压缩（NOT_OBSERVED_IN_TESTED_SCOPE），type A 块已用标准库解压验证；另有 type B 块（小 u32 头）未解码，故 Gate = PARTIAL（非 NO_GO）。详见 `docs/research/evidence/windows/wave-1.6/asset-feasibility/archive-linkage.md`。
