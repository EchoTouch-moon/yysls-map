import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Protocol

from sqlalchemy import delete, func, select

from app.core.config import settings
from app.db import SessionLocal
from app.models import RateLimitHit

MAX_KEY_LENGTH = 200


class RateLimiter(Protocol):
    def allow(self, key: str, *, now: datetime | None = None) -> bool: ...


@dataclass(frozen=True)
class SlidingWindowLimiter:
    limit: int
    window: timedelta
    _requests: dict[str, deque[datetime]] = field(default_factory=lambda: defaultdict(deque))
    _lock: Lock = field(default_factory=Lock)

    def allow(self, key: str, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        threshold = current - self.window
        with self._lock:
            attempts = self._requests[key]
            while attempts and attempts[0] <= threshold:
                attempts.popleft()
            if len(attempts) >= self.limit:
                return False
            attempts.append(current)
            return True


class DatabaseSlidingWindowLimiter:
    """Sliding-window limiter backed by PostgreSQL.

    State survives deploys and restarts and is shared across API instances.
    A per-key transaction-level advisory lock serializes concurrent checks so
    the count-then-insert step cannot over-admit under load.
    """

    def __init__(self, limit: int, window: timedelta) -> None:
        self.limit = limit
        self.window = window
        self._sweep_lock = Lock()
        self._last_sweep: datetime | None = None

    def allow(self, key: str, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        threshold = current - self.window
        bucket = key[:MAX_KEY_LENGTH]
        self._sweep_if_due(current=current, threshold=threshold)
        with SessionLocal() as db:
            db.execute(select(func.pg_advisory_xact_lock(func.hashtext(bucket))))
            db.execute(
                delete(RateLimitHit).where(
                    RateLimitHit.bucket_key == bucket,
                    RateLimitHit.created_at <= threshold,
                )
            )
            recent_count = db.scalar(
                select(func.count())
                .select_from(RateLimitHit)
                .where(
                    RateLimitHit.bucket_key == bucket,
                    RateLimitHit.created_at > threshold,
                )
            )
            if (recent_count or 0) >= self.limit:
                db.commit()
                return False
            db.add(RateLimitHit(id=uuid.uuid4(), bucket_key=bucket, created_at=current))
            db.commit()
            return True

    def _sweep_if_due(self, *, current: datetime, threshold: datetime) -> None:
        with self._sweep_lock:
            if self._last_sweep is not None and current - self._last_sweep < self.window:
                return
        with SessionLocal() as db:
            db.execute(delete(RateLimitHit).where(RateLimitHit.created_at <= threshold))
            db.commit()
        with self._sweep_lock:
            self._last_sweep = current


def build_limiter(limit: int, window: timedelta) -> RateLimiter:
    if settings.rate_limit_backend == "memory":
        return SlidingWindowLimiter(limit=limit, window=window)
    return DatabaseSlidingWindowLimiter(limit=limit, window=window)


submission_limiter: RateLimiter = build_limiter(limit=5, window=timedelta(hours=1))
login_limiter: RateLimiter = build_limiter(limit=10, window=timedelta(minutes=15))
