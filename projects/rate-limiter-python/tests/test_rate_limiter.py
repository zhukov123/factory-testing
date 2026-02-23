from __future__ import annotations

import time

import pytest

from rate_limiter import FixedWindowRateLimiter


def test_under_limit_allows_requests() -> None:
    limiter = FixedWindowRateLimiter(limit=3, window_size_ms=1_000)
    timestamp = 1_000

    assert limiter.allow("alice", timestamp) is True
    assert limiter.allow("alice", timestamp + 10) is True
    assert limiter.allow("alice", timestamp + 20) is True
    assert limiter.allow("alice", timestamp + 30) is False


def test_over_limit_blocks_request() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window_size_ms=1_000)
    timestamp = 5_000

    assert limiter.allow("bob", timestamp) is True
    assert limiter.allow("bob", timestamp + 1) is True
    assert limiter.allow("bob", timestamp + 2) is False


def test_window_rolls_over_on_boundary() -> None:
    limiter = FixedWindowRateLimiter(limit=2, window_size_ms=1_000)
    initial = 10_000

    assert limiter.allow("carol", initial) is True
    assert limiter.allow("carol", initial + 1) is True
    # Next window should clear the counter
    next_window = initial + limiter.window_size_ms
    assert limiter.allow("carol", next_window) is True


def test_multiple_users_independent_counters() -> None:
    limiter = FixedWindowRateLimiter(limit=1, window_size_ms=1_000)
    base_ts = 20_000

    assert limiter.allow("alice", base_ts) is True
    assert limiter.allow("bob", base_ts) is True
    assert limiter.allow("alice", base_ts + 1) is False
    assert limiter.allow("bob", base_ts + 1) is False
