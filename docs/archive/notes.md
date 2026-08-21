# Notes: Project Progress Review

## 2026-08-20 Current Review Context

- 当前目标扩展为全项目梳理、发展路线分层与一轮核心改进。
- 上轮 P0/P1 已完成图谱几何与交互收尾、内容导入安全化、来源主体扩展、迁移与隔离 E2E。
- 当前工作树包含 21 个已跟踪文件的未提交改动和若干新增测试/迁移文件；这些是本轮必须保护的基线。
- 评估必须把工程能力、内容准备度和发布准备度分开，避免将功能完成误判为产品可用。
- 新方向按核心功能、增强功能、未来方向、灵感仓库分类；只有核心闭环缺口进入本轮代码。

## 2026-08-20 Audit Evidence

### Engineering baseline

- `npm run verify` passed: Web/API lint and type checks, 38 Web tests, 34 API tests, and production builds.
- Two PostgreSQL-dependent API tests were skipped in the default run; the previous P0/P1 report records a 36-test database run.
- A fresh isolated database successfully completed every migration and imported Qinghe v4: 1 chapter, 10 factions, 39 characters, 27 events, 29 relationships, 21 source definitions, and 172 subject-source links.
- The worktree remains intentionally dirty with the prior graph/import work; no existing change has been reverted.

### Product path walkthrough

- Desktop home, graph, and timeline render cleanly with the real Qinghe dataset; no page exceptions occurred.
- One browser console 404 is consistent with a missing optional browser asset and does not interrupt the flow.
- At `start`, the product exposes 2 characters, 0 relationships, and 1 event.
- At `qinghe`, it exposes 33 characters, 25 relationships, and 23 events.
- `kaifeng` is byte-for-scope equivalent to `qinghe`, while `current` is equivalent to `unrestricted` at 39 characters, 29 relationships, and 27 events.
- Therefore five UI choices currently represent only three distinct visibility states, and `current` reveals records deliberately gated beyond the completed Qinghe chapter.
- The homepage describes a player-corrected dossier, and the data layer preserves 172 evidence links, but public relationship, character, and timeline views expose no source title, type, link, or note.

### Core-loop diagnosis

The shortest value loop is:

1. Declare a **completed** story milestone.
2. Enter through a person, event, or query.
3. Follow a visible relationship or chronological consequence.
4. Distinguish explicit fact, credible synthesis, and interpretation.
5. Inspect the supporting source and continue exploration without leaking later content.

Steps 1 and 5 are currently incomplete. Misleading progress labels weaken spoiler safety; inaccessible provenance weakens trust in every summary and confidence label.

## Implementation Evidence

- Public progress choices now expose only `start`, `qinghe`, and `unrestricted`, labelled as Qinghe not completed, Qinghe completed, and no spoiler protection.
- The selector explicitly tells users to choose the previous milestone while a chapter is in progress.
- Character details, relationship details, and timeline events now return and render their linked evidence sources.
- Evidence is collapsed by default; external references are only linked for HTTP(S) URLs and carry `noopener noreferrer`.
- Public evidence intentionally omits generic source notes and internal source IDs because real start-visible records contained metadata such as “主角身世揭秘” and “序章至第五章”, which could itself cross spoiler boundaries.
- Real Qinghe walkthrough confirmed 3 source links on the first visible timeline event and 3 on the protagonist dossier, with no page exceptions.
- Web checks passed with 41 tests; the full API suite passed with 36 tests and 75% coverage against PostgreSQL.
- Isolated Playwright passed both desktop submission/moderation and mobile navigation/graph fallback scenarios.
- Production and development dependency audits identified vulnerable framework/transitive packages. Next.js and its PostCSS/Sharp/Nanoid chain, Pydantic Settings, Starlette, pytest, Redocly, js-yaml, and brace-expansion were moved to patched compatible releases without a major product dependency migration.

## Feature Classification

### Core function — act now

- Expose only release-supported progress choices and state that chapter choices mean the chapter is completed.
- Show spoiler-safe evidence summaries for visible relationships, character dossiers, and timeline events.
- Complete editorial review and source upgrades before public launch; this is operational work and must not be auto-edited in code.
- Establish a reproducible staging release and backup/restore proof; requires external infrastructure, so document but do not perform locally.

### Enhancement — candidate after first release

- Drive progress options dynamically from published chapters once a second real chapter exists.
- Add full event/faction dossiers and evidence filtering by source type.
- Add content quality dashboards for missing/weak provenance and review status.
- Improve the mobile graph into a compact relationship list after mobile usage evidence exists.

### Future direction — validate first

- Expand to Kaifeng only after the Qinghe editorial/release workflow is repeatable.
- Add saved reading state, bookmarks, or personal notes after demand and privacy expectations are known.
- Add release analytics focused on spoiler setting, successful exploration, empty searches, and source opens.

### Inspiration backlog — do not implement now

- Automatic AI publication, social feeds, recommendation systems, and real-time collaborative graph editing.
- These add moderation, copyright, privacy, and trust costs without solving the current release bottlenecks.

## Initial Repository Findings (before the P0/P1 remediation)

- Current branch: `codex/mvp-platform`, latest commit `6685995` from 2026-06-09.
- No Git remote or upstream branch is configured, so CI and deployment status cannot be confirmed.
- The execution ledger marks all 14 listed engineering batches/tasks complete.
- The repository contains a functional Next.js/FastAPI/PostgreSQL MVP:
  - spoiler-aware graph, timeline, character/faction details, search, and paths;
  - submissions, admin review, full content management, and disabled AI draft workflow;
  - migrations, CI configuration, Vercel/Railway configuration, and deployment documentation.
- Current uncommitted work is primarily graph/UI polish across 10 existing files.
- `npm run verify` currently fails:
  - two TypeScript errors in `StoryGraph.tsx` when adding `isHovered` to optional edge data;
  - two unused-import warnings and trailing whitespace in `RelationshipEdge.tsx`.
- Unit tests pass despite the typecheck failure:
  - Web: 34/34 tests passed.
  - API: 26 passed, 1 skipped because the local PostgreSQL test database is unavailable.
  - API coverage is 61%; graph route 27%, path service 20%, content import 45%.
- End-to-end tests were not run because the local Playwright setup targets the default database
  and writes a submission/moderation record.
- Real Qinghe content dataset v4 exists with 1 chapter, 10 factions, 39 characters,
  27 events, 29 relationships, and 21 sources.
- All 21 v4 sources are classified as `community_analysis`; no official references,
  quest references, or player notes are represented.
- The importer's automated tests validate only parsing and a few references. They do not test a
  full database import, rollback, replacement behavior, or idempotency.
- The standard `import:content` script always uses `--replace-existing`, which deletes all existing
  graph content before importing.
- Chapter and faction source IDs exist in the dataset contract but are not persisted because the
  current `Source` model supports only characters, events, and relationships.
- The package lock diff is platform-metadata churn and appears unrelated to the UI work.
- The current edge implementation likely misidentifies center edges: React Flow's `sourceX/sourceY`
  and `targetX/targetY` are handle coordinates, not the node's layout position `(0, 0)`.

## Synthesized Findings

### Current Stage

The engineering MVP is substantially complete. The project is now between internal MVP and a
staging-ready content release. The active UI polish branch is not yet merge-ready, and the real
content import/review process is the main product risk.

### Priority Order

1. Restore a green working tree and finish the current graph interaction changes.
2. Harden and integration-test real-content import before using it on any persistent database.
3. Perform editorial/source review and preserve provenance for every supported content type.
4. Establish remote CI, staging deployment, backup/restore, and production-like smoke testing.
5. Expand content beyond Qinghe only after the first chapter's release workflow is repeatable.

## Implementation Completion

- Graph edge geometry, hover typing, arrow placement, and default-focus fallback are complete.
- Import validation, dry-run, safe upsert, confirmed replacement, advisory locking, and audit
  records are complete.
- Chapter and faction source provenance is persisted and spoiler-gated.
- Alembic round-trip, PostgreSQL lifecycle tests, full verification, and isolated E2E passed.

## Final Verification Snapshot

- Runtime contract: Node `24.15.0`, Python `3.13.13`, PostgreSQL-backed test database.
- `npm run verify`: passed Web/API lint, strict type checks, 41/41 Web tests, 36/36 API tests with 75% coverage, Next.js 16.3.1 production build, and API client build.
- Playwright: 2/2 scenarios passed, covering desktop exploration/submission/moderation and mobile navigation/graph fallback.
- Alembic: `4d3b9f7c2a11 -> 8c3240e690af -> 4d3b9f7c2a11` round-trip passed; Qinghe v4 re-import restored 1 chapter, 10 factions, 39 characters, 27 events, 29 relationships, 21 sources, and 172 source links.
- Security: full npm audit and `pip-audit` report no known vulnerabilities; the local application package is the only expected PyPI audit skip.
- Hygiene: `git diff --check` passes. Existing user changes and `.freebuff/` were preserved; no commit or remote operation was performed. Both disposable PostgreSQL verification databases were removed after the final run and can be recreated from migrations plus the Qinghe dataset.
- Remaining non-blocking warning: FastAPI's compatibility import emits a Starlette warning that `httpx` support in `starlette.testclient` is deprecated in favor of `httpx2`; runtime and tests remain green.

## 2026-08-20 Story Guide / Historical Context Slice

### Existing capability and gap

- `/timeline` currently orders published `StoryEvent` rows by chapter and `sort_order`, filters them by progress/spoiler level, and returns summary, impact, characters and evidence.
- The UI is a safe event index, not a guided narrative: it does not identify the dramatic question, setup/turn/payoff role, causal bridge, or next question.
- Existing `summary`, `impact`, character/faction links, relationship-event links, sources and spoiler gates can be reused.
- The Qinghe dataset has 27 events; the first guide should select 8—10 key beats instead of duplicating all 27.

### Historical trust boundary

- Qinghe v4 already contains “历史人物”, “历史势力”, exact years and “历史原型” claims, while all 21 current sources are `community_analysis`.
- Historical context therefore needs independent evidence and four public labels: 作品事实、历史事实、可信对照、编辑推测.
- The visible history feature is an enhancement, but historical claim classification and source quality are a core prerequisite.
- `HistoricalContext` must remain separate from `StoryEvent`; the link needs an explicit relation kind such as setting, inspired-by, parallel, contrast or fictionalized.

### Recommended vertical slice

- One Qinghe main-story arc with 8—10 manually curated beats.
- One sample event with 2—3 independently sourced historical context cards.
- Same-page “跟着故事读 / 完整事件” modes.
- Historical cards remain collapsed/supporting material; they do not compete with the story flow.

### Historical source audit — final corrections

- The Zhongdu Bridge account belongs to Later Jin Kaiyun 3 / Liao Huitong 9 (**946**), not 945. The dataset's faction, Wang Qing profile, and `wangqing-battle` wording must use 946.
- `Zizhi Tongjian` volume 285 and `Old History of the Five Dynasties` volumes 85/95 support Wang Qing's office, his request for two thousand infantry, the bridge assault, Du Wei withholding reinforcement, Wang Qing's death, and Du Wei's subsequent surrender plan.
- The record supports the sequence “withheld reinforcement, then sought surrender”; it does not prove an earlier secret collusion or a deliberate plot to have Wang Qing killed. Any motive claim must be an editorial inference.
- Army totals conflict: `History of Liao` reports 200,000 surrendering, while `Old History of the Five Dynasties` reports 100,000. These are surrender totals, not an uncontested “200,000 defenders at the bridge”; public copy should say “a large Later Jin force” and disclose the disagreement when relevant.
- “Du Wei” and “Du Chongwei” refer to the same person; the shorter form reflects avoidance of Emperor Shi Chonggui's name. Do not model them as separate people.
- Yanbei Alliance, the protagonist's parentage, Dream Puppet poison, Jiang Yan's role, and other work-specific relations remain work facts / fictionalization, never historical facts.
- Reviewed public sources (accessed 2026-08-20): Ruzhou municipal history for the Five Dynasties sequence; Miyun district history and `History of Liao` volume 4 for Later Jin–Khitan/Yanyun context; `Zizhi Tongjian` volume 285 and `Old History of the Five Dynasties` volumes 85/95 for the Zhongdu Bridge account. Online transcriptions are public verification aids; publication should check decisive wording against an authoritative punctuated edition.
