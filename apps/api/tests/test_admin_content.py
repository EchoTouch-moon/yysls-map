import os
import uuid
from typing import cast

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.contracts import AdminChapterWrite, AdminRelationshipWrite
from app.core.config import settings
from app.core.security import password_hasher
from app.db import SessionLocal
from app.main import app
from app.models import Chapter
from app.services.admin_content import archive_content


def test_admin_content_requires_session() -> None:
    client = TestClient(app)

    bootstrap = client.get("/api/v1/admin/content/bootstrap")
    create = client.post(
        "/api/v1/admin/content/chapters",
        json={
            "slug": "test-chapter",
            "title": "测试章节",
            "region": None,
            "sort_order": 99,
            "progress_key": "current",
            "progress_rank": 90,
            "status": "draft",
        },
    )

    assert bootstrap.status_code == 401
    assert create.status_code == 401


def test_admin_chapter_contract_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        AdminChapterWrite.model_validate(
            {
                "slug": "test-chapter",
                "title": "测试章节",
                "sort_order": 1,
                "progress_key": "start",
                "progress_rank": 0,
                "summary": "章节没有该字段",
            }
        )


def test_relationship_contract_rejects_self_reference() -> None:
    character_id = uuid.uuid4()
    with pytest.raises(ValidationError, match="关系起点和终点不能相同"):
        AdminRelationshipWrite.model_validate(
            {
                "source_character_id": character_id,
                "target_character_id": character_id,
                "relation_type": "ally",
                "label": "同一角色",
                "summary": "关系端点不能相同。",
                "spoiler_level": 0,
                "confidence": 1,
            }
        )


def test_archive_rejects_unknown_resource_before_query() -> None:
    with pytest.raises(HTTPException) as exc_info:
        archive_content(cast(Session, object()), "unknown", uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1",
    reason="requires the local PostgreSQL test database",
)
def test_admin_chapter_http_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    password = "integration-admin-password"
    monkeypatch.setattr(settings, "admin_password_hash", password_hasher.hash(password))
    slug = f"integration-{uuid.uuid4().hex}"
    with SessionLocal() as db:
        sort_order = (db.scalar(select(func.max(Chapter.sort_order))) or 0) + 100

    client = TestClient(app)
    login = client.post(
        "/api/v1/admin/session",
        headers={"Origin": settings.web_origin},
        json={"username": settings.admin_username, "password": password},
    )
    assert login.status_code == 200
    csrf = login.json()["data"]["csrf_token"]
    headers = {
        "Origin": settings.web_origin,
        "X-CSRF-Token": csrf,
    }
    payload = {
        "slug": slug,
        "title": "集成测试章节",
        "region": None,
        "sort_order": sort_order,
        "progress_key": "current",
        "progress_rank": 90,
        "status": "draft",
    }

    try:
        created = client.post(
            "/api/v1/admin/content/chapters",
            headers=headers,
            json=payload,
        )
        assert created.status_code == 201
        chapter_id = created.json()["data"]["id"]

        updated = client.patch(
            f"/api/v1/admin/content/chapters/{chapter_id}",
            headers=headers,
            json={**payload, "title": "已更新章节", "status": "published"},
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["title"] == "已更新章节"

        archived = client.delete(
            f"/api/v1/admin/content/chapters/{chapter_id}",
            headers=headers,
        )
        assert archived.status_code == 200
        assert archived.json()["data"]["status"] == "archived"

        bootstrap = client.get("/api/v1/admin/content/bootstrap")
        assert bootstrap.status_code == 200
        chapter = next(
            item for item in bootstrap.json()["data"]["chapters"] if item["id"] == chapter_id
        )
        assert chapter["status"] == "archived"
    finally:
        with SessionLocal() as db:
            db.execute(delete(Chapter).where(Chapter.slug == slug))
            db.commit()
