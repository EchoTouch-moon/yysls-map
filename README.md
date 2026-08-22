# 燕云十六声剧情关系图谱

面向《燕云十六声》玩家的非官方剧情理解工具，通过角色关系图、时间线与分级防剧透帮助玩家梳理复杂叙事。

> **非官方声明**：本项目与网易/Everstone Studio 无任何隶属或背书关系。
> 游戏相关名称与内容的权利归其权利方所有；详见 [NOTICE.md](NOTICE.md)。
>
> **许可**：源代码 [MIT](LICENSE)；`content/` 剧情数据集
> [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)。

## 当前方向：Wave 1.6

Wave 1.5 已完成清河 canonical story alignment 与 canonical-first continuous Timeline。当前进入 **Wave 1.6 — Narrative Depth & Native Presentation**：不再横向扩功能，而是优先补足剧情研究深度、游戏原生明潮/暗涌结构、人物 point-of-need recall、玩家社区称谓与燕云式信息设计。

当前原则：

- 游戏原生 canonical structure 决定主阅读顺序，编辑解析不得创造第二套权威剧情顺序；
- 先把“第一章·神仙不渡 / 又见新来燕”做成深度样板，再扩整章；
- Mac 负责公共资料、证据 reconciliation、内容深挖、模型与产品实现；Windows 负责游戏内任务/明潮/暗涌观察和本地资源 metadata feasibility；
- Windows raw evidence 与 Mac reviewed conclusion 分离，未经 review 不修改 frozen canonical dataset；
- 本地资源研究先做只读 feasibility，不绕过加密、DRM、反作弊或访问控制；
- Canvas、开封扩张、AI chat、账号/收藏与大规模解包继续 DEFER。

详细方向见 [`docs/WAVE_1_6_NARRATIVE_DIRECTION.md`](docs/WAVE_1_6_NARRATIVE_DIRECTION.md)，双机任务分发与 Task-ID 见 [`docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md`](docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md)，总执行台账见 [`docs/execution/TASKS.md`](docs/execution/TASKS.md)。

## 技术栈

- Web：Next.js 16、TypeScript、Tailwind CSS 4、React Flow
- API：FastAPI、SQLAlchemy 2、Alembic、PostgreSQL 17
- 工具：npm workspaces、uv、Vitest、Playwright、pytest、Ruff、mypy

## 本地启动

1. 使用 Node.js 24，并确认 PostgreSQL 17 已启动（可用 `npm run dev:db` 通过
   Docker Compose 启动，首次启动会同时创建 `yysls_map` 与 `yysls_map_test`）。
2. 创建数据库：`createdb yysls_map`（使用 Docker Compose 时可跳过）
3. 复制 `.env.example` 为 `.env`，设置管理员密码哈希和会话密钥。
4. 安装依赖：`npm install` 与 `cd apps/api && uv sync`
5. 执行迁移：`cd apps/api && uv run alembic upgrade head`
6. 可选导入演示数据：`cd apps/api && uv run python -m app.seed`
7. 分别运行 `npm run dev:api` 和 `npm run dev:web`

## 内容导入

清河数据导入默认采用非破坏性更新。先验证，再在数据库事务中演练：

```bash
npm run import:content:validate --workspace @yysls/api
npm run import:content:dry-run --workspace @yysls/api
npm run import:content --workspace @yysls/api
```

全量替换会删除已有图谱内容，只能通过
`npm run import:content:replace --workspace @yysls/api` 显式执行。该命令要求
数据集 ID 二次确认，并为成功提交保存导入摘要与文件哈希。

默认导入是非破坏性的 upsert：会同步传入事件的历史关联和传入故事卷的节点，
但不会因为新版文件缺少某个顶层故事卷、历史卡或历史参考就自动删除它。整卷撤稿或
完整数据集替换必须使用上述带二次确认的 replace 命令。

## 验证

```bash
npm run verify
npm run test:api:db
npm run test:e2e
```

`npm run verify` 默认跳过依赖 PostgreSQL 的 API 测试；`npm run test:api:db`
通过 Docker Compose 数据库运行完整 API 测试套件，与 CI 一致。

生产发布与备份恢复步骤见 `docs/DEPLOYMENT.md`。演示数据均带有
`[DEMO FICTION]` 标记，不得直接用于生产内容。

## 内容边界

本站只收录原创剧情摘要、关系分析和必要的事实索引，不建设完整任务文本、对话、书信、语音、视频或拆包数据库。

## 内容整理原则

本站允许收录玩家亲历、社区整理和剧情推断，不要求每条内容都具备官方或多站交叉证据，但必须保留资料性质：

- 明确剧情事实：`confidence >= 0.9`
- 可信玩家整理或多方线索：`confidence >= 0.7`
- 尚待验证的剧情解读：`confidence < 0.7`
- 玩家亲历可使用 `player_note` 来源，记录任务名、场景、角色和记忆中的关键线索
- 已确认事实写入摘要，个人理解写入角色 `interpretation`、事件 `impact` 或低置信关系

可信度表示资料确定程度，不表示内容是否值得收录。目标是在明确区分事实与解读的前提下，尽可能完整地还原玩家经历的剧情。

## 编辑发布（阶段 B）

```bash
python3 scripts/generate_signoff_checklist.py
```

生成逐条签字清单（`docs/editorial-signoff-qinghe.md`）与发布清单
（`content/release-manifest.json`，含数据集 SHA-256 与实体计数）。
数据集任何改动后必须重新生成两者；全部条目签字通过前不进入发布流程。
真实玩家验证使用 `docs/player-validation-worksheet.md`。
