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
└── samples/                  ← 本地研究样本（.mpkinfo 副本，gitignored，不进 Git）
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

## 状态

- W-R00 Baseline Freeze：DONE
- W-R01 MPKINFO Structural Inspection：DONE（R1 = PASS）
- W-R02 Deterministic Index Parser：DONE（`inspect_mpkinfo.py`，R2 = PASS）
- W-R03 Index→Archive Linkage Probe：DONE（`probe_archive_mapping.py`，Gate = **STATIC_EXTRACTION_PARTIAL**）
- W-R03.5 Block & Container Classification：DONE（Gate = **CONTENT_CLASSIFICATION_READY**）
- W-R04 Archive Candidate Discovery：DONE（Gate = **NARRATIVE_CANDIDATES_FOUND**；叙事候选 = `LT*.mpk`）
- W-R05 Narrative Metadata Schema Probe：DONE（Gate = **R5_SCHEMA_AND_JOIN_FOUND**；叙事 = `LuaT` 容器 + 编译 Lua）
- W-R06 Static Extraction Decision：DONE（建议 = **MINIMAL_EXTRACTOR_GO**，边界 = LT/LuaT narrative metadata only）
- 下一阶段（extractor implementation）：WAITING_FOR_LEAD_AUTHORIZATION

## W-R03 关键结论

`.mpk` 块可静态定位；存在普通 LZMA 压缩（无加密/无密钥），type A 块已用标准库解压验证；另有 type B 块（小 u32 头）未解码，故 Gate = PARTIAL（非 NO_GO）。详见 `docs/research/evidence/windows/wave-1.6/asset-feasibility/archive-linkage.md`。
