"""add chapter content status

Revision ID: 8c3240e690af
Revises: c5147d5d7e65
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8c3240e690af"
down_revision: str | None = "c5147d5d7e65"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "chapters",
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PUBLISHED",
                "ARCHIVED",
                name="content_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PUBLISHED",
        ),
    )
    op.create_index("ix_chapters_status", "chapters", ["status"])
    op.alter_column("chapters", "status", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_chapters_status", table_name="chapters")
    op.drop_column("chapters", "status")
