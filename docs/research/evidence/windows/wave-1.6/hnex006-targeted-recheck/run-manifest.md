# H-NEX-006-WIN run manifest

```text
Task-ID: H-NEX-006-WIN
Status: REVIEW_REQUIRED
Gate Result: BASELINE_DRIFT
Branch / Commit: research/hnex006-win-targeted @ db9413428189e1a32b11af6547facb8d8e4dc0f7
Run Date: 2026-08-30T10:10+08:00 .. 10:40+08:00 (local)
Game Install Root: E:\yysls (archive dir E:\yysls\yysls_fast\LocalData\Patch)
Expected Snapshot: 20260829165912
Observed Snapshot: 20260820220319 (patching_version.txt) + post-freeze archive rewrite
Jobs: 0 total started / 7 halted before start (old locators invalidated by drift)
Fallback Requests: NONE
Canonical Diff: EMPTY (Windows 未触碰 content/、schemas/、apps/、packages/、public/)
Next: Mac Lead 复审新快照 → 按 frozen engine + policy 重建 records/packet → 重启七个 job
```

## Phase 0 gate 结果

| gate check | expected | observed | result |
| --- | --- | --- | --- |
| `verify_hnex006.py`（50 项） | exit 0 | 49 PASS / 1 FAIL，失败项为 `canonical SHA-256 is frozen`，根因是本机 `core.autocrlf=true` 将 LF blob 以 CRLF 检出到工作区（非内容漂移；HEAD blob 哈希 = 冻结值 `4b1919f0…`，与 MAC/BASE blob 逐字节相同）；`content/` 受边界保护未写回，以只读方式比对 | PASS-with-note |
| `discovery_engine.py --selftest` | exit 0 | exit 0 | PASS |
| `qinghe_packet_builder.py --selftest` | exit 0 | exit 0 | PASS |
| packet SHA-256 | `8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7` | 相同 | PASS |
| manifest SHA-256 | `4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c` | 相同 | PASS |
| `patching_version.txt` | `20260829165912` | `20260820220319`（路径 `E:\yysls\yysls_fast\LocalData\Patch\patching_version.txt`） | **FAIL** |
| LT31/LT51/LT71 + `.mpkinfo` 存在 | yes | yes（见下表） | PASS |
| baseline replay | 两份 hash 与 §1 一致 | builder 拒绝：`LT71[1248] game_version '20260829165912' != current '20260820220319' (stale record; regenerate)` | **FAIL** |

## Drift 证据（三重独立信号）

1. 版本文件：`patching_version.txt == 20260820220319` ≠ 冻结 `20260829165912`。
2. 文件系统时间：`LT71.mpk`/`LT71.mpkinfo`/`LT101.mpk`/`LT101.mpkinfo` mtime
   `2026-08-29 20:55`，`CanCompactSize.tag` mtime `2026-08-30 01:14` —— 冻结快照
   （2026-08-29 16:59:12 建立）之后，启动器对安装目录做了增量修补。
3. Replay gate：frozen records 携带 `game_version=20260829165912`，fail-closed
   builder 在第一条记录（`LT71[1248]`）即拒绝，replay exit 1，未产出任何
   replay packet。

当前归档哈希（供与旧记录比对）：

```text
LT31.mpk sha256 b404de7775a7e18876bbc4da732ee997509b09eb26f4fe4affee961ba1abea87  (mtime 2026-08-28 23:05)
LT51.mpk sha256 808a7d85b0160e1bf7691af7869db09ad37e13213e1838aa03b4765b15301870  (mtime 2026-08-28 23:05)
LT71.mpk sha256 74b0db1a3ca320fe03ef4ad5414b6e3d916c405f416ac274a018a26c988b3426  (mtime 2026-08-29 20:55, 11045539 bytes)
```

注意：`patching_version.txt` 的字符串（08-20 版本）比冻结快照（08-29 版本）更旧，
而 `LT71` 却在 08-29 晚被重写。可能原因：启动器修补流程未更新版本字符串，或
修补包内嵌的版本声明与文件名时间戳不同步。无论哪种，`current != frozen`，
按交接包 §3 一律判 `BASELINE_DRIFT`，不作内容层推断。

## 环境说明（已解释的工作区差异）

- 本机 `core.autocrlf=true`：5 个 Mac 输入文件（`source-ledger.md`、
  `main-story-inventory.md`、`unresolved-questions.md`、`character-aliases.md`、
  `interpretation/part-1-you-jian-xin-lai-yan.md`）被检出为 CRLF，与冻结字节
  不符。已用 `git cat-file blob HEAD:<path>` 恢复为与冻结输入逐字节一致的 LF
  版本（内容无变化，`git diff` 规范化后为空）。此为本机检出行为，非内容漂移。
- `content/yysls-qinghe-canonical-v0.1.json` 同样被 autocrlf 检出为 CRLF；
  因 `content/` 在 Windows 禁写边界内，未写回，改用只读 `git show` 比对 blob
  字节，确认与冻结哈希一致。

## 停止的任务

`WIN-HNEX006-P0-1..P0-4`、`WIN-HNEX006-P1-1..P1-3` 全部未执行。旧
`qinghe-evidence-packet.json` 的 12 entries / 7 clusters locator 在新基线确认前
一律不得引用为当前证据。
