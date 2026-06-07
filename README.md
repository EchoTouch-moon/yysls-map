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
