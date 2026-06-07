import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain import ProgressKey, RelationType, SubmissionStatus, SubmissionType


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, list[str]] | None = None


class ResponseMeta(BaseModel):
    request_id: str | None = None
    next_cursor: str | None = None


class ApiResponse[T](BaseModel):
    data: T | None = None
    error: ErrorDetail | None = None
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class HealthData(BaseModel):
    status: str
    environment: str


class RestrictedData(BaseModel):
    restricted: bool = True
    required_progress: ProgressKey | None = None
    message: str = "该内容涉及后续剧情，已隐藏。"


class GraphNode(BaseModel):
    id: uuid.UUID
    slug: str
    label: str
    faction_id: uuid.UUID | None
    faction_name: str | None
    importance: int
    summary: str


class GraphEdge(BaseModel):
    id: uuid.UUID
    source: uuid.UUID
    target: uuid.UUID
    relation_type: RelationType
    label: str
    summary: str
    directional: bool


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    progress: ProgressKey


class SubmissionCreate(BaseModel):
    submission_type: SubmissionType
    payload: dict[str, str | int | bool | list[str]]
    source_note: str = Field(min_length=10, max_length=4000)
    contact: str | None = Field(default=None, max_length=200)
    website: str = Field(default="", max_length=0, exclude=True)


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    submission_type: SubmissionType
    payload: dict[str, object]
    source_note: str
    contact: str | None
    status: SubmissionStatus
    review_note: str | None
    created_at: datetime
