from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .limiter import RateLimitDecision, RateLimitRequest, RateLimiter


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        limiter: RateLimiter,
        user_header: str = "x-user-id",
        api_key_header: str = "x-api-key",
        tier_header: str = "x-tier",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter
        self.user_header = user_header.lower()
        self.api_key_header = api_key_header.lower()
        self.tier_header = tier_header.lower()
        self.logger = logger or logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next):
        payload = self._build_request(request)
        try:
            decision = await self._limiter.check_limit(payload)
        except Exception as exc:
            self.logger.warning("rate limiter check failed", exc_info=exc)
            return JSONResponse(
                content={"detail": "rate limiter unavailable"},
                status_code=503,
            )
        headers = self._render_headers(decision)
        if not decision.allowed:
            return JSONResponse(
                content={
                    "detail": "rate limit exceeded",
                    "rule": decision.rule,
                },
                status_code=429,
                headers=headers,
            )
        response = await call_next(request)
        response.headers.update(headers)
        return response

    def _build_request(self, request: Request) -> RateLimitRequest:
        endpoint = f"{request.method} {request.url.path}"
        user_id = request.headers.get(self.user_header)
        api_key = request.headers.get(self.api_key_header)
        labels = {}
        tier = request.headers.get(self.tier_header)
        if tier:
            labels["tier"] = tier
        cost_header = request.headers.get("x-rate-cost")
        cost = 1
        if cost_header:
            try:
                cost = max(1, int(cost_header))
            except ValueError:
                cost = 1
        return RateLimitRequest(
            endpoint=endpoint,
            user_id=user_id,
            api_key=api_key,
            cost=cost,
            labels=labels,
        )

    @staticmethod
    def _render_headers(decision: RateLimitDecision) -> dict:
        headers = {
            "X-RateLimit-Limit": str(decision.limit),
            "X-RateLimit-Remaining": str(decision.remaining),
            "X-RateLimit-Reset": str(decision.reset_at),
            "X-RateLimit-Source": decision.backend,
        }
        if decision.retry_after is not None:
            headers["Retry-After"] = str(decision.retry_after)
        return headers
