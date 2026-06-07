from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock


@dataclass
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


submission_limiter = SlidingWindowLimiter(limit=5, window=timedelta(hours=1))
login_limiter = SlidingWindowLimiter(limit=10, window=timedelta(minutes=15))

