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
| W15-C1 | Canonical story contract | Codex / Lead | Closed | `codex/mvp-platform` | Wave 1 baseline | Contract review + thin-slice evidence | `Canonical Contract v0.1 rev2` frozen |
| W15-C2 | Canonical infrastructure | Codex / Lead | Closed | `codex/mvp-platform` | W15-C1 | migration round-trip, API tests, remote provenance | Infrastructure accepted |
| W15-C3 | Qinghe canonical v0.1 data | Codex / Lead | Closed | `codex/mvp-platform` | W15-C2 | deterministic/idempotent import + exact-HEAD remote `verify` | Dataset baseline frozen |
| W15-D | Canonical-first continuous timeline | Codex / Lead | Closed | `codex/mvp-platform` | W15-C3 | API/Web/E2E + exact-HEAD remote `verify` | H-D1 overlay parity closed; Player Validation exposed Wave 1.6 needs |
| W16-E0-MAC | Narrative research expansion — Mac track | Mac | Ready | `research/wave-1.6-mac-narrative` (suggested) | W15-D | claim/evidence ledger + reconciliation review | See `docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md` M-00..M-08 |
| W16-E0-WIN | Game evidence acquisition — Windows track | Windows | Ready | evidence-only / optional `research/windows-evidence-tooling` | W15-D | native UI/task observations + evidence ledger | See W-00..W-05; raw evidence separated from canonical conclusions |
| W16-E05 | Local asset feasibility | Windows + Mac Lead | Ready, read-only | research only | W16-E0-WIN | installation inventory, optional metadata probe | No bypass of encryption/DRM/anti-cheat; extractor not approved |
| W16-E1 | Narrative Model v0.2 proposal | Mac + Lead | Waiting | TBD | W16-E0-MAC, W16-E0-WIN, W16-E05 | proposal review; no migration yet | Must preserve frozen canonical v0.1 |
| W16-E2 | `又见新来燕` deep-dive pilot | Mac + Lead | Waiting | TBD | evidence join | six-layer narrative review | Depth before breadth; do not expand whole chapter before pilot signoff |
| W16-E3 | Reading UX v2 | Mac / Web | Waiting | TBD | W16-E1, W16-E2 | UX proposal then implementation gates | 明潮/暗涌 + inline character recall + event archive unification |
| W16-E4 | Yanyun visual alignment | Mac / Web | Waiting | TBD | W16-E3 | visual-language review + accessibility | Information design first, not cosmetic skinning |
| W16-E5 | Player Validation Round 2 | Lead | Waiting | N/A | W16-E2, W16-E3 | alignment/flow/understanding/recall/community-fit evidence | Wave 2 remains NO_GO until evidence |

## Active Wave 1.6 references

- Direction: [`docs/WAVE_1_6_NARRATIVE_DIRECTION.md`](../WAVE_1_6_NARRATIVE_DIRECTION.md)
- Dual-machine task distribution: [`docs/execution/WAVE_1_6_DUAL_MACHINE_TASKS.md`](WAVE_1_6_DUAL_MACHINE_TASKS.md)

### Current execution rule

Mac and Windows may run the first E0 tasks in parallel. Windows produces observations/evidence; Mac produces reconciliation, research conclusions, model proposals and reviewed product changes. Neither track may independently mutate the frozen canonical dataset based on unreviewed evidence.
