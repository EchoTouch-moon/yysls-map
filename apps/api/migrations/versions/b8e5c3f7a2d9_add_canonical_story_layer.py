"""add canonical story layer (frozen contract v0.1 rev 2)

Revision ID: b8e5c3f7a2d9
Revises: a7c1e9b4d2f8
Create Date: 2026-08-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b8e5c3f7a2d9"
down_revision: str | None = "a7c1e9b4d2f8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    canonical_story_node_type = postgresql.ENUM(
        "CHAPTER",
        "MAIN_PART",
        "MAIN_QUEST",
        name="canonical_story_node_type",
        create_type=False,
    )
    canonical_mapping_kind = postgresql.ENUM(
        "EXACT",
        "MERGED",
        "SPLIT",
        name="canonical_mapping_kind",
        create_type=False,
    )
    canonical_verification_state = postgresql.ENUM(
        "VERIFIED",
        "PROVISIONAL",
        "SOURCE_CONFLICT",
        "UNRESOLVED",
        name="canonical_verification_state",
        create_type=False,
    )
    canonical_spine = postgresql.ENUM(
        "MAIN",
        "SECONDARY",
        name="canonical_spine",
        create_type=False,
    )
    content_status = postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "ARCHIVED",
        name="content_status",
        create_type=False,
    )
    canonical_story_node_type.create(op.get_bind(), checkfirst=True)
    canonical_mapping_kind.create(op.get_bind(), checkfirst=True)
    canonical_verification_state.create(op.get_bind(), checkfirst=True)
    canonical_spine.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "canonical_story_nodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("canonical_key", sa.String(length=200), nullable=False),
        sa.Column("native_id", sa.String(length=200), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("node_type", canonical_story_node_type, nullable=False),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("chapter_slug", sa.String(length=80), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("spine", canonical_spine, server_default="MAIN", nullable=False),
        sa.Column(
            "provenance",
            postgresql.JSON(astext_type=sa.Text()),
            server_default=sa.text("'[]'::json"),
            nullable=False,
        ),
        sa.Column("verification_state", canonical_verification_state, nullable=False),
        sa.Column(
            "status",
            content_status,
            server_default="DRAFT",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sort_order >= 0", name=op.f("ck_canonical_story_nodes_sort_order_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["canonical_story_nodes.id"],
            name=op.f("fk_canonical_story_nodes_parent_id_canonical_story_nodes"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_canonical_story_nodes")),
        sa.UniqueConstraint(
            "canonical_key", name=op.f("uq_canonical_story_nodes_canonical_key")
        ),
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_canonical_key"), "canonical_story_nodes", ["canonical_key"]
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_chapter_slug"), "canonical_story_nodes", ["chapter_slug"]
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_node_type"), "canonical_story_nodes", ["node_type"]
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_parent_id"), "canonical_story_nodes", ["parent_id"]
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_status"), "canonical_story_nodes", ["status"]
    )
    op.create_index(
        op.f("ix_canonical_story_nodes_verification_state"),
        "canonical_story_nodes",
        ["verification_state"],
    )
    op.create_index(
        "ix_canonical_story_nodes_parent_order",
        "canonical_story_nodes",
        ["parent_id", "sort_order"],
        unique=True,
        postgresql_where=sa.text("parent_id IS NOT NULL"),
    )

    op.create_table(
        "canonical_story_event_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("canonical_node_id", sa.UUID(), nullable=False),
        sa.Column("story_event_id", sa.UUID(), nullable=False),
        sa.Column("mapping_kind", canonical_mapping_kind, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sort_order >= 0", name=op.f("ck_canonical_story_event_links_sort_order_nonnegative")
        ),
        sa.ForeignKeyConstraint(
            ["canonical_node_id"],
            ["canonical_story_nodes.id"],
            name=op.f("fk_canonical_story_event_links_canonical_node_id_canonical_story_nodes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["story_event_id"],
            ["story_events.id"],
            name=op.f("fk_canonical_story_event_links_story_event_id_story_events"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_canonical_story_event_links")),
        sa.UniqueConstraint(
            "canonical_node_id",
            "story_event_id",
            name=op.f("uq_canonical_link_node_event"),
        ),
    )
    op.create_index(
        op.f("ix_canonical_story_event_links_canonical_node_id"),
        "canonical_story_event_links",
        ["canonical_node_id"],
    )
    op.create_index(
        op.f("ix_canonical_story_event_links_mapping_kind"),
        "canonical_story_event_links",
        ["mapping_kind"],
    )
    op.create_index(
        op.f("ix_canonical_story_event_links_story_event_id"),
        "canonical_story_event_links",
        ["story_event_id"],
    )


def downgrade() -> None:
    op.drop_table("canonical_story_event_links")
    op.drop_table("canonical_story_nodes")

    bind = op.get_bind()
    postgresql.ENUM(name="canonical_spine").drop(bind, checkfirst=True)
    postgresql.ENUM(name="canonical_verification_state").drop(bind, checkfirst=True)
    postgresql.ENUM(name="canonical_mapping_kind").drop(bind, checkfirst=True)
    postgresql.ENUM(name="canonical_story_node_type").drop(bind, checkfirst=True)
