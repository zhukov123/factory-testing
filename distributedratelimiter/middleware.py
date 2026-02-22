"""
FastAPI middleware for rate limiting.
"""

import time
import re
from typing import Callable, Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .limiter import RateLimiter, RateLimitResult
from .redis_backend import RedisRateLimiter, RedisBackend
from .local_fallback import LocalFallbackLimiter
from .config import Config, RateLimitRule, load_config


@dataclass
class RateLimitHeaders:
    """Rate limit headers to be added to response."""
    limit: int
    remaining: int
    reset_at: float
    retry_after: Optional[float] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to header dictionary."""
        headers = {
            f"{self._prefix}-Limit": str(self.limit),
            f"{self._prefix}-Remaining": str(self.remaining),
            f"{self._prefix}-Reset": str(int(self.reset_at))
        }
        if self.retry_after is not None:
            headers[f"{self._prefix}-Retry-After"] = str(round(self.retry_after, 2))
        return headers
    
    @property
    def _prefix(self) -> str:
        return "X-RateLimit"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for distributed rate limiting.
    
    Supports Redis backend with local fallback.
    """
    
    def __init__(
        self,
        config: Config,
        limiter: Optional[RateLimiter] = None,
        redis_backend: Optional[RedisBackend] = None,
        fallback: Optional[LocalFallbackLimiter] = None
    ):
        """
        Initialize the middleware.
        
        Args:
            config: Configuration object
            limiter: Rate limiter instance (optional, created from config if not provided)
            redis_backend: Redis backend instance (optional)
            fallback: Fallback limiter instance (optional)
        """
        super().__init__(self._dispatch)
        self.config = config
        self.redis_backend = redis_backend
        self.fallback = fallback
        self._limiter = limiter
        
        # Compile skip path patterns
        self._skip_patterns = [
            re.compile(pattern) for pattern in self.config.middleware.skip_paths
        ]
    
    async def _dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main dispatch method."""
        # Check if should skip
        if self._should_skip(request):
            return await call_next(request)
        
        # Get rate limit rule
        rule = self._get_rule(request)
        if not rule:
            return await call_next(request)
        
        # Get identifier
        identifier = self._get_identifier(request, rule)
        
        # Check rate limit
        result = await self._check_rate_limit(identifier, rule)
        
        # Build response
        response = await call_next(request)
        self._add_headers(response, result, rule)
        
        # Add rate limit info to response body if configured
        if self.config.middleware.include_stats_in_response:
            response.headers["X-RateLimit-Info"] = "stats-included"
        
        return response
    
    def _should_skip(self, request: Request) -> bool:
        """Check if request should be skipped."""
        # Check skip patterns
        for pattern in self._skip_patterns:
            if pattern.match(request.url.path):
                return True
        return False
    
    def _get_rule(self, request: Request) -> Optional[RateLimitRule]:
        """Get rate limit rule for request."""
        # Try to find a matching rule
        rule = self.config.rules
        for r in self.config.rules:
            if (request.url.path == r.path or 
                request.url.path.startswith(r.path)):
                if request.method.upper() in [m.upper() for m in r.methods]:
                    return r
        
        # Use default rule if configured
        if self.config.middleware.default_rule:
            return RateLimitRule.from_dict(self.config.middleware.default_rule)
        
        return None
    
    def _get_identifier(self, request: Request, rule: RateLimitRule) -> str:
        """Get identifier for rate limiting."""
        if rule.identifier == "client_ip":
            return request.client.host if request.client else "unknown"
        elif rule.identifier == "user_id":
            return str(request.state.user.id) if hasattr(request.state, "user") else "anonymous"
        elif rule.identifier == "api_key":
            return request.headers.get("X-API-Key", "anonymous")
        elif rule.identifier == "header":
            return request.headers.get("X-Client-Id", "anonymous")
        else:
            # Custom identifier function
            return rule.identifier
    
    async def _get_limiter(self) -> RateLimiter:
        """Get or create rate limiter instance."""
        if self._limiter is None:
            if self.config.redis:
                if self.redis_backend is None:
                    self.redis_backend = RedisBackend(
                        redis_url=self.config.redis.to_url(),
                        pool_size=self.config.redis.connection_pool_size,
                        timeout=self.config.redis.timeout
                    )
                self._limiter = RedisRateLimiter(
                    redis_url=self.config.redis.to_url(),
                    algorithm=self.config.fallback.algorithm
                )
            else:
                self._limiter = LocalFallbackLimiter(
                    algorithm=self.config.fallback.algorithm
                )
        return self._limiter
    
    async def _check_rate_limit(self, identifier: str, rule: RateLimitRule) -> RateLimitResult:
        """Check rate limit for identifier."""
        limiter = await self._get_limiter()
        
        try:
            result = await limiter.is_allowed(
                identifier=identifier,
                limit=rule.limit,
                window=rule.window
            )
            
            # Update fallback if using Redis
            if isinstance(limiter, RedisRateLimiter) and self.config.fallback.enabled:
                if not result.allowed and self.fallback:
                    await self.fallback.record_request(identifier, rule.window)
            
            return result
            
        except Exception as e:
            # Fall back to local limiter on error
            if self.config.fallback.enabled and self.fallback:
                return await self.fallback.check_rate_limit(
                    identifier=identifier,
                    limit=rule.limit,
                    window=rule.window
                )
            raise
    
    def _add_headers(
        self,
        response: Response,
        result: RateLimitResult,
        rule: RateLimitRule
    ) -> None:
        """Add rate limit headers to response."""
        headers = RateLimitHeaders(
            limit=rule.limit,
            remaining=result.remaining,
            reset_at=result.reset_at,
            retry_after=result.retry_after
        )
        
        for key, value in headers.to_dict().items():
            response.headers[key] = value
    
    async def close(self) -> None:
        """Cleanup resources."""
        if self.redis_backend:
            await self.redis_backend.close()


def create_rate_limit_middleware(
    config: Optional[Config] = None,
    config_path: Optional[str] = None
) -> Callable:
    """
    Factory function to create rate limit middleware.
    
    Args:
        config: Config object (optional)
        config_path: Path to config file (optional)
        
    Returns:
        Middleware class
    """
    if config is None:
        config = load_config(config_path)
    
    # Create fallback limiter
    fallback = None
    if config.fallback.enabled:
        fallback = LocalFallbackLimiter(
            algorithm=config.fallback.algorithm,
            max_requests=config.fallback.max_requests,
            window=config.fallback.window
        )
    
    # Create middleware class with dependencies
    class RateLimitMiddlewareFactory(RateLimitMiddleware):
        def __init__(self, *args, **kwargs):
            super().__init__(
                config=config,
                fallback=fallback,
                *args,
                **kwargs
            )
    
    return RateLimitMiddlewareFactory


# Shortcut for easy usage
RateLimiterMiddleware = create_rate_limit_middleware


async def get_rate_limit_info(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get rate limit info from request headers.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary with rate limit info or None
    """
    headers = {}
    for key in request.headers.keys():
        if key.startswith("X-RateLimit"):
            headers[key] = request.headers[key]
    
    if not headers:
        return None
    
    return headers
