"""add source subjects and content import audit

Revision ID: 4d3b9f7c2a11
Revises: e3d9a1c2b7f4
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4d3b9f7c2a11"
down_revision: str | None = "e3d9a1c2b7f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("chapter_id", sa.UUID(), nullable=True))
    op.add_column("sources", sa.Column("faction_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_sources_chapter_id_chapters"),
        "sources",
        "chapters",
        ["chapter_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_sources_faction_id_factions"),
        "sources",
        "factions",
        ["faction_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_sources_chapter_id"), "sources", ["chapter_id"])
    op.create_index(op.f("ix_sources_faction_id"), "sources", ["faction_id"])
    op.drop_constraint(
        op.f("ck_sources_exactly_one_subject"),
        "sources",
        type_="check",
    )
    op.create_check_constraint(
        op.f("ck_sources_exactly_one_subject"),
        "sources",
        "num_nonnulls(chapter_id, faction_id, character_id, event_id, relationship_id) = 1",
    )

    op.create_table(
        "content_import_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("dataset_id", sa.String(length=160), nullable=False),
        sa.Column("dataset_title", sa.String(length=240), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("collected_at", sa.Date(), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=False),
        sa.Column("replaced_existing", sa.Boolean(), nullable=False),
        sa.Column("stats", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_import_runs")),
    )
    op.create_index(
        op.f("ix_content_import_runs_dataset_id"),
        "content_import_runs",
        ["dataset_id"],
    )
    op.create_index(
        op.f("ix_content_import_runs_file_sha256"),
        "content_import_runs",
        ["file_sha256"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_content_import_runs_file_sha256"),
        table_name="content_import_runs",
    )
    op.drop_index(
        op.f("ix_content_import_runs_dataset_id"),
        table_name="content_import_runs",
    )
    op.drop_table("content_import_runs")

    op.drop_constraint(
        op.f("ck_sources_exactly_one_subject"),
        "sources",
        type_="check",
    )
    op.execute(
        "DELETE FROM sources "
        "WHERE chapter_id IS NOT NULL OR faction_id IS NOT NULL"
    )
    op.create_check_constraint(
        op.f("ck_sources_exactly_one_subject"),
        "sources",
        "num_nonnulls(character_id, event_id, relationship_id) = 1",
    )
    op.drop_index(op.f("ix_sources_faction_id"), table_name="sources")
    op.drop_index(op.f("ix_sources_chapter_id"), table_name="sources")
    op.drop_constraint(
        op.f("fk_sources_faction_id_factions"),
        "sources",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_sources_chapter_id_chapters"),
        "sources",
        type_="foreignkey",
    )
    op.drop_column("sources", "faction_id")
    op.drop_column("sources", "chapter_id")
