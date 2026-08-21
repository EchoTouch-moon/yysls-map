"""add story guides and historical context

Revision ID: 6f4a2c9d8e31
Revises: 4d3b9f7c2a11
Create Date: 2026-08-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "6f4a2c9d8e31"
down_revision: str | None = "4d3b9f7c2a11"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    story_beat_role = postgresql.ENUM(
        "SETUP",
        "CLUE",
        "ESCALATION",
        "TURNING_POINT",
        "CONSEQUENCE",
        "RESOLUTION",
        name="story_beat_role",
        create_type=False,
    )
    historical_fact_kind = postgresql.ENUM(
        "WORK_FACT",
        "HISTORICAL_FACT",
        "CREDIBLE_PARALLEL",
        "EDITORIAL_INFERENCE",
        name="historical_fact_kind",
        create_type=False,
    )
    historical_relation_kind = postgresql.ENUM(
        "SETTING",
        "INSPIRED_BY",
        "PARALLEL",
        "CONTRAST",
        "FICTIONALIZED",
        name="historical_relation_kind",
        create_type=False,
    )
    historical_reference_type = postgresql.ENUM(
        "PRIMARY_SOURCE",
        "SCHOLARLY_RESEARCH",
        "INSTITUTIONAL_REFERENCE",
        name="historical_reference_type",
        create_type=False,
    )
    content_status = postgresql.ENUM(
        "DRAFT",
        "PUBLISHED",
        "ARCHIVED",
        name="content_status",
        create_type=False,
    )
    story_beat_role.create(op.get_bind(), checkfirst=True)
    historical_fact_kind.create(op.get_bind(), checkfirst=True)
    historical_relation_kind.create(op.get_bind(), checkfirst=True)
    historical_reference_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "story_arcs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("core_question", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("visible_after_chapter_id", sa.UUID(), nullable=True),
        sa.Column("spoiler_level", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            content_status,
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
            "estimated_minutes >= 1", name=op.f("ck_story_arcs_estimated_minutes_positive")
        ),
        sa.CheckConstraint(
            "spoiler_level >= 0 AND spoiler_level <= 3",
            name=op.f("ck_story_arcs_spoiler_level_range"),
        ),
        sa.ForeignKeyConstraint(
            ["visible_after_chapter_id"],
            ["chapters.id"],
            name=op.f("fk_story_arcs_visible_after_chapter_id_chapters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_story_arcs")),
        sa.UniqueConstraint("slug", name=op.f("uq_story_arcs_slug")),
    )
    op.create_index(op.f("ix_story_arcs_slug"), "story_arcs", ["slug"])
    op.create_index(op.f("ix_story_arcs_status"), "story_arcs", ["status"])
    op.create_index(
        op.f("ix_story_arcs_visible_after_chapter_id"), "story_arcs", ["visible_after_chapter_id"]
    )

    op.create_table(
        "story_arc_beats",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("arc_id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("role", story_beat_role, nullable=False),
        sa.Column("guide", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("bridge", sa.Text(), nullable=False),
        sa.Column("next_question", sa.Text(), nullable=False),
        sa.Column("visible_after_chapter_id", sa.UUID(), nullable=True),
        sa.Column("spoiler_level", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            content_status,
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
            "sort_order >= 0", name=op.f("ck_story_arc_beats_sort_order_nonnegative")
        ),
        sa.CheckConstraint(
            "spoiler_level >= 0 AND spoiler_level <= 3",
            name=op.f("ck_story_arc_beats_spoiler_level_range"),
        ),
        sa.ForeignKeyConstraint(
            ["arc_id"],
            ["story_arcs.id"],
            name=op.f("fk_story_arc_beats_arc_id_story_arcs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["story_events.id"],
            name=op.f("fk_story_arc_beats_event_id_story_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["visible_after_chapter_id"],
            ["chapters.id"],
            name=op.f("fk_story_arc_beats_visible_after_chapter_id_chapters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_story_arc_beats")),
        sa.UniqueConstraint("arc_id", "event_id", name="uq_story_arc_beat_event"),
        sa.UniqueConstraint("arc_id", "sort_order", name="uq_story_arc_beat_order"),
    )
    op.create_index(op.f("ix_story_arc_beats_arc_id"), "story_arc_beats", ["arc_id"])
    op.create_index(op.f("ix_story_arc_beats_event_id"), "story_arc_beats", ["event_id"])
    op.create_index(op.f("ix_story_arc_beats_status"), "story_arc_beats", ["status"])
    op.create_index(
        op.f("ix_story_arc_beats_visible_after_chapter_id"),
        "story_arc_beats",
        ["visible_after_chapter_id"],
    )

    op.create_table(
        "historical_references",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("reference_type", historical_reference_type, nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("publisher", sa.String(length=160), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("locator", sa.String(length=240), nullable=True),
        sa.Column("accessed_at", sa.Date(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_historical_references")),
        sa.UniqueConstraint("slug", name=op.f("uq_historical_references_slug")),
    )
    op.create_index(op.f("ix_historical_references_slug"), "historical_references", ["slug"])

    op.create_table(
        "historical_contexts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("period_label", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("fact_kind", historical_fact_kind, nullable=False),
        sa.Column("boundary_note", sa.Text(), nullable=False),
        sa.Column("visible_after_chapter_id", sa.UUID(), nullable=True),
        sa.Column("spoiler_level", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            content_status,
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
            "spoiler_level >= 0 AND spoiler_level <= 3",
            name=op.f("ck_historical_contexts_spoiler_level_range"),
        ),
        sa.ForeignKeyConstraint(
            ["visible_after_chapter_id"],
            ["chapters.id"],
            name=op.f("fk_historical_contexts_visible_after_chapter_id_chapters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_historical_contexts")),
        sa.UniqueConstraint("slug", name=op.f("uq_historical_contexts_slug")),
    )
    op.create_index(op.f("ix_historical_contexts_fact_kind"), "historical_contexts", ["fact_kind"])
    op.create_index(op.f("ix_historical_contexts_slug"), "historical_contexts", ["slug"])
    op.create_index(op.f("ix_historical_contexts_status"), "historical_contexts", ["status"])
    op.create_index(
        op.f("ix_historical_contexts_visible_after_chapter_id"),
        "historical_contexts",
        ["visible_after_chapter_id"],
    )

    op.create_table(
        "historical_context_references",
        sa.Column("context_id", sa.UUID(), nullable=False),
        sa.Column("reference_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["historical_contexts.id"],
            name=op.f("fk_historical_context_references_context_id_historical_contexts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reference_id"],
            ["historical_references.id"],
            name=op.f("fk_historical_context_references_reference_id_historical_references"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "context_id", "reference_id", name=op.f("pk_historical_context_references")
        ),
    )

    op.create_table(
        "event_historical_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("context_id", sa.UUID(), nullable=False),
        sa.Column("relation_kind", historical_relation_kind, nullable=False),
        sa.Column("editorial_note", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("visible_after_chapter_id", sa.UUID(), nullable=True),
        sa.Column("spoiler_level", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            content_status,
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
            "sort_order >= 0", name=op.f("ck_event_historical_links_sort_order_nonnegative")
        ),
        sa.CheckConstraint(
            "spoiler_level >= 0 AND spoiler_level <= 3",
            name=op.f("ck_event_historical_links_spoiler_level_range"),
        ),
        sa.ForeignKeyConstraint(
            ["context_id"],
            ["historical_contexts.id"],
            name=op.f("fk_event_historical_links_context_id_historical_contexts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["story_events.id"],
            name=op.f("fk_event_historical_links_event_id_story_events"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["visible_after_chapter_id"],
            ["chapters.id"],
            name=op.f("fk_event_historical_links_visible_after_chapter_id_chapters"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_historical_links")),
        sa.UniqueConstraint("event_id", "context_id", name="uq_event_historical_context"),
        sa.UniqueConstraint("event_id", "sort_order", name="uq_event_historical_sort_order"),
    )
    op.create_index(
        op.f("ix_event_historical_links_context_id"), "event_historical_links", ["context_id"]
    )
    op.create_index(
        op.f("ix_event_historical_links_event_id"), "event_historical_links", ["event_id"]
    )
    op.create_index(op.f("ix_event_historical_links_status"), "event_historical_links", ["status"])
    op.create_index(
        op.f("ix_event_historical_links_visible_after_chapter_id"),
        "event_historical_links",
        ["visible_after_chapter_id"],
    )


def downgrade() -> None:
    op.drop_table("event_historical_links")
    op.drop_table("historical_context_references")
    op.drop_table("historical_contexts")
    op.drop_table("historical_references")
    op.drop_table("story_arc_beats")
    op.drop_table("story_arcs")

    bind = op.get_bind()
    postgresql.ENUM(name="historical_reference_type").drop(bind, checkfirst=True)
    postgresql.ENUM(name="historical_relation_kind").drop(bind, checkfirst=True)
    postgresql.ENUM(name="historical_fact_kind").drop(bind, checkfirst=True)
    postgresql.ENUM(name="story_beat_role").drop(bind, checkfirst=True)
