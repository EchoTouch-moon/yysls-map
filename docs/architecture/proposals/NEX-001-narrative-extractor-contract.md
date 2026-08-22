# NEX-001 — Minimal Narrative Extractor Contract & Architecture

> Status: **GO（draft，供 Lead review）**
> Phase: NEX（Narrative Extractor）— 第一项
> 前置：J-02R = `MINIMAL_EXTRACTOR_GO`；W-R00→W-R06 = DONE（`research/windows-evidence-tooling` @ `4ce57e2`）
> 约束：本文件只定义契约与架构。**不实现 extractor**；实现需 NEX-002+ 单独 GO。

---

## 0. 目标与范围红线

**目标**：从 `LT*.mpk` 的 `LuaT` 块中，**静态、可重复**地提取「叙事结构 metadata」——不是对白，不是资产。

**一条红线**：

> **LT / LuaT Narrative Metadata Extractor**，不是通用 MPK 解包器、不是 Lua 反编译器、不是资源浏览器、不是对白导出器、不是 asset extractor。

一旦范围漂向「把客户端资源全解析出来」，立即视为 scope drift 停止。

---

## A. Input Contract

**只允许**：

```text
LT*.mpkinfo          version=3 索引
LT*.mpk              配对归档
game version metadata  patching_version / pkgversion / 注册表版本
```

**明确 out of scope**：

```text
Resources.mpk        shader（format reference 仅此）
Patch100x.mpk        JPEG/PNG 图片
HEXB_ 变体           混淆，不解析
runtime / 内存       禁止
```

---

## B. Pipeline（冻结建议）

```text
MPKINFO Reader          只读 v3 索引（8B header + N×20B entry + 16B trailer）
      ↓
Archive Entry Reader    按 offset/stored_size 绝对寻址
      ↓
Block Decoder           LZMA 解压 / 原样读取（raw）
      ↓
LuaT Detector           magic `LuaT` + 源码路径识别
      ↓
Lua Metadata Reader     常量表 / 符号键 / 数字常量（最小解析，见 C）
      ↓
Narrative Classifier    分类（region / task / character / story）
      ↓
Normalizer              产出 ExtractedNarrativeRecord（见 D）
      ↓
Evidence Record         provenance 完整（见 E）
```

**约束**：任何一层都**不得直接写 canonical dataset**。每层只读输入、产出自描述输出。

---

## C. Lua 最小解析能力（关键决策）

**不以「完整 Lua decompiler」为目标。**

extractor 最小需要（足够恢复 `dq_610900` / `EXPANSION_QINGHE` / `NodeGraphData` / `TextByNo` 即可）：

```text
source path             hexm/client/storyline_data/…
string constants        清河 / 江晏 / dq_610900 / 70276
numeric constants       u32/u64 数字常量
symbol/table keys       name / area_name / TextByNo / expansion_id
proto boundaries        function/proto 边界（可选）
references              EXPANSION_QINGHE / MSD_ST / storyline_data
simple table structure  可选；不做完整 AST/源码重建
```

**验收**：能稳定读出上述字段即可，不要求还原 Lua 源码。

---

## D. Normalized Output Contract

从「Observed Metadata」开始，**不叫 Quest**：

```text
ExtractedNarrativeRecord
  game_version
  archive            LT71
  archive_sha256
  entry_index        1631
  entry_offset
  payload_sha256

  source_path        hexm/client/storyline_data/…
  script_family      storyline_data | MSD_ST | AI | UI | other

  string_constants[]     清河 / 江晏 / dq_610900 / 70276 / EXPANSION_QINGHE
  numeric_constants[]
  symbol_keys[]          name / area_name / TextByNo / expansion_id
  reference_tokens[]     EXPANSION_QINGHE / MSD_ST / storyline_data

  region_candidates[]    清QINGHE（candidate，非 verified）
  task_candidates[]      dq_610900（candidate）
  character_tokens[]     江晏 / 天泉

  extraction_confidence  RAW | STRUCTURAL | SEMANTIC
```

> **`task_candidates` ≠ `task_id`**：直到语义跨样本验证完成才能升级。

---

## E. Provenance

任一 extracted claim 必须可反查：

```text
GameVersion
  → MPK SHA
  → MPKINFO SHA
  → entry index
  → byte offset
  → payload SHA
  → parser version
```

缺失任一级 → 记录为 provenance-incomplete，不得晋升。

---

## F. Promotion Policy

**EXTRACTED ≠ CANONICAL VERIFIED**：

```text
RAW_EXTRACTED
  → STRUCTURALLY_VALIDATED   （schema 跨样本一致）
  → SEMANTICALLY_MAPPED      （token ↔ 语义类别）
  → RECONCILED_WITH_PUBLIC/OBSERVED
  → CANONICAL_CANDIDATE
```

只有最后一步才触碰 canonical v0.1/v0.2。**automatic canonical overwrite 永远 FORBIDDEN**。

---

## G. Copyright Boundary

extractor 本地可见剧情文本，但**默认输出不得保存完整对白**：

| 项 | 允许 |
| --- | --- |
| short_identity_token | ✅ |
| text_id | ✅ |
| string hash | ✅ |
| short locator | ✅ |
| full dialogue | ❌ |
| full script reconstruction | ❌ |
| bulk content export | ❌ |

---

## H. Version Drift

必须能发现（而非静默把旧 parser 跑在新数据上）：

```text
game version changed
archive SHA changed
entry layout changed（version / entry_size / 结构）
LuaT format changed
```

策略：`unknown version → fail closed`；provenance 记录解析时的版本。

---

## I. Test Strategy

**不用大量游戏数据做 fixture。**

建立小型 synthetic / redacted fixtures：

```text
fake MPKINFO v3        自造 8B + N×20B + 16B
fake archive block     自造 LuaT-like + LZMA + raw
fake LuaT minimal      自造含已知常量的最小容器
fake narrative constants  dq_/EXPANSION_/TextByNo 等
```

真实游戏数据只作本地 integration evidence，**不进 Git**。

---

## J. Rejected Alternatives（明确拒绝）

```text
full MPK unpacker
runtime hook
memory inspection
anti-cheat interaction
generic Lua decompiler
bulk dialogue export
automatic canonical overwrite
```

---

## 下一阶段任务序列

```text
NEX-001 Contract / Architecture        GO（本稿）
NEX-002 LuaT Dialect Identification    WAITING
NEX-003 Minimal Constant/Proto Reader  WAITING
NEX-004 Narrative Record Normalizer    WAITING
NEX-005 Qinghe Pilot Extraction        WAITING
NEX-006 Mac Evidence Reconciliation    WAITING
NEX-007 Canonical Promotion Decision   WAITING
```

**NEX-002 是最大技术 unknown**：只回答「Lua 5.x? / LuaJIT? / modified Lua? / custom container around standard bytecode?」以及「能否在不完整反编译下可靠读 constant/proto metadata？」——不放大成大型逆向。
