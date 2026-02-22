from __future__ import annotations

import threading
import time
from typing import Dict


class LocalFallback:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._buckets: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, cost: int = 1) -> Dict[str, float]:
        cost = max(0, cost)
        now = time.time()
        with self._lock:
            bucket = self._buckets.get(key)
            if not bucket or now >= bucket["reset_at"]:
                bucket = {"count": 0.0, "reset_at": now + self.window_seconds}
            projected = bucket["count"] + cost
            if projected > self.limit:
                retry = bucket["reset_at"] - now
                return {
                    "allowed": False,
                    "remaining": max(0, int(self.limit - bucket["count"])),
                    "limit": self.limit,
                    "reset_at": int(bucket["reset_at"]),
                    "retry_after": max(0.0, retry),
                }
            bucket["count"] = projected
            bucket["reset_at"] = bucket["reset_at"]
            self._buckets[key] = bucket
            remaining = max(0, int(self.limit - bucket["count"]))
            return {
                "allowed": True,
                "remaining": remaining,
                "limit": self.limit,
                "reset_at": int(bucket["reset_at"]),
                "retry_after": 0.0,
            }
