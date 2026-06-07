import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import CharacterDetail, RelationshipDetail
from app.db import get_db
from app.domain import ContentStatus, ProgressKey
from app.models import Chapter, Character, Faction, Relationship
from app.schemas import ApiResponse, RestrictedData
from app.services.spoiler import context_for, is_visible

router = APIRouter(tags=["details"])


@router.get(
    "/characters/{slug}",
    response_model=ApiResponse[CharacterDetail | RestrictedData],
)
def character_detail(
    slug: str,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    reveal: bool = Query(default=False),
) -> ApiResponse[CharacterDetail | RestrictedData]:
    row = db.execute(
        select(Character, Faction.name, Chapter)
        .outerjoin(
            Faction,
            (Character.faction_id == Faction.id) & (Faction.status == ContentStatus.PUBLISHED),
        )
        .outerjoin(
            Chapter,
            (Character.first_appear_chapter_id == Chapter.id)
            & (Chapter.status == ContentStatus.PUBLISHED),
        )
        .where(Character.slug == slug, Character.status == ContentStatus.PUBLISHED)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在。")
    character, faction_name, first_chapter = row
    required_chapter = db.get(
        Chapter, character.visible_after_chapter_id or character.first_appear_chapter_id
    )
    visible = is_visible(
        context=context_for(progress, allow_reveal=reveal),
        required_progress_rank=required_chapter.progress_rank if required_chapter else None,
        spoiler_level=character.spoiler_level,
    )
    if not visible:
        return ApiResponse(
            data=RestrictedData(
                required_progress=required_chapter.progress_key if required_chapter else None
            )
        )
    return ApiResponse(
        data=CharacterDetail(
            id=character.id,
            slug=character.slug,
            name=character.name,
            summary=character.summary,
            interpretation=character.interpretation,
            identity_tags=character.identity_tags,
            faction_name=faction_name,
            first_appear_chapter=first_chapter.title if first_chapter else None,
        )
    )


@router.get(
    "/relationships/{relationship_id}",
    response_model=ApiResponse[RelationshipDetail | RestrictedData],
)
def relationship_detail(
    relationship_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    progress: ProgressKey = ProgressKey.START,
    reveal: bool = Query(default=False),
) -> ApiResponse[RelationshipDetail | RestrictedData]:
    relationship = db.get(Relationship, relationship_id)
    if (
        relationship is None
        or relationship.status is not ContentStatus.PUBLISHED
        or relationship.source.status is not ContentStatus.PUBLISHED
        or relationship.target.status is not ContentStatus.PUBLISHED
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="关系不存在。")
    required_chapter = db.get(
        Chapter, relationship.visible_after_chapter_id or relationship.chapter_id
    )
    visible = is_visible(
        context=context_for(progress, allow_reveal=reveal),
        required_progress_rank=required_chapter.progress_rank if required_chapter else None,
        spoiler_level=relationship.spoiler_level,
    )
    if not visible:
        return ApiResponse(
            data=RestrictedData(
                required_progress=required_chapter.progress_key if required_chapter else None
            )
        )
    return ApiResponse(
        data=RelationshipDetail(
            id=relationship.id,
            source_name=relationship.source.name,
            target_name=relationship.target.name,
            relation_type=relationship.relation_type,
            label=relationship.label,
            summary=relationship.summary,
            stage=relationship.stage,
            confidence=float(Decimal(relationship.confidence)),
        )
    )
