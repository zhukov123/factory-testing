"""Fixed-window rate limiter implementation for T5."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Dict


@dataclass
class _UserWindow:
    """Tracks the current window start and counter for a user."""

    window_start: int
    count: int = 0


class FixedWindowRateLimiter:
    """A thread-safe fixed-window rate limiter with per-user buckets."""

    def __init__(self, limit: int, window_size_ms: int = 60_000) -> None:
        if limit <= 0:
            raise ValueError("limit must be positive")
        if window_size_ms <= 0:
            raise ValueError("window_size_ms must be positive")

        self.limit = limit
        self.window_size_ms = window_size_ms
        self._lock = threading.Lock()
        self._buckets: Dict[str, _UserWindow] = {}

    def _current_window_start(self, timestamp: int) -> int:
        """Return the floor-aligned start for the current window."""
        return (timestamp // self.window_size_ms) * self.window_size_ms

    def allow(self, user_id: str, timestamp: int) -> bool:
        """Return True if the request is permitted, False otherwise."""
        if timestamp < 0:
            raise ValueError("timestamp must be non-negative")

        window_start = self._current_window_start(timestamp)

        with self._lock:
            bucket = self._buckets.get(user_id)
            if bucket is None or bucket.window_start != window_start:
                bucket = _UserWindow(window_start=window_start, count=0)
                self._buckets[user_id] = bucket

            if bucket.count < self.limit:
                bucket.count += 1
                return True

            return False

    def reset(self) -> None:
        """Clear all user buckets (useful for tests)."""
        with self._lock:
            self._buckets.clear()
