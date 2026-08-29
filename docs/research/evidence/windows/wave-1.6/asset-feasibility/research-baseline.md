# W-R00 — Research Baseline Freeze

> Task-ID: W-R00 · Owner: Windows · Status: **DONE**
> 采集日期: 2026-08-23 03:08 +08:00
> 用途：冻结研究输入，保证后续 parser 结果可追溯到确定的游戏版本与文件。

---

## 1. 环境基线

| 项 | 值 |
| --- | --- |
| install root | `E:\yysls` |
| patching_version | `20260820220319`（`yysls_fast\LocalData\Patch\patching_version.txt`，2026-08-20 22:03:19） |
| pkgversion | `0-1783500887`（`…\Patch\pkgversion`） |
| 注册表 DisplayVersion | `1.0.0`（Publisher: Netease） |
| Windows | Windows 10 Home China 22H2 · build `10.0.22621.3593` |
| Python（本机） | `python` = 3.12.3 · `py` = 3.12.5（repo `.python-version` = 3.13，未安装） |
| 研究脚本 | `tools/research/windows-static-archive/inspect_mpkinfo.py`（仅 stdlib，3.8+ 兼容） |

---

## 2. 冻结的研究样本（已复制到 `tools/research/windows-static-archive/samples/`，gitignored）

| sample_name | size (B) | SHA-256 | mtime | 来源 |
| --- | ---: | --- | --- | --- |
| main_Resources.mpkinfo | 12,524 | `DC98DF817E390414B7FD89FDD6A0BDA764826938AB585B0E493CF8D41730468F` | 2025-01-11 10:51:42 | `E:\yysls\Resources.mpkinfo` |
| (paired) Resources.mpk | 200,632,208 | `31C309B06FD8A4FAA15B37C3B076D7215FF4B7A28C78038E291F7F2FFF532E01` | 2025-01-11 10:51:40 | `E:\yysls\Resources.mpk` |
| deploy_Resources.mpkinfo | 13,744 | `925616A47626DC9B32FAD51FCCD04D48F0CF027963DD6DA3496E066A8E7CC0D5` | 2026-07-24 21:05:28 | `E:\yysls\Win32\deploy\Resources.mpkinfo` |
| (paired) Resources.mpk | 270,179,195 | `3C8E059BC7810A6EC24286D5ECAADA9D160EBCE976587F4244BFBF5C6EE24D9F` | 2026-07-24 21:05:28 | `E:\yysls\Win32\deploy\Resources.mpk` |
| tiny_hexi_1.mpkinfo | 64 | `049A1503F0B6EC2022450C58AB672108DBD976215046C6302F5B51903EF5AE90` | 2026-08-18 21:54:08 | `…\Patch\TinyFiles_common_hexi.1.mpkinfo` |
| tiny_bjs_3.mpkinfo | 161 | `E454BBD028A5D5303DF197F6CF2A0D0F61C9450D44FFF44576787DADC3334D24` | 2026-08-18 21:52:12 | `…\Patch\TinyFiles_common_bjs.3.mpkinfo`（HEXB 变体） |
| lt261.mpkinfo | 224 | `392C6687DF02E8F05031755633B4437D5566685040F154B5A677EB521EC6BC3C` | 2026-08-18 21:54:30 | `…\Patch\LT261.mpkinfo` |
| patch1001.mpkinfo | 264 | `9E496AD6F2678617CAEEF42AD6B848FCE2B6ABB12B7316FA163C8B0500B4FB17` | 2026-08-22 23:11:28 | `…\Patch\Patch1001.mpkinfo` |
| lt312.mpkinfo | 1,524 | `13C92FD2D996EB9FC69462B4E351A23CAFD4380312A9F902BC309F1875A6BC0A` | 2026-08-22 23:10:24 | `…\Patch\LT312.mpkinfo` |
| tiny_qingzhou.mpkinfo | 2,984 | `5F85FF5AFE241D4C21181CA8125A30D97CB38DB9DB5821E143337576BC63F295` | 2026-08-18 21:55:14 | `…\Patch\TinyFiles_mid_qingzhou.mpkinfo` |

> 原安装目录 `E:\yysls` 未做任何修改；样本为只读复制。样本目录已被 `tools/research/windows-static-archive/.gitignore` 排除，不进 Git。

---

## 3. provenance 问答

> “后续 parser 结果对应哪一个确切游戏版本和哪一组确切文件？”

- 游戏版本：`patching_version=20260820220319` / `pkgversion=0-1783500887`（注册表 1.0.0）
- 文件：上表 8 个 `.mpkinfo` 样本（SHA-256 已冻结），其中 version=3 可解析样本 7 个、HEXB 混淆变体 1 个
- 任何 parser 输出可通过“样本名 + SHA-256”回溯到确切字节。

---

## 4. STOP 检查

- ✅ 未修改原安装目录
- ✅ 未读取/复制 `.mpk` 内部 payload
- ✅ 未接触密钥 / 反作弊 / 运行时状态
- ✅ 原始 `.mpkinfo` 样本不进 Git
