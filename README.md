# 燕云十六声剧情关系图谱

面向《燕云十六声》玩家的非官方剧情理解工具，通过角色关系图、时间线与分级防剧透帮助玩家梳理复杂叙事。

## 技术栈

- Web：Next.js 16、TypeScript、Tailwind CSS 4、React Flow
- API：FastAPI、SQLAlchemy 2、Alembic、PostgreSQL 17
- 工具：npm workspaces、uv、Vitest、Playwright、pytest、Ruff、mypy

## 本地启动

1. 使用 Node.js 24，并确认 PostgreSQL 17 已启动。
2. 创建数据库：`createdb yysls_map`
3. 复制 `.env.example` 为 `.env`，设置管理员密码哈希和会话密钥。
4. 安装依赖：`npm install` 与 `cd apps/api && uv sync`
5. 执行迁移：`cd apps/api && uv run alembic upgrade head`
6. 可选导入演示数据：`cd apps/api && uv run python -m app.seed`
7. 分别运行 `npm run dev:api` 和 `npm run dev:web`

## 验证

```bash
npm run verify
npm run test:e2e
```

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
