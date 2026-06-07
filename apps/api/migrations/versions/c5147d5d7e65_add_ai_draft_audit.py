"""add AI draft audit

Revision ID: c5147d5d7e65
Revises: 92ae3cf8be0a
Create Date: 2026-06-07 19:12:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5147d5d7e65"
down_revision: str | None = "92ae3cf8be0a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_draft_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "duration_ms >= 0",
            name=op.f("ck_ai_draft_runs_duration_nonnegative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_draft_runs")),
    )
    op.create_index(
        op.f("ix_ai_draft_runs_input_hash"),
        "ai_draft_runs",
        ["input_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_draft_runs_input_hash"), table_name="ai_draft_runs")
    op.drop_table("ai_draft_runs")

