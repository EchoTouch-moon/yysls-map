from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.contracts import RelationshipPathData, SearchData
from app.db import get_db
from app.domain import ProgressKey
from app.schemas import ApiResponse
from app.services.path import shortest_visible_path
from app.services.search import search_visible_content

router = APIRouter(tags=["discovery"])


@router.get("/search", response_model=ApiResponse[SearchData])
def search(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, max_length=100)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[SearchData]:
    return ApiResponse(
        data=SearchData(
            query=q,
            results=search_visible_content(db, query=q, progress=progress),
        )
    )


@router.get(
    "/relationships/path",
    response_model=ApiResponse[RelationshipPathData],
)
def relationship_path(
    db: Annotated[Session, Depends(get_db)],
    source: Annotated[str, Query(alias="from", min_length=1, max_length=100)],
    target: Annotated[str, Query(alias="to", min_length=1, max_length=100)],
    progress: ProgressKey = ProgressKey.START,
) -> ApiResponse[RelationshipPathData]:
    return ApiResponse(
        data=shortest_visible_path(
            db,
            source_slug=source,
            target_slug=target,
            progress=progress,
        )
    )

