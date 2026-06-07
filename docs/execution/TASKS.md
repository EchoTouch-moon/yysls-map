# Execution Ledger

| ID | Batch | Owner | Status | Branch | Dependencies | Verification | Review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | Baseline | Codex | Complete | `codex/mvp-platform` | None | Web/API checks passed | Approved |
| B1 | Domain contract | Codex | Complete | `codex/mvp-platform` | B0 | Migration round-trip passed | Approved |
| T01 | CRUD schemas/routes/tests | MiMo + Codex | Complete | `mimo/T01-crud` | B1 | API checks passed | SQLite tests rejected; pagination and source leakage fixed by Codex |
| T02 | Web shell/design system | MiMo + Codex | Complete | `mimo/T02-web-shell` | B1 | 19 initial UI tests passed | Hydration, no-JS navigation and test cleanup fixed by Codex |
| T03 | React Flow graph UI | MiMo + Codex | Complete | `mimo/T03-graph-ui` | T02 | Main branch lint/typecheck passed | MiMo result failed 3 lint and 18 type errors; orchestration/layout/security rewritten |
| T04 | Demo seed and fixtures | MiMo + Codex | Complete | `mimo/T04-seed-data` | B1 | Definition tests passed | 1500-line/type-ignore draft rejected; replaced with typed deterministic generator |
| T05 | Timeline UI | Codex | Complete | `codex/mvp-platform` | T02 | Workflow tests passed | Progress downgrade remount prevents stale spoiler data |
| T06 | Submission/admin UI | Codex | Complete | `codex/mvp-platform` | B4 API | Workflow tests passed | HttpOnly session plus sessionStorage CSRF token |
| T07 | Boundary tests/docs | Codex | In progress | `codex/mvp-platform` | MVP | 17 API + 24 web tests passed | PostgreSQL seed run and production build blocked by local approval quota |
| T08 | Playwright/a11y | Codex | Ready, not run | `codex/mvp-platform` | MVP | Config lint/typecheck passed | Runtime requires database and local ports |
| B6 | Search and relationship path | Codex | Core complete | `codex/mvp-platform` | B3 | UI/static checks passed | Search, path and faction UI complete; full content management forms remain post-MVP |
| B7 | AI extraction boundary | Codex | Complete, disabled | `codex/mvp-platform` | B4 | API and disabled-UI tests passed | Editable candidate review only; never publishes or invents sources |
