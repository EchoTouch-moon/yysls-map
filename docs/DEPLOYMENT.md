# Deployment Runbook

Platform references:
[Vercel monorepos](https://vercel.com/docs/monorepos/) and
[Railway config as code](https://docs.railway.com/reference/config-as-code).

## Required environment

### API / Railway

- `APP_ENV=production`
- `DATABASE_URL`
- `WEB_ORIGIN=https://<web-domain>`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD_HASH`
- `SESSION_SECRET` (at least 32 random characters)
- Optional `LLM_*` values; keep `LLM_ENABLED=false` until reviewed

Generate an Argon2 password hash locally:

```bash
cd apps/api
uv run python -c 'from argon2 import PasswordHasher; print(PasswordHasher().hash("replace-me"))'
```

### Web / Vercel

- `NEXT_PUBLIC_API_URL=https://<api-domain>/api/v1`
- Set the Vercel project Root Directory to `apps/web`.

## Release

1. Create a PostgreSQL backup.
2. Build and test the exact revision in CI.
3. Deploy the API; Railway runs `alembic upgrade head` as its pre-deploy command.
4. Verify `/api/v1/health`, then deploy the web app.
5. Run the Playwright core flow against production with a disposable submission.
6. Confirm `LLM_ENABLED=false` unless the extraction review workflow is ready.

## Backup and restore drill

```bash
pg_dump --format=custom --no-owner "$DATABASE_URL" > yysls-map.dump
createdb yysls_map_restore_test
pg_restore --clean --if-exists --no-owner \
  --dbname yysls_map_restore_test yysls-map.dump
```

Run migrations and a read-only smoke test against the restored database before
declaring the backup valid. Never load demo seed data into production.
