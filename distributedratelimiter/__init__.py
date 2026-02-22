"""
Distributed Rate Limiter - Package exports.
"""

from .limiter import (
    RateLimiter,
    FixedWindowLimiter,
    SlidingWindowLogLimiter,
    TokenBucketLimiter,
    RateLimitResult
)

from .redis_backend import (
    RedisRateLimiter,
    RedisBackend
)

from .config import (
    Config,
    RedisConfig,
    RateLimitRule,
    MiddlewareConfig,
    FallbackConfig,
    RateLimitAlgorithm,
    load_config,
    get_config_for_path
)

from .middleware import (
    RateLimitMiddleware,
    RateLimitHeaders,
    create_rate_limit_middleware,
    get_rate_limit_info
)

from .local_fallback import (
    LocalFallbackLimiter,
    LocalFallbackManager,
    get_fallback_manager
)

__all__ = [
    # Main classes
    "RateLimiter",
    "FixedWindowLimiter",
    "SlidingWindowLogLimiter",
    "TokenBucketLimiter",
    "RateLimitResult",
    # Redis backend
    "RedisRateLimiter",
    "RedisBackend",
    # Configuration
    "Config",
    "RedisConfig",
    "RateLimitRule",
    "MiddlewareConfig",
    "FallbackConfig",
    "RateLimitAlgorithm",
    "load_config",
    "get_config_for_path",
    # Middleware
    "RateLimitMiddleware",
    "RateLimitHeaders",
    "create_rate_limit_middleware",
    "get_rate_limit_info",
    # Fallback
    "LocalFallbackLimiter",
    "LocalFallbackManager",
    "get_fallback_manager",
]

__version__ = "1.0.0"
__author__ = "Senior Engineer"
