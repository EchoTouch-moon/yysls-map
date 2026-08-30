# H-NEX-006 — Windows targeted native-evidence handoff

> Task-ID: H-NEX-006-WIN
> Owner: Windows Research Station
> Status: **READY**
> Depends on: NEX-006 reconciliation + H-NEX-006-MAC
> Goal: close or explicitly fail the remaining native-owned evidence checks without canonical promotion.

## 1. 交付给 Windows 的固定输入

| input | required identity |
| --- | --- |
| H-NEX-006 handoff content freeze | `8d81422bb4bfcd0655d243ed2e1c66c36fdaaad9` |
| NEX-006 reconciliation | `e98f8d08f38dab52a2d1f4852e12a68f27945fd2` |
| Mac input | `cd50bd24779fd47b808bc270a12c617cd9977be9` |
| Windows packet builder | `6c47256be6f42b33826341bf217469be03d4c7ab` |
| Windows extractor | `204c97f0d1a6039860f49a9c4b9232c51ae8d8fa` |
| packet SHA-256 | `8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7` |
| manifest SHA-256 | `4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c` |
| canonical SHA-256 | `4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec` |
| expected game snapshot | `20260829165912` |

Windows 应 checkout 一个包含 handoff content freeze 的干净 branch tip；后续 provenance-only commit
不改变本任务的 job/constraint 语义。若该 commit 不可解析，返回 `PROVENANCE_INCOMPLETE`。

Authoritative task details：

- [NEX-006 evidence map](../research/narrative/qinghe/reconciliation/qinghe-part1-evidence-map.md)
- [seven targeted checks](../research/narrative/qinghe/reconciliation/windows-followup-evidence-list.md)
- [Mac completed validation](../research/narrative/qinghe/reconciliation/mac-validation-report.md)
- [frozen packet](../research/evidence/windows/wave-1.6/nex005-qinghe-packet/out/qinghe-evidence-packet.json)

## 2. 不可突破的约束

允许：

- 本机安装目录离线、只读检查；
- 读取 `.mpkinfo` / `.mpk`，使用现有 frozen parser/normalizer/builder；
- 标准压缩格式的受限解压；
- 建立 term/ID → owned record → typed edge 的最小图；
- 返回 bounded observation、hash、archive/index/offset、owner/type 与必要短摘要；
- 静态失败且满足 fallback gate 后，采集最小任务簿/UI/过场证据。

禁止：

- 修改游戏客户端或安装文件；
- runtime memory dump、hook、注入、反作弊交互；
- 获取/破解密钥或绕过访问控制、DRM、受保护资源；
- 大规模导出或提交完整对白、脚本、图片、音频、视频、模型或其他原始资产；
- 仅凭 source path、identifier token、SHORT_CJK、byte/entry 顺序或 cluster 邻近推导语义；
- Windows 直接修改 canonical、schema、产品 UI 或 reconciliation status；
- 把普通 grep miss 写成 `NOT_FOUND`。

出现密钥、运行时解密、hook、注入、反作弊或 protected bypass 需求时，立即返回
`STOP_NO_GO`，不得扩大范围。

## 3. Phase 0 — baseline preflight（所有任务的硬前置）

在仓库根目录执行；PowerShell 变量不得复用系统 `$HOME`：

```powershell
$RepoRoot = (Get-Location).Path
$ArchiveRoot = 'E:\yysls'
$RunRoot = Join-Path $env:TEMP 'hnex006-targeted-recheck'
New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null

python tools/research/verify_hnex006.py
python tools/research/windows-static-archive/discovery_engine.py --selftest
python tools/research/windows-static-archive/qinghe_packet_builder.py --selftest

Get-FileHash docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/out/qinghe-evidence-packet.json -Algorithm SHA256
Get-FileHash docs/research/evidence/windows/wave-1.6/nex005-qinghe-packet/out/selection-manifest.json -Algorithm SHA256
Get-Content (Join-Path $ArchiveRoot 'patching_version.txt')
```

只有以下条件全部满足才继续：

1. 三个 verifier/selftest exit `0`；
2. packet/manifest hash 与 §1 完全一致；
3. `patching_version.txt == 20260829165912`；
4. LT31/LT51/LT71 archive 与 `.mpkinfo` 存在且只读；
5. worktree 没有无法解释的修改。

### Baseline replay

在 current snapshot 未漂移时，以现有 records 重建 packet 到临时目录：

```powershell
$ReplayRoot = Join-Path $RunRoot 'packet-replay'
python tools/research/windows-static-archive/qinghe_packet_builder.py `
  $ArchiveRoot `
  --records-dir docs/research/evidence/windows/wave-1.6/nex004b-structural-discovery `
  --records-dir docs/research/evidence/windows/wave-1.6/nex004c-holdout `
  --out $ReplayRoot `
  --commit 204c97f0d1a6039860f49a9c4b9232c51ae8d8fa `
  --builder-commit 6c47256be6f42b33826341bf217469be03d4c7ab

Get-FileHash (Join-Path $ReplayRoot 'qinghe-evidence-packet.json') -Algorithm SHA256
Get-FileHash (Join-Path $ReplayRoot 'selection-manifest.json') -Algorithm SHA256
```

两份 replay hash 必须与 §1 一致。若 game version 或任何 archive/entry/block hash 变化，返回：

```text
Status: REVIEW_REQUIRED
Gate Result: BASELINE_DRIFT
```

此时停止所有旧 locator 任务，先按 frozen engine + policy 重建 records/packet，由 Mac 复审新
snapshot。禁止在 drift 后继续使用旧 entry index 或旧 negative result。

## 4. 执行依赖图

```text
Phase 0 baseline PASS
  ├─ P0-1 native title arbitration ──→ P0-2 five-node structure ──→ P1-3 name/identity hardening
  ├─ P0-3 寻心 identity
  ├─ P0-4 mechanism graph ───────────→ P1-2 hidden-thread membership
  └─ P1-1 official alias occurrence
```

同一层可以并行，但不得让下游任务在上游 owner/ID 未建立时自行猜测映射。

## 5. 七个可直接执行的 job

| job | priority | target | initial search universe | success output | dependency |
| --- | --- | --- | --- | --- | --- |
| `WIN-HNEX006-P0-1` | P0 | `NEX006-UQ-002` | LT71/LT51/LT31 localization + task title；两式及 normalized/text-ID reverse lookup | owned exact title + text ID + task/part owner + version | Phase 0 |
| `WIN-HNEX006-P0-2` | P0 | `NEX006-P1-001..005` | 从 P0-1 part/task owner 枚举 typed children/sequence | 5 task IDs/titles + common parent + typed order/prerequisite | P0-1 |
| `WIN-HNEX006-P0-3` | P0 | `NEX006-UQ-019` | character/task/localization；寻心、寒姨、寒香寻及 reverse IDs | character/form/BOSS typed identity edge；或 complete negative graph | Phase 0 |
| `WIN-HNEX006-P0-4` | P0 | `NEX006-UQ-021-A` | 现有 8 end-task entries + 全量明潮/暗涌/collection catalog | identity + member category + completion predicate + final target | Phase 0 |
| `WIN-HNEX006-P1-1` | P1 | `NEX006-UQ-020` | localization/dialogue/text；少东家、寒姨、江叔分别查 | 每个 term 独立 owning occurrence/context | Phase 0 |
| `WIN-HNEX006-P1-2` | P1 | `NEX006-UQ-021-B` | P0-4 collection IDs + task/lizehao seeds + target aliases/IDs | 三组各自独立 membership edge；未命中组显式 NONE | P0-4 |
| `WIN-HNEX006-P1-3` | P1 | P1-003/004 character subclaims | P0-2 archery/wilderness task IDs + character/localization | native 冯姓名；天涯客 relation 仅 explicit edge 可关闭 | P0-2 |

每个 job 的完整 procedure、候选 entries、成功/失败与 fallback 判据，以
[seven targeted checks](../research/narrative/qinghe/reconciliation/windows-followup-evidence-list.md)
对应章节为准。若表和原章节冲突，以原章节的更严格边界为准，并回报 `SPEC_CONFLICT`。

## 6. 静态检索完成条件

每个 term/ID search 必须记录：

```text
archives_and_tables_scanned
game_version
normalization (Unicode / punctuation / aliases)
query_or_script_version
hit_count
reverse_id_lookup
owner_resolution
negative_branches
limits
```

`NOT_FOUND` 只在以下条件全部满足时允许：

1. 声明的 archive/table universe 已完整扫描；
2. 精确值、normalized 值、已知别名与 derived IDs 均执行；
3. hit 为 orphan 时已尝试 reverse owner lookup；
4. command、tool commit、game version 与 input hashes 可重放；
5. 不是权限、parser、provenance、baseline drift 或 unsupported container 导致的假阴性。

否则只允许 `CANNOT_REPRODUCE`、`PROVENANCE_INCOMPLETE` 或 `BASELINE_DRIFT`。

## 7. 输出与 Git ownership

Windows 只拥有以下新目录和必要的只读 helper：

```text
docs/research/evidence/windows/wave-1.6/hnex006-targeted-recheck/
├── README.md
├── run-manifest.md
└── results/
    ├── win-hnex006-p0-1.md
    ├── win-hnex006-p0-2.md
    ├── win-hnex006-p0-3.md
    ├── win-hnex006-p0-4.md
    ├── win-hnex006-p1-1.md
    ├── win-hnex006-p1-2.md
    └── win-hnex006-p1-3.md

tools/research/windows-static-archive/   # 仅确有必要的最小只读 helper/test
```

不得编辑：

```text
content/
schemas/
apps/
packages/
public/
docs/research/narrative/qinghe/reconciliation/qinghe-part1-evidence-map.md
docs/research/narrative/qinghe/reconciliation/mac-validation-report.md
```

原始 `.mpk/.mpkinfo`、全量 dump、raw screenshot/video 与完整游戏文本不得进入 Git。
Windows 可以本地 commit，但不得 push/开 PR/merge；由 Mac Lead 复审后处理。

## 8. 单 job 结果模板

每份 result 必须使用：

```text
Task-ID: WIN-HNEX006-Px-y
Status: DONE | REVIEW_REQUIRED | BLOCKED
Result: CONFIRMED | PARTIALLY_CONFIRMED | CONFLICT | NOT_FOUND |
        CANNOT_REPRODUCE | PROVENANCE_INCOMPLETE | BASELINE_DRIFT | STOP_NO_GO
Branch / Commit:
Game Version:
Input Hashes:
Target Claim:
Search Universe:
Commands / Tool Commit:
Normalization / Aliases:
Hit Count:
Owned Records:
Typed Edges:
Archive / Entry / Observation Offset:
Block SHA-256:
Evidence Type:
Bounded Evidence Summary:
Negative Branches:
Success-or-Failure Criterion Met:
Limitations:
Manual Fallback Decision:
Changed Files:
Next:
```

单条文字证据只保留 title/alias 或最小必要上下文；普通上下文摘要最多 160 UTF-8 bytes。
若需更长内容才能理解，保留 hash/locator，在本地由 Mac reviewer 查看，不提交原文。

## 9. Manual fallback gate

人工采集不是自动下一步。只有同时满足以下条件才允许：

1. 对应 static job 已满足 failure criterion；
2. 该 claim 阻塞 J-01/J-03 或产品精确展示；
3. result 中给出 `Manual Fallback Decision: REQUESTED`；
4. Mac Lead 回传 `MANUAL_FALLBACK_APPROVED`；
5. 采集范围严格限制在原任务列出的任务簿/UI/BOSS 名牌/最小过场。

默认策略：P0-1/P0-2/P0-3/P0-4 可申请；P1-1/P1-3 不申请；P1-2 仅逐组申请且
不得用一组成功补齐另一组。

## 10. Windows 总回报格式

七个 job 结束后统一回报：

```text
Task-ID: H-NEX-006-WIN
Status: READY_FOR_REVIEW
Branch / Commit:
Inputs:
Game Version:
Outputs:
Jobs: 7 total / confirmed / partial / conflict / not-found / incomplete
Evidence:
Unresolved:
Fallback Requests:
Risks:
Boundary Check:
Canonical Diff: MUST BE EMPTY
Next: Mac reconciliation review
```

Mac 接收后重新运行 `python3 tools/research/verify_hnex006.py`、复核每个 owner/typed edge，
再更新 reconciliation。H-NEX-006 只负责验证；NEX-007 canonical promotion decision 保持独立，
不得由 Windows result 自动触发。
