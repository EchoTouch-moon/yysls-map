import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.contracts import SubmissionPayload
from app.domain import ContentStatus, SubmissionStatus, SubmissionType
from app.models import Chapter, Character, Relationship, StoryEvent, Submission


def create_submission(
    db: Session,
    *,
    submission_type: SubmissionType,
    payload: SubmissionPayload,
    source_note: str,
    contact: str | None,
) -> Submission:
    submission = Submission(
        submission_type=submission_type,
        payload=payload.model_dump(mode="json", exclude_none=True),
        source_note=source_note,
        contact=contact,
        status=SubmissionStatus.PENDING,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def _get_character(db: Session, slug: str | None, field_name: str) -> Character:
    character = db.scalar(select(Character).where(Character.slug == slug))
    if character is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field_name} 对应的角色不存在。",
        )
    return character


def _get_chapter(db: Session, slug: str | None) -> Chapter:
    chapter = db.scalar(select(Chapter).where(Chapter.slug == slug))
    if chapter is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="投稿对应的章节不存在。",
        )
    return chapter


def _approve_relationship(db: Session, payload: SubmissionPayload) -> None:
    source = _get_character(db, payload.source_character_slug, "source_character_slug")
    target = _get_character(db, payload.target_character_slug, "target_character_slug")
    if payload.relation_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="关系投稿缺少 relation_type。",
        )
    duplicate = db.scalar(
        select(Relationship.id).where(
            Relationship.source_character_id == source.id,
            Relationship.target_character_id == target.id,
            Relationship.relation_type == payload.relation_type,
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="相同角色和类型的关系已存在。",
        )
    chapter = _get_chapter(db, payload.chapter_slug) if payload.chapter_slug else None
    db.add(
        Relationship(
            source_character_id=source.id,
            target_character_id=target.id,
            relation_type=payload.relation_type,
            label=payload.title,
            summary=payload.summary,
            chapter_id=chapter.id if chapter else None,
            visible_after_chapter_id=chapter.id if chapter else None,
            spoiler_level=payload.spoiler_level,
            status=ContentStatus.PUBLISHED,
        )
    )


def _approve_event(db: Session, payload: SubmissionPayload) -> None:
    chapter = _get_chapter(db, payload.chapter_slug)
    next_order = (
        db.scalar(
            select(StoryEvent.sort_order)
            .where(StoryEvent.chapter_id == chapter.id)
            .order_by(StoryEvent.sort_order.desc())
            .limit(1)
        )
        or 0
    ) + 1
    slug = f"community-{uuid.uuid4().hex[:12]}"
    db.add(
        StoryEvent(
            slug=slug,
            title=payload.title,
            summary=payload.summary,
            chapter_id=chapter.id,
            sort_order=next_order,
            visible_after_chapter_id=chapter.id,
            spoiler_level=payload.spoiler_level,
            status=ContentStatus.PUBLISHED,
        )
    )


def _approve_interpretation(db: Session, payload: SubmissionPayload) -> None:
    character = _get_character(db, payload.character_slug, "character_slug")
    character.interpretation = payload.summary


def review_submission(
    db: Session,
    *,
    submission_id: uuid.UUID,
    action: str,
    review_note: str,
    reviewer: str,
) -> Submission:
    submission = db.scalar(
        select(Submission).where(Submission.id == submission_id).with_for_update()
    )
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="投稿不存在。")
    if submission.status is not SubmissionStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="投稿已完成审核。")

    if action == "approve":
        payload = SubmissionPayload.model_validate(submission.payload)
        if submission.submission_type is SubmissionType.RELATIONSHIP:
            _approve_relationship(db, payload)
        elif submission.submission_type is SubmissionType.EVENT:
            _approve_event(db, payload)
        elif submission.submission_type is SubmissionType.INTERPRETATION:
            _approve_interpretation(db, payload)
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="纠错投稿需要管理员手工处理，不能自动批准。",
            )
        submission.status = SubmissionStatus.APPROVED
    else:
        submission.status = SubmissionStatus.REJECTED

    submission.review_note = review_note
    submission.reviewed_by = reviewer
    db.commit()
    db.refresh(submission)
    return submission

