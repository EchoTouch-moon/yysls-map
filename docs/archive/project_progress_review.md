# Project Progress Review

## Current Position

The engineering MVP plus the P0 graph finish and P1 import hardening are complete locally.
Editorial review and staging deployment remain intentionally out of scope.

## Verification Snapshot

- Web unit tests: 38 passed.
- API tests with PostgreSQL: 36 passed, 74% total coverage.
- Content import coverage: 96%; graph route: 75%; timeline route: 96%.
- Migration upgrade/downgrade/upgrade passed with populated source data.
- Full `npm run verify` passed, including the production build.
- Playwright desktop and mobile flows passed against an isolated database.
- No Git remote/upstream is configured; CI and actual deployment status are unverified.

## Product Readiness Gaps

- Qinghe v4 has useful scope: 39 characters, 27 events, and 29 relationships.
- All 21 sources are community analysis, so higher-risk facts and hidden identities need review.
- Content review is still pending by design.
- Staging backup/restore and deployment smoke testing are still pending.
- The E2E suite still uses isolated fictional fixtures, now with configurable ports.

## Recommended Next Steps

### P1: Editorial Release Review

1. Review all low-confidence and spoiler level 2/3 records.
2. Add official/quest/player-note sources where available.
3. Define a sign-off checklist for summaries, interpretations, aliases, and hidden identities.
4. Decide which records publish now and which remain draft.

Exit condition: every published claim has an explicit confidence and review decision.

### P2: Staging and Release

1. Configure a Git remote and verify CI on the actual branch.
2. Deploy a staging API/database and Web preview.
3. Run migrations, safe content import, backup/restore drill, and Playwright against staging.
4. Replace demo-dependent E2E fixtures with isolated test data.

Exit condition: a reproducible release candidate exists with rollback instructions.

## Suggested Immediate Sprint

The next sprint can begin editorial release review, followed by staging import, backup/restore,
and deployment smoke testing. P0 and import hardening no longer block that work.
