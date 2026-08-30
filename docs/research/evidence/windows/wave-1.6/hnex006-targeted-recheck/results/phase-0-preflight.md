```text
Task-ID: WIN-HNEX006-PHASE0
Status: REVIEW_REQUIRED
Result: BASELINE_DRIFT
Branch / Commit: research/hnex006-win-targeted @ db9413428189e1a32b11af6547facb8d8e4dc0f7
Game Version: observed 20260820220319 (patching_version.txt); frozen/expected 20260829165912
Input Hashes: packet 8c1e4b5ae6d05ef52ccdc3cb6412bb50007e1532f1bfe2aad174d3c7100ef9a7 (PASS);
  manifest 4d5a1397786be70c71b5ba81ea2282bfe4cf246d24ed3e01adc00ff3c5c80f9c (PASS);
  canonical blob 4b1919f0b8d86ffac66b77d0e2f02c9e1a824e02ecd9a87e170889c134ece1ec (PASS via git-show, 工作区副本为 autocrlf CRLF)
Target Claim: Phase 0 baseline gate（全部 7 job 的硬前置）
Search Universe: E:\yysls\yysls_fast\LocalData\Patch（LT31/LT51/LT71 + .mpkinfo 存在；另见 LT101 同批重写）
Commands / Tool Commit: discovery_engine.py --selftest (exit 0); qinghe_packet_builder.py --selftest (exit 0);
  verify_hnex006.py (49/50 PASS，唯一 FAIL 为 canonical 工作区 CRLF，已用只读 blob 比对替代);
  qinghe_packet_builder.py replay (exit 1)
Normalization / Aliases: N/A
Hit Count: N/A
Owned Records: N/A（gate 阶段不做语义检索）
Typed Edges: N/A
Archive / Entry / Observation Offset: replay 首条拒绝点 LT71[1248]（frozen record game_version 与当前不符）
Block SHA-256: 当前 LT31 b404de7775a7e18876bbc4da732ee997509b09eb26f4fe4affee961ba1abea87;
  LT51 808a7d85b0160e1bf7691af7869db09ad37e13213e1838aa03b4765b15301870;
  LT71 74b0db1a3ca320fe03ef4ad5414b6e3d916c405f416ac274a018a26c988b3426
Evidence Type: baseline gate / provenance check
Bounded Evidence Summary: 版本文件 20260820220319 ≠ 冻结 20260829165912；
  LT71.mpk mtime 2026-08-29 20:55 晚于冻结时刻；
  replay 被 fail-closed builder 以 stale record 拒绝（exit 1，未产出产物）。
Negative Branches: 未进入任何检索分支；旧 12 entries / 7 clusters locator 全部冻结失效。
Success-or-Failure Criterion Met: 交接包 §3 drift 条款满足（版本或任何
  archive/entry/block hash 变化 → REVIEW_REQUIRED / BASELINE_DRIFT，停止旧 locator 任务）。
Limitations: 未判定版本字符串过旧的根因（启动器修补未更新版本文件，或修补包
  内嵌版本声明回退）；不影响判定本身。
Manual Fallback Decision: N/A（gate 失败，未进入任何静态任务）
Changed Files: docs/research/evidence/windows/wave-1.6/hnex006-targeted-recheck/{README.md, run-manifest.md, results/phase-0-preflight.md};
  另：5 个 Mac 输入 md 恢复为冻结字节（autocrlf 检出修复，非内容变更）
Next: 停止七个 job；由 Mac Lead 按 §3 决定重建路径（新快照重跑
  discovery → nex004b/004c records → NEX-005 packet → Mac 复审），再重启。
```
