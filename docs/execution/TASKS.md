# Execution Ledger

| ID | Batch | Owner | Status | Branch | Dependencies | Verification | Review |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | Baseline | Codex | Complete | `codex/mvp-platform` | None | Web/API checks passed | Approved |
| B1 | Domain contract | Codex | Complete | `codex/mvp-platform` | B0 | Migration round-trip passed | Approved |
| T01 | CRUD schemas/routes/tests | MiMo | Pending | `mimo/T01-crud` | B1 | Pending | Pending |
| T02 | Web shell/design system | MiMo | Pending | `mimo/T02-web-shell` | B1 | Pending | Pending |
| T03 | React Flow graph UI | MiMo | Pending | `mimo/T03-graph-ui` | T02 | Pending | Pending |
| T04 | Demo seed and fixtures | MiMo | Pending | `mimo/T04-seed-data` | B1 | Pending | Pending |
| T05 | Timeline UI | MiMo | Pending | `mimo/T05-timeline` | T02 | Pending | Pending |
| T06 | Submission/admin UI | MiMo | Pending | `mimo/T06-review-ui` | B4 API | Pending | Pending |
| T07 | Boundary tests/docs | MiMo | Pending | `mimo/T07-hardening` | MVP | Pending | Pending |
| T08 | Playwright/a11y | MiMo | Pending | `mimo/T08-e2e` | MVP | Pending | Pending |
