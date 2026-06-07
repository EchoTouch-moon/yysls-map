"""add search indexes

Revision ID: 92ae3cf8be0a
Revises: 51ed672e0612
Create Date: 2026-06-07 19:05:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "92ae3cf8be0a"
down_revision: str | None = "51ed672e0612"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX ix_characters_name_trgm "
        "ON characters USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_factions_name_trgm "
        "ON factions USING gin (name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_story_events_title_trgm "
        "ON story_events USING gin (title gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_story_events_title_trgm")
    op.execute("DROP INDEX IF EXISTS ix_factions_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_characters_name_trgm")

