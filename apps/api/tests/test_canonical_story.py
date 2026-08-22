"""C2 gate tests for the canonical story layer (frozen contract v0.1 rev 2).

Covers the C2 acceptance gates:
- G1 additive import / G3 identity constraints / G7 parity (DB tests);
- G4 publication safety / G5 mapping invariants / G6 provenance (pure validator);
plus the migration -> import -> validate -> query internally loop.
"""

import os
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.content_import import (
    CanonicalDataset,
    ContentValidationError,
    import_canonical_dataset,
    validate_canonical_dataset,
)
from app.content_import.models import CanonicalProvenanceItem
from app.db import SessionLocal
from app.domain import (
    CanonicalEvidenceRole,
    CanonicalMappingKind,
    CanonicalSourceKind,
    CanonicalSpine,
    CanonicalStoryNodeType,
    CanonicalVerificationState,
    ContentStatus,
    ProgressKey,
)
from app.models import (
    CanonicalStoryEventLink,
    CanonicalStoryNode,
    Chapter,
    StoryEvent,
)
from app.services.canonical import (
    get_canonical_node,
    get_links_for_event,
    get_links_for_node,
    ordered_main_spine,
)

DB_TEST = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)

IDENTITY = CanonicalEvidenceRole.IDENTITY


def _provenance(
    role: CanonicalEvidenceRole = IDENTITY,
    ref: str = "https://example.test/source",
) -> dict:
    return {"source_kind": CanonicalSourceKind.WALKTHROUGH, "ref": ref, "evidence_role": role}


def _node(
    key: str,
    *,
    parent_key: str | None = None,
    sort_order: int = 0,
    node_type: CanonicalStoryNodeType = CanonicalStoryNodeType.MAIN_QUEST,
    state: CanonicalVerificationState = CanonicalVerificationState.VERIFIED,
    status: ContentStatus = ContentStatus.PUBLISHED,
    provenance: list[dict] | None = None,
    title: str | None = None,
) -> dict:
    return {
        "canonical_key": key,
        "title": title or key,
        "node_type": node_type,
        "region": "清河",
        "chapter_slug": "qinghe",
        "parent_key": parent_key,
        "sort_order": sort_order,
        "spine": CanonicalSpine.MAIN,
        "provenance": provenance if provenance is not None else [_provenance()],
        "verification_state": state,
        "status": status,
    }


def _link(node_key: str, event_slug: str, kind: CanonicalMappingKind) -> dict:
    return {"node_key": node_key, "event_slug": event_slug, "mapping_kind": kind}


def _dataset(nodes: list[dict], links: list[dict]) -> CanonicalDataset:
    return CanonicalDataset.model_validate(
        {
            "schema_version": "0.1",
            "dataset": {"id": "c2-test-canonical", "title": "C2 test canonical"},
            "nodes": nodes,
            "links": links,
        }
    )


# ---------------------------------------------------------------------------
# C2-G4 publication safety (pure validator)
# ---------------------------------------------------------------------------


def test_g4_unresolved_node_cannot_be_published() -> None:
    ds = _dataset(
        [_node("n1", state=CanonicalVerificationState.UNRESOLVED)],
        [],
    )
    with pytest.raises(ContentValidationError, match="cannot be PUBLISHED"):
        validate_canonical_dataset(ds)


def test_g4_provisional_node_cannot_be_published() -> None:
    ds = _dataset(
        [_node("n1", state=CanonicalVerificationState.PROVISIONAL)],
        [],
    )
    with pytest.raises(ContentValidationError, match="cannot be PUBLISHED"):
        validate_canonical_dataset(ds)


def test_g4_unresolved_node_can_be_draft() -> None:
    ds = _dataset(
        [_node("n1", state=CanonicalVerificationState.UNRESOLVED, status=ContentStatus.DRAFT)],
        [],
    )
    validate_canonical_dataset(ds)  # must not raise


# ---------------------------------------------------------------------------
# C2-G5 mapping cardinality invariants (pure validator)
# ---------------------------------------------------------------------------


def test_g5_merged_event_with_single_link_rejected() -> None:
    """MERGED needs at least two nodes; an event with one MERGED link is invalid."""
    ds = _dataset([_node("n1")], [_link("n1", "evt-x", CanonicalMappingKind.MERGED)])
    with pytest.raises(ContentValidationError, match="single link must be EXACT or SPLIT"):
        validate_canonical_dataset(ds)


def test_g5_event_with_two_exact_links_rejected() -> None:
    ds = _dataset(
        [_node("n1"), _node("n2")],
        [
            _link("n1", "evt-x", CanonicalMappingKind.EXACT),
            _link("n2", "evt-x", CanonicalMappingKind.EXACT),
        ],
    )
    with pytest.raises(ContentValidationError, match="must be all MERGED"):
        validate_canonical_dataset(ds)


def test_g5_merged_event_mixed_with_exact_rejected() -> None:
    ds = _dataset(
        [_node("n1"), _node("n2")],
        [
            _link("n1", "evt-x", CanonicalMappingKind.MERGED),
            _link("n2", "evt-x", CanonicalMappingKind.EXACT),
        ],
    )
    with pytest.raises(ContentValidationError, match="must be all MERGED"):
        validate_canonical_dataset(ds)


def test_g5_split_with_single_event_rejected() -> None:
    """SPLIT needs at least two events; a node with one SPLIT link is invalid."""
    ds = _dataset([_node("n1")], [_link("n1", "evt-x", CanonicalMappingKind.SPLIT)])
    with pytest.raises(ContentValidationError, match="single link must be EXACT or MERGED"):
        validate_canonical_dataset(ds)


def test_g5_split_node_mixed_with_exact_rejected() -> None:
    ds = _dataset(
        [_node("n1")],
        [
            _link("n1", "evt-x", CanonicalMappingKind.EXACT),
            _link("n1", "evt-y", CanonicalMappingKind.SPLIT),
        ],
    )
    with pytest.raises(ContentValidationError, match="must be all SPLIT"):
        validate_canonical_dataset(ds)


def test_g5_complex_many_to_many_rejected() -> None:
    """Frozen rule: v0.1 rejects complex N:M mapping groups."""
    ds = _dataset(
        [_node("n1"), _node("n2")],
        [
            _link("n1", "evt-x", CanonicalMappingKind.MERGED),
            _link("n2", "evt-x", CanonicalMappingKind.MERGED),
            _link("n1", "evt-y", CanonicalMappingKind.SPLIT),
            _link("n1", "evt-z", CanonicalMappingKind.SPLIT),
        ],
    )
    with pytest.raises(ContentValidationError, match="complex N:M mapping group"):
        validate_canonical_dataset(ds)


def test_g5_valid_exact_merged_split_pass() -> None:
    ds = _dataset(
        [
            _node("exact-node"),
            _node("merged-a"),
            _node("merged-b"),
            _node("split-node"),
        ],
        [
            _link("exact-node", "evt-e", CanonicalMappingKind.EXACT),
            _link("merged-a", "evt-m", CanonicalMappingKind.MERGED),
            _link("merged-b", "evt-m", CanonicalMappingKind.MERGED),
            _link("split-node", "evt-s1", CanonicalMappingKind.SPLIT),
            _link("split-node", "evt-s2", CanonicalMappingKind.SPLIT),
        ],
    )
    validate_canonical_dataset(ds)  # must not raise


# ---------------------------------------------------------------------------
# C2-G6 provenance validation (pure validator)
# ---------------------------------------------------------------------------


def test_g6_published_node_needs_identity_or_general_evidence() -> None:
    ds = _dataset(
        [
            _node(
                "n1",
                provenance=[_provenance(role=CanonicalEvidenceRole.ORDER)],
            )
        ],
        [],
    )
    with pytest.raises(ContentValidationError, match="IDENTITY or GENERAL"):
        validate_canonical_dataset(ds)


def test_g6_invalid_evidence_role_rejected() -> None:
    with pytest.raises(ValidationError):
        CanonicalProvenanceItem.model_validate(
            {
                "source_kind": CanonicalSourceKind.WALKTHROUGH,
                "ref": "x",
                "evidence_role": "not-a-role",
            }
        )


def test_g6_empty_ref_rejected() -> None:
    with pytest.raises(ValidationError):
        CanonicalProvenanceItem.model_validate(
            {
                "source_kind": CanonicalSourceKind.WALKTHROUGH,
                "ref": "   ",
                "evidence_role": IDENTITY,
            }
        )


def test_g6_editorial_only_event_needs_no_link() -> None:
    """An editorial-only event simply has no canonical link (zero-link audit)."""
    ds = _dataset([_node("n1")], [])
    validate_canonical_dataset(ds)


# ---------------------------------------------------------------------------
# C2-G1 additive import + C2-G3 identity constraints + query loop (DB tests)
# ---------------------------------------------------------------------------


def _seed_event(db, marker: str, slug_suffix: str, chapter: Chapter) -> StoryEvent:
    event = StoryEvent(
        slug=f"c2-{slug_suffix}-{marker}",
        title=f"C2 {slug_suffix}",
        summary="c2 fixture",
        chapter_id=chapter.id,
        sort_order=1,
        spoiler_level=0,
        status=ContentStatus.PUBLISHED,
    )
    db.add(event)
    return event


@DB_TEST
def test_c2_g1_import_is_additive_and_query_loop() -> None:
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            chapter = Chapter(
                slug=f"c2-chapter-{marker}",
                title="C2 章",
                region="清河",
                sort_order=9700,
                progress_key=ProgressKey.START,
                progress_rank=0,
                status=ContentStatus.PUBLISHED,
            )
            db.add(chapter)
            db.flush()
            ev1 = _seed_event(db, marker, "ev1", chapter)
            db.flush()
            event_count_before = db.scalar(select(func.count()).select_from(StoryEvent))

            prefix = f"csn-{marker}"
            ds = _dataset(
                [
                    _node(f"{prefix}-ch1", node_type=CanonicalStoryNodeType.CHAPTER, title="章"),
                    _node(
                        f"{prefix}-p1",
                        node_type=CanonicalStoryNodeType.MAIN_PART,
                        parent_key=f"{prefix}-ch1",
                        sort_order=1,
                        title="篇一",
                    ),
                    _node(
                        f"{prefix}-q1",
                        parent_key=f"{prefix}-p1",
                        sort_order=1,
                        title="节点一",
                    ),
                ],
                [_link(f"{prefix}-q1", ev1.slug, CanonicalMappingKind.EXACT)],
            )
            import_canonical_dataset(db, ds)
            db.flush()

            # G1: existing story content untouched
            event_count_after = db.scalar(select(func.count()).select_from(StoryEvent))
            assert event_count_after == event_count_before

            # migration -> import -> validate -> query internally
            node = get_canonical_node(db, f"{prefix}-q1")
            assert node is not None
            assert node.parent is not None
            links = get_links_for_node(db, node.id)
            assert len(links) == 1
            assert links[0].mapping_kind is CanonicalMappingKind.EXACT
            assert links[0].event.slug == ev1.slug
            event_links = get_links_for_event(db, ev1.id)
            assert len(event_links) == 1
            spine = ordered_main_spine(db, chapter_slug="qinghe")
            assert any(n.canonical_key == f"{prefix}-q1" for n in spine)
        finally:
            db.rollback()


@DB_TEST
def test_c2_g3_identity_constraints() -> None:
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            parent = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-parent",
                title="parent",
                node_type=CanonicalStoryNodeType.CHAPTER,
                region="清河",
                chapter_slug="qinghe",
                sort_order=0,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(parent)
            db.flush()

            # native_id nullable (G3)
            node = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-child",
                title="child",
                node_type=CanonicalStoryNodeType.MAIN_PART,
                region="清河",
                chapter_slug="qinghe",
                parent_id=parent.id,
                sort_order=1,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(node)
            db.flush()
            assert node.native_id is None

            # duplicate canonical_key -> reject
            dup = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-child",
                title="dup",
                node_type=CanonicalStoryNodeType.MAIN_PART,
                region="清河",
                chapter_slug="qinghe",
                sort_order=2,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(dup)
            with pytest.raises(IntegrityError):
                db.flush()
            db.rollback()

            # parent FK to missing node -> reject
            orphan = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-orphan",
                title="orphan",
                node_type=CanonicalStoryNodeType.MAIN_QUEST,
                region="清河",
                chapter_slug="qinghe",
                parent_id=uuid.uuid4(),
                sort_order=9,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(orphan)
            with pytest.raises(IntegrityError):
                db.flush()
            db.rollback()

            # duplicate (parent_id, sort_order) -> reject (partial unique index)
            sibling = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-sibling",
                title="sibling",
                node_type=CanonicalStoryNodeType.MAIN_PART,
                region="清河",
                chapter_slug="qinghe",
                parent_id=parent.id,
                sort_order=1,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(sibling)
            with pytest.raises(IntegrityError):
                db.flush()
            db.rollback()
        finally:
            db.rollback()


@DB_TEST
def test_c2_g3_link_unique_and_fk() -> None:
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            chapter = Chapter(
                slug=f"c2-ch-{marker}",
                title="C2",
                region="清河",
                sort_order=9701,
                progress_key=ProgressKey.START,
                progress_rank=0,
                status=ContentStatus.PUBLISHED,
            )
            db.add(chapter)
            db.flush()
            event = _seed_event(db, marker, "ev", chapter)
            db.flush()
            node = CanonicalStoryNode(
                canonical_key=f"csn-{marker}-node",
                title="n",
                node_type=CanonicalStoryNodeType.MAIN_QUEST,
                region="清河",
                chapter_slug="qinghe",
                sort_order=0,
                provenance=[],
                verification_state=CanonicalVerificationState.VERIFIED,
                status=ContentStatus.DRAFT,
            )
            db.add(node)
            db.flush()

            def add_link() -> None:
                db.add(
                    CanonicalStoryEventLink(
                        canonical_node_id=node.id,
                        story_event_id=event.id,
                        mapping_kind=CanonicalMappingKind.EXACT,
                        sort_order=0,
                        is_primary=True,
                    )
                )

            add_link()
            db.flush()
            add_link()  # duplicate (node_id, event_id)
            with pytest.raises(IntegrityError):
                db.flush()
            db.rollback()

            # link FK to missing node -> reject
            bad = CanonicalStoryEventLink(
                canonical_node_id=uuid.uuid4(),
                story_event_id=event.id,
                mapping_kind=CanonicalMappingKind.EXACT,
                sort_order=0,
            )
            db.add(bad)
            with pytest.raises(IntegrityError):
                db.flush()
            db.rollback()
        finally:
            db.rollback()


@DB_TEST
def test_c2_import_missing_event_slug_fails_closed() -> None:
    marker = uuid.uuid4().hex[:8]
    with SessionLocal() as db:
        try:
            ds = _dataset(
                [_node(f"csn-{marker}-n1")],
                [_link(f"csn-{marker}-n1", "no-such-event", CanonicalMappingKind.EXACT)],
            )
            with pytest.raises(ContentValidationError, match="missing events"):
                import_canonical_dataset(db, ds)
        finally:
            db.rollback()
