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
| T07 | Boundary tests/docs | Codex | Complete | `codex/mvp-platform` | MVP | 21 API + 28 web tests, production build passed | PostgreSQL lifecycle test, idempotent seed and OpenAPI client verified |
| T08 | Playwright/a11y | Codex | Complete | `codex/mvp-platform` | MVP | Desktop and Pixel 7 flows passed | CORS origin, SameSite cookie host and rerun isolation fixed |
| T09 | Full content management | MiMo + Codex | Complete | `mimo/T09-admin-forms` | B6 | CRUD component tests, real DB lifecycle and E2E passed | MiMo draft rejected for schema mismatch and size; two retry calls failed at local model socket, implementation completed and reviewed by Codex |
| B5 | MVP hardening | Codex | Complete | `codex/mvp-platform` | T07, T08 | `npm run verify`, migration downgrade/upgrade and smoke tests passed | Deployment credentials intentionally not used locally |
| B6 | Search, path and content management | Codex | Complete | `codex/mvp-platform` | B3 | Search/path UI plus five-resource admin CRUD passed | Archive-only deletion and published-content filters reviewed for leakage |
| B7 | AI extraction boundary | Codex | Complete, disabled | `codex/mvp-platform` | B4 | API and disabled-UI tests passed | Editable candidate review only; never publishes or invents sources |
