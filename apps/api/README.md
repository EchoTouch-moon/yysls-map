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
