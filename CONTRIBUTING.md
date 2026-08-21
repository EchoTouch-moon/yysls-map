# 贡献指南

感谢关注本项目！这是一个玩家社区的剧情理解工具，欢迎两类贡献：
**代码** 与 **剧情内容**。

## 本地开发

环境搭建见 [README](README.md)。最低要求：Node.js 24、Python 3.13、
PostgreSQL 17（可用 `npm run dev:db` 启动）。

提交前请确保：

```bash
npm run verify        # lint + typecheck + 单测 + 生产构建
npm run test:api:db   # 完整 API 测试（含 PostgreSQL 用例与覆盖率门禁）
npm run test:e2e      # Playwright 端到端
```

## 提交规范

- Conventional Commits：`feat|fix|docs|refactor|test|chore(scope): 摘要`
- 数据相关 scope 用 `data`，工作流用 `workflow`

## 剧情内容贡献

### 方式一：站内投稿（推荐）

使用站点内的投稿入口提交线索，经人工审核后入库。这是面向所有玩家的
低门槛通道。

### 方式二：直接修改数据集（PR）

适合熟悉 JSON 结构的贡献者。请遵守：

1. **内容边界**：只收录原创撰写的摘要、关系分析与事实索引；
   不收录游戏原文文本、对话、语音或拆包数据。
2. **置信度规则**：明确剧情事实 ≥0.9；可信整理 ≥0.7；待考解读 <0.7。
3. **来源要求**：每条结论至少一个可定位来源；高风险结论（剧透 2/3）
   不应只依赖单一社区转述。
4. **历史卡红线**：新增历史断言必须有独立史料来源、事实标签与边界说明，
   且不得反向充当游戏剧情的证据。
5. **重新冻结**：数据集任何改动后必须重跑
   `python3 scripts/generate_signoff_checklist.py`
   更新签字清单与 `content/release-manifest.json`（SHA-256 会变化）。

## 许可

提交即表示同意你的贡献以项目现行许可发布：代码 MIT，
`content/` 数据集 CC BY-NC-SA 4.0（见 [NOTICE.md](NOTICE.md)）。
