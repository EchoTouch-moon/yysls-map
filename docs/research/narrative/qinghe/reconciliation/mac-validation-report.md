# H-NEX-006 — Mac validation report

> Task-ID: H-NEX-006-MAC
> Owner: Mac / Lead
> Status: **DONE — MAC_SCOPE_EXHAUSTED**
> Audit date: 2026-08-30
> Input reconciliation: NEX-006 @ `e98f8d08f38dab52a2d1f4852e12a68f27945fd2`
> H-NEX-006 content freeze: `8d81422bb4bfcd0655d243ed2e1c66c36fdaaad9`

## 1. 结论

Mac 能完成的验证已经全部执行。结果证明 NEX-006 的仓库 identity、Mac 输入、canonical
映射、Windows packet locator、公开来源 claim 与 lineage 限制均可复现；没有发现可由 Mac
单独关闭的 native-owned claim。因此 10 条 reconciliation status 保持：

```text
SUPPORTED             0
PARTIALLY_SUPPORTED   5
CONFLICT              1
UNRESOLVED            4
```

本轮不修改 canonical，不将公开攻略、repo v5、source path、token 或 cluster proximity
提升为游戏内 ownership 证据。剩余验证全部进入
[Windows handoff](../../../../execution/H-NEX-006_WINDOWS_HANDOFF.md)。

## 2. Mac 可验证边界

Mac 本轮负责：

1. Git/ref/file identity 与 SHA-256；
2. canonical key/title/parent/order 的冻结映射；
3. packet cluster/entry/observation locator 的存在性与 provenance；
4. claim/status/follow-up schema 的内部一致性；
5. 公开页面是否可达、关键 claim 是否真实出现、镜像是否同 lineage；
6. repo v5 只能作为项目内既有整理，不作为 native corroboration。

Mac 不能负责：

- 游戏安装目录中的 localization/task/character owning record；
- typed parent/order/prerequisite/collection edge；
- 当前游戏版本 UI 的精确显示；
- BOSS 身份等式、说话人、动机与剧情上下文；
- 任何需要 Windows 本地 archive 或最小人工任务簿/过场采集的结论。

## 3. Deterministic repository verification

执行：

```text
python3 tools/research/verify_hnex006.py
```

结果：**50/50 PASS**。验证器位于
[verify_hnex006.py](../../../../../tools/research/verify_hnex006.py)，覆盖：

- base `3c99afe` 是当前分支祖先；canonical/schema/product/asset surface 相对 base 零差异；
- 7 份 Mac 输入共 532 行，5 份正文逐字节一致，hidden inventory 仅去 trailing spaces，
  Mac README 只做 additive reconciliation 索引；
- 7 份 Mac input SHA、packet SHA、manifest SHA、canonical SHA 全部匹配；
- 47/47 tracked JSON 可解析，NEX-006 新增 33 个本地 Markdown 链接有效；
- 6 个篇一 canonical keys 的 title/parent/order 全匹配；
- 10 个 claim ID 唯一，状态分布正确；
- 7/7 clusters、12/12 entries、18/18 representative observations 可解析；
- 21 个 native target terms 在冻结 packet 中均为 `NOT_FOUND`；
- 7/7 Windows follow-up tasks 均包含 target、required evidence、candidate surface、
  static procedure、success/failure criterion 与 manual fallback。

冻结 identity：

| input | verified identity |
| --- | --- |
| canonical v0.1 | `4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec` |
| Windows packet | `8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7` |
| Windows manifest | `4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c` |
| packet builder | `6c47256be6f42b33826341bf217469be03d4c7ab` |
| extractor | `204c97f0d1a6039860f49a9c4b9232c51ae8d8fa` |
| game snapshot | `20260829165912` |

## 4. Public-source replay

方法：2026-08-30 按 [source ledger](../source-ledger.md) 在 Mac 使用正文抽取器读取页面；
不保存/提交页面正文、图片或视频，只记录 locator、派生比较与能力边界。Bilibili 视频使用
公开 view metadata API 复核 BVID/title；没有
下载视频。补充 opus 页面仍受站点限制，和原 source ledger 的“内容待人工/其他通道核阅”一致。

| source | Mac replay result | 可证明 | 仍不能证明 |
| --- | --- | --- | --- |
| `SRC-YYSLCN-NARRATIVE-INTERVIEW` | `REPRODUCED` | 官方页面含清河主线“神秘的江湖人”、暗线与“清风驿之变”锚点 | 天涯客等同该人物；明暗收集机制字段 |
| `SRC-ALI213-FULL-STORY` | `REPRODUCED` | 「又见新来燕」与篇一 1–19 步骤可读取 | 游戏内任务簿 title/hierarchy |
| `SRC-SOHU-MAIN-STORY` | `REPRODUCED` | 红线过桥、断桥、轻功、天涯客等流程可读取 | native task ownership/order field |
| `SRC-9GAME-YJXL` | `REPRODUCED / SAME_LINEAGE` | 1–19 步骤与 ali213 逐条完全一致；页面明确标注来源为游侠网（app） | 独立 corroboration |
| `SRC-9GAME-NAME-VARIANT` | `REPRODUCED / CONFLICT` | 两个页面分别使用「又见新来燕」与「又见新燕来」 | 哪一式是当前 native title |
| `SRC-BILIBILI-MAIN-PARTS` / `BV1ZL6fYMEer` | `METADATA_REPRODUCED` | 视频 title 标明篇一「又见新来燕」并使用「冯继升」 | 任务簿字符串；视频内容未作为 native capture |
| `SRC-ALI213-XUNXIN` | `REPRODUCED / SINGLE_SOURCE` | 页面明确提出寻心=寒姨及江叔关系 claim | 游戏内 character-ID / BOSS owned link |
| `SRC-3DM-MINGAN-STORY` | `REPRODUCED / MIRROR_ORIGIN` | 页面标注小黑盒、Asterismkings，并包含明潮/暗涌机制和清河暗线分组 claim | 官方/native collection graph |
| `SRC-CHINA-MINGAN-STORY` | `REPRODUCED / MIRROR` | 关键机制段与 3DM 页面逐字一致 | 第二个独立来源 |
| `SRC-ALI213-WANSIZHI-ANCHONG` | `REPRODUCED` | 「怒潮暗涌」进入万事知攻略标题 | “暗涌”机制 membership 或 category ownership |

派生 lineage 复核：

- ali213 与 9game 的 19 条 numbered steps 完全相同，规范化步骤 SHA-256 均为
  `5827620a9a49f1187de014e1ed29599c792fc7f5ca810ad1b73d3c792aea1e2b`；
- 3DM 与中华网的关键机制段逐字相同，派生段落 SHA-256 为
  `8ff2b5ccc94b739e130657ef8fb6eecff4b660e783227e4f713fc675d86376e9`；
- Bilibili opus `1023239554148073477` 无法由正文抽取器读取，保持 `CANNOT_EXTRACT`，
  不把页面存在性当内容证据。

## 5. Claim-by-claim Mac disposition

| claim | Mac result | Mac 已验证 | Windows 仍需验证 |
| --- | --- | --- | --- |
| `NEX006-P1-001` | `MAC_PUBLIC_REPRODUCED` | canonical mapping、公开步骤、v5 event locator | native title/ID/parent 与角色引用 |
| `NEX006-P1-002` | `MAC_PUBLIC_REPRODUCED` | canonical mapping、公开断桥流程 | native task/order；隐藏设计若存在需显式 metadata |
| `NEX006-P1-003` | `MAC_SOURCE_CONFLICT_REPRODUCED` | 「冯继升/冯继生」两式均真实存在 | native display name + character/task owner |
| `NEX006-P1-004` | `MAC_CANDIDATE_REPRODUCED` | 天涯客流程与官方“江湖人”锚点各自存在 | 两者 identity relation 与 task owner |
| `NEX006-P1-005` | `MAC_PUBLIC_REPRODUCED` | canonical mapping、19-step 流程与同 lineage 镜像 | native task/title/order 与角色引用 |
| `NEX006-UQ-002` | `MAC_CONFLICT_REPRODUCED` | 标题两式的公开页面冲突 | 当前版本 owned localization/task title |
| `NEX006-UQ-019` | `MAC_SINGLE_SOURCE_REPRODUCED` | 攻略 claim 与 repo v5 alias 弱自洽 | 寻心 ↔ 寒姨/寒香寻 typed identity |
| `NEX006-UQ-020` | `MAC_COMMUNITY_USAGE_REPRODUCED` | 少东家/寒姨/江叔的公开与 repo 使用 | 每个称谓的官方 in-game owned occurrence |
| `NEX006-UQ-021-A` | `MAC_MIRROR_LIMIT_REPRODUCED` | 双线官方锚点、单 origin 机制 claim | collection identity/membership/prerequisite/final target |
| `NEX006-UQ-021-B` | `MAC_MIRROR_LIMIT_REPRODUCED` | 社区分组 claim、清风驿官方 anchor | 三组各自的 dark-story typed membership |

## 6. Gate 与 next

> **MAC_SCOPE_EXHAUSTED / WINDOWS_NATIVE_EVIDENCE_REQUIRED**

- Mac 没有遗漏可由当前 repo、公开页面或冻结 packet 独立完成的验证；
- 上述 replay 不改变 [evidence map](qinghe-part1-evidence-map.md) 的四态结论；
- Windows 必须先做 archive baseline drift preflight，再按依赖图执行 7 个定向任务；
- Windows 回传后由 Mac 重新 reconciliation；在此之前不进入 NEX-007 promotion decision。
