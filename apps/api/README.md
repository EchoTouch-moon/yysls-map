# API

FastAPI service for graph, timeline, submissions, administration, search and relationship paths.

## Demo data

The local seed is deterministic, idempotent, and explicitly fictional:

```bash
uv run python -m app.seed
```

It creates 5 chapters, 5 factions, 20 characters, 30 relationships, 10
timeline events, and 10 source records. Every public title or summary is
marked with `[DEMO FICTION]`; replace it with manually verified original
summaries before production.

## Normalized content import

The import command is non-destructive by default and validates all references
before opening a database session:

```bash
npm run import:content:validate
npm run import:content:dry-run
npm run import:content
```

Use `npm run import:content:replace` only for an intentional full graph
replacement. Successful commits are recorded in `content_import_runs`;
validation-only, dry-run, and failed imports do not leave audit rows.

The default import is a non-destructive upsert. It synchronizes child links
for events and story arcs present in the incoming dataset, but intentionally
does not delete an entire previously imported story arc, historical context,
or historical reference when that top-level item is absent. Use the explicit
confirmed replace command for a complete withdrawal or dataset replacement.
