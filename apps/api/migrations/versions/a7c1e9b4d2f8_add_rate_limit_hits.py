"""add rate limit hits

Revision ID: a7c1e9b4d2f8
Revises: 6f4a2c9d8e31
Create Date: 2026-08-21 10:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c1e9b4d2f8"
down_revision: str | None = "6f4a2c9d8e31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "rate_limit_hits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("bucket_key", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rate_limit_hits")),
    )
    op.create_index(
        "ix_rate_limit_hits_bucket_key_created_at",
        "rate_limit_hits",
        ["bucket_key", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_rate_limit_hits_bucket_key_created_at", table_name="rate_limit_hits")
    op.drop_table("rate_limit_hits")
