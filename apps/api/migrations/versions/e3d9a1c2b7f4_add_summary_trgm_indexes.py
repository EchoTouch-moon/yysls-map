"""add summary trigram indexes

Revision ID: e3d9a1c2b7f4
Revises: 8c3240e690af
Create Date: 2026-08-18 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e3d9a1c2b7f4"
down_revision: str | None = "8c3240e690af"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_characters_summary_trgm "
        "ON characters USING gin (summary gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_factions_summary_trgm "
        "ON factions USING gin (summary gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_story_events_summary_trgm "
        "ON story_events USING gin (summary gin_trgm_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_story_events_summary_trgm")
    op.execute("DROP INDEX IF EXISTS ix_factions_summary_trgm")
    op.execute("DROP INDEX IF EXISTS ix_characters_summary_trgm")
