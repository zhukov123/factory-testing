from __future__ import annotations

import fnmatch
import math
import time
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import logging

from .config import RateLimitRule, RateLimitRuleBody, RateLimitRuleMatch, RateLimiterConfig
from .local_fallback import LocalFallback
from .redis_backend import RedisBackend, RedisBackendError


@dataclass
class RateLimitRequest:
    endpoint: str
    user_id: Optional[str] = None
    api_key: Optional[str] = None
    cost: int = 1
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class RateLimitDecision:
    allowed: bool
    remaining: int
    limit: int
    reset_at: int
    retry_after: Optional[int]
    rule: str
    backend: str


_FIXED_WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = math.floor(tonumber(ARGV[2]))
local cost = math.floor(tonumber(ARGV[3]))
if window <= 0 then
  window = 1
end
local now = redis.call("TIME")
local current = 0
if cost > 0 then
  current = redis.call("INCRBY", key, cost)
  if redis.call("TTL", key) == -1 then
    redis.call("EXPIRE", key, window)
  end
else
  current = tonumber(redis.call("GET", key) or 0)
end
if current == nil then
  current = 0
end
local ttl = redis.call("PTTL", key)
if ttl < 0 then
  ttl = window * 1000
end
local reset = tonumber(now[1]) + math.ceil(ttl / 1000)
local remaining = limit - current
if remaining < 0 then
  remaining = 0
end
local allowed = 0
if current <= limit then
  allowed = 1
end
return {allowed, remaining, reset}
"""


_SLIDING_WINDOW_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = math.floor(tonumber(ARGV[2]))
local cost = math.floor(tonumber(ARGV[3]))
if window <= 0 then
  window = 1
end
local now = redis.call("TIME")
local now_ms = now[1] * 1000 + math.floor(now[2] / 1000)
local window_ms = window * 1000
redis.call("ZREMRANGEBYSCORE", key, 0, now_ms - window_ms)
local current = redis.call("ZCARD", key)
local allowed = 0
if (current + cost) <= limit then
  if cost > 0 then
    for i = 1, cost do
      redis.call("ZADD", key, now_ms, tostring(now_ms) .. ":" .. tostring(i) .. ":" .. tostring(math.random()))
    end
  end
  allowed = 1
end
if cost > 0 then
  redis.call("PEXPIRE", key, window_ms)
end
local remaining = limit - current
if allowed == 1 then
  remaining = limit - (current + cost)
end
if remaining < 0 then
  remaining = 0
end
local reset = now[1] + window
local earliest = redis.call("ZRANGE", key, 0, 0, "WITHSCORES")
if #earliest == 2 then
  reset = math.floor((tonumber(earliest[2]) + window_ms) / 1000)
end
return {allowed, remaining, reset}
"""


_TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local cost = math.floor(tonumber(ARGV[3]))
local refill_rate = tonumber(ARGV[4])
local burst = tonumber(ARGV[5])
if burst <= 0 then
  burst = limit
end
if refill_rate <= 0 then
  refill_rate = 1
end
local now = redis.call("TIME")
local now_ts = tonumber(now[1]) + tonumber(now[2]) / 1000000
local stored = redis.call("HMGET", key, "tokens", "last_refill")
local tokens = tonumber(stored[1]) or burst
local last_refill = tonumber(stored[2]) or now_ts
local elapsed = now_ts - last_refill
local refill = elapsed * refill_rate
tokens = math.min(burst, tokens + refill)
local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end
redis.call("HMSET", key, "tokens", tokens, "last_refill", now_ts)
local ttl = math.ceil(burst / refill_rate) + 2
redis.call("EXPIRE", key, ttl)
local reset = math.floor(now_ts)
if allowed == 0 then
  local deficit = cost - tokens
  local wait = math.ceil(deficit / refill_rate)
  reset = reset + wait
end
if reset < now[1] then
  reset = now[1]
end
local remaining = math.floor(tokens)
if remaining < 0 then
  remaining = 0
end
return {allowed, remaining, reset}
"""


class FixedWindowLimiter:
    NAME = "fixed_window"

    def __init__(self, backend: RedisBackend):
        self._backend = backend

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: Optional[int],
        cost: int,
    ) -> Tuple[bool, int, int]:
        window_seconds = max(1, window_seconds or 60)
        raw = await self._backend.eval_script(
            self.NAME,
            _FIXED_WINDOW_SCRIPT,
            [key],
            [limit, window_seconds, cost],
        )
        return self._parse(raw)

    @staticmethod
    def _parse(result: List[object]) -> Tuple[bool, int, int]:
        allowed = bool(int(result[0]))
        remaining = max(0, int(result[1]))
        reset = int(result[2])
        return allowed, remaining, reset


class SlidingWindowLogLimiter:
    NAME = "sliding_window"

    def __init__(self, backend: RedisBackend):
        self._backend = backend

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: Optional[int],
        cost: int,
    ) -> Tuple[bool, int, int]:
        window_seconds = max(1, window_seconds or 60)
        raw = await self._backend.eval_script(
            self.NAME,
            _SLIDING_WINDOW_SCRIPT,
            [key],
            [limit, window_seconds, cost],
        )
        return self._parse(raw)

    @staticmethod
    def _parse(result: List[object]) -> Tuple[bool, int, int]:
        allowed = bool(int(result[0]))
        remaining = max(0, int(result[1]))
        reset = int(result[2])
        return allowed, remaining, reset


class TokenBucketLimiter:
    NAME = "token_bucket"

    def __init__(self, backend: RedisBackend):
        self._backend = backend

    async def check(
        self,
        key: str,
        limit: int,
        window_seconds: Optional[int],
        cost: int,
        refill_rate: float,
        burst_size: int,
    ) -> Tuple[bool, int, int]:
        effective_burst = burst_size or limit
        if effective_burst <= 0:
            raise ValueError("burst_size must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")
        raw = await self._backend.eval_script(
            self.NAME,
            _TOKEN_BUCKET_SCRIPT,
            [key],
            [limit, window_seconds or 0, cost, refill_rate, effective_burst],
        )
        return self._parse(raw)

    @staticmethod
    def _parse(result: List[object]) -> Tuple[bool, int, int]:
        allowed = bool(int(result[0]))
        remaining = max(0, int(result[1]))
        reset = int(result[2])
        return allowed, remaining, reset


class RateLimiter:
    _ALGORITHM_TAGS = {
        "fixed_window": "fw",
        "sliding_window": "sw",
        "token_bucket": "tb",
    }

    def __init__(
        self,
        config: RateLimiterConfig,
        backend: RedisBackend,
        logger: Optional[logging.Logger] = None,
    ):
        self._config = config
        self._backend = backend
        self.logger = logger or logging.getLogger(__name__)
        self._algo_instances = {
            "fixed_window": FixedWindowLimiter(backend),
            "sliding_window": SlidingWindowLogLimiter(backend),
            "token_bucket": TokenBucketLimiter(backend),
        }
        self._default_rule = RateLimitRule(
            name="default",
            match=RateLimitRuleMatch(),
            rate=config.default_rule,
        )
        self._local_fallback: Optional[LocalFallback] = None
        self._prepare_fallback()

    def _prepare_fallback(self) -> None:
        fallback_cfg = self._config.fallback
        if fallback_cfg.mode == "local":
            limit = fallback_cfg.local_limit or self._config.default_rule.limit
            window = (
                fallback_cfg.local_window_seconds
                or self._config.default_rule.window_seconds
                or 60
            )
            self._local_fallback = LocalFallback(limit=limit, window_seconds=window)
        else:
            self._local_fallback = None

    def reload_config(self, config: RateLimiterConfig) -> None:
        self._config = config
        self._default_rule = RateLimitRule(
            name="default",
            match=RateLimitRuleMatch(),
            rate=config.default_rule,
        )
        self._prepare_fallback()

    async def close(self) -> None:
        await self._backend.close()

    async def check_limit(self, request: RateLimitRequest) -> RateLimitDecision:
        return await self._process(request, consume=True)

    async def peek_limit(self, request: RateLimitRequest) -> RateLimitDecision:
        return await self._process(request, consume=False)

    async def _process(self, request: RateLimitRequest, consume: bool) -> RateLimitDecision:
        matched = self._match_rules(request)
        if not matched:
            matched = [self._default_rule]
        best: Optional[RateLimitDecision] = None
        for rule in matched:
            decision = await self._evaluate_rule(rule, request, consume)
            if not decision.allowed:
                return decision
            if best is None or decision.remaining < best.remaining:
                best = decision
        if best is None:
            best = self._make_allow_decision(self._default_rule, request)
        return best

    async def _evaluate_rule(
        self, rule: RateLimitRule, request: RateLimitRequest, consume: bool
    ) -> RateLimitDecision:
        rate = rule.rate
        algorithm = self._algo_instances.get(rate.algorithm)
        if algorithm is None:
            raise ValueError(f"unsupported algorithm {rate.algorithm}")
        limit_value = self._resolve_limit(rate)
        cost = max(0, request.cost)
        if not consume:
            cost = 0
        key = self._build_key(rule, request)
        try:
            if rate.algorithm == "token_bucket":
                refill_rate = rate.refill_rate
                burst = rate.burst_size or limit_value
                if refill_rate is None:
                    raise ValueError("token bucket requires refill_rate")
                allowed, remaining, reset_at = await algorithm.check(
                    key,
                    limit_value,
                    rate.window_seconds,
                    cost,
                    float(refill_rate),
                    burst,
                )
            else:
                allowed, remaining, reset_at = await algorithm.check(
                    key, limit_value, rate.window_seconds, cost
                )
            retry_after = None
            if not allowed:
                retry_after = max(0, int(reset_at - time.time()))
            return RateLimitDecision(
                allowed=allowed,
                remaining=remaining,
                limit=limit_value,
                reset_at=reset_at,
                retry_after=retry_after,
                rule=rule.name,
                backend="redis",
            )
        except (RedisBackendError, ValueError) as exc:
            self.logger.warning("redis backend unavailable, entering fallback", exc_info=exc)
            return self._apply_fallback(rule, key, limit_value, cost)

    def _apply_fallback(
        self, rule: RateLimitRule, key: str, limit_value: int, cost: int
    ) -> RateLimitDecision:
        now = int(time.time())
        fallback = self._config.fallback
        mode = fallback.mode
        if mode == "allow":
            return RateLimitDecision(
                allowed=True,
                remaining=limit_value,
                limit=limit_value,
                reset_at=now,
                retry_after=0,
                rule=rule.name,
                backend="redis",
            )
        if mode == "deny":
            retry_after = (rule.rate.window_seconds or 60)
            return RateLimitDecision(
                allowed=False,
                remaining=0,
                limit=limit_value,
                reset_at=now + retry_after,
                retry_after=retry_after,
                rule=rule.name,
                backend="redis",
            )
        if mode == "local" and self._local_fallback:
            data = self._local_fallback.check(key, cost)
            retry_after = data.get("retry_after")
            if retry_after is not None:
                retry_after = max(0, int(math.ceil(retry_after)))
            return RateLimitDecision(
                allowed=data["allowed"],
                remaining=data["remaining"],
                limit=data["limit"],
                reset_at=data["reset_at"],
                retry_after=retry_after,
                rule=rule.name,
                backend="local",
            )
        return RateLimitDecision(
            allowed=True,
            remaining=limit_value,
            limit=limit_value,
            reset_at=now,
            retry_after=0,
            rule=rule.name,
            backend="redis",
        )

    def _match_rules(self, request: RateLimitRequest) -> List[RateLimitRule]:
        matched: List[RateLimitRule] = []
        for rule in self._config.rules:
            if self._matches(rule.match, request):
                matched.append(rule)
        return matched

    @staticmethod
    def _matches(match: RateLimitRuleMatch, request: RateLimitRequest) -> bool:
        if match.endpoint:
            if not request.endpoint or not fnmatch.fnmatchcase(request.endpoint, match.endpoint):
                return False
        if match.user_id:
            if match.user_id == "*":
                if not request.user_id:
                    return False
            elif request.user_id != match.user_id:
                return False
        if match.api_key:
            if match.api_key == "*":
                if not request.api_key:
                    return False
            elif request.api_key != match.api_key:
                return False
        for key, value in match.labels.items():
            if request.labels.get(key) != value:
                return False
        return True

    def _build_key(self, rule: RateLimitRule, request: RateLimitRequest) -> str:
        prefix = self._config.redis.key_prefix.rstrip(":")
        tag = self._ALGORITHM_TAGS.get(rule.rate.algorithm, rule.rate.algorithm)
        parts = [prefix, tag, self._sanitize(rule.name)]
        if rule.match.user_id and request.user_id:
            parts.append(f"user:{self._sanitize(request.user_id)}")
        elif request.user_id:
            parts.append(f"user:{self._sanitize(request.user_id)}")
        if rule.match.api_key and request.api_key:
            parts.append(f"api:{self._sanitize(request.api_key)}")
        elif request.api_key:
            parts.append(f"api:{self._sanitize(request.api_key)}")
        if rule.match.endpoint and request.endpoint:
            parts.append(f"endpoint:{self._sanitize(request.endpoint)}")
        if rule.match.labels:
            for key in sorted(rule.match.labels):
                parts.append(f"label:{self._sanitize(key)}:{self._sanitize(rule.match.labels[key])}")
        return ":".join(parts)

    @staticmethod
    def _sanitize(value: Optional[str]) -> str:
        if not value:
            return ""
        return urllib.parse.quote_plus(value)

    @staticmethod
    def _resolve_limit(rate: RateLimitRuleBody) -> int:
        if rate.algorithm == "token_bucket":
            return rate.burst_size or rate.limit
        return rate.limit

    def _make_allow_decision(
        self, rule: RateLimitRule, request: RateLimitRequest
    ) -> RateLimitDecision:
        now = int(time.time())
        limit_value = self._resolve_limit(rule.rate)
        return RateLimitDecision(
            allowed=True,
            remaining=limit_value,
            limit=limit_value,
            reset_at=now,
            retry_after=0,
            rule=rule.name,
            backend="redis",
        )
