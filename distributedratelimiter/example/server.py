"""
Example FastAPI Server with Distributed Rate Limiter

This example demonstrates how to use the distributed rate limiter
with FastAPI, including Redis backend and fallback support.

Run with:
    uvicorn example.server:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from distributedratelimiter import (
    create_rate_limiter,
    RateLimitMiddleware,
    setup_middleware,
    RateLimiter,
    RedisConfig,
    RedisBackend,
)
from distributedratelimiter.config import ConfigLoader, MiddlewareConfig


# Create FastAPI application
app = FastAPI(
    title="Distributed Rate Limiter Example",
    description="Example server demonstrating distributed rate limiting",
    version="1.0.0"
)


# Configure rate limiter
async def configure_rate_limiter():
    """Configure rate limiter with Redis support."""
    # Try to connect to Redis
    redis_config = RedisConfig(
        host="localhost",
        port=6379,
        db=0,
    )
    redis_backend = RedisBackend(redis_config)
    
    try:
        if await redis_backend.is_available():
            print("✓ Connected to Redis")
            rate_limiter = RateLimiter(
                algorithm="token_bucket",
                max_requests=100,
                window_seconds=60.0,
                backend=redis_backend
            )
            return rate_limiter, redis_backend
        else:
            print("⚠ Redis unavailable, using in-memory fallback")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}, using in-memory fallback")
    
    # Fallback to in-memory
    rate_limiter = RateLimiter(
        algorithm="token_bucket",
        max_requests=100,
        window_seconds=60.0,
        backend=None
    )
    return rate_limiter, redis_backend


# Global rate limiter instances
rate_limiter: RateLimiter = None
redis_backend: RedisBackend = None


@app.on_event("startup")
async def startup_event():
    """Initialize rate limiter on startup."""
    global rate_limiter, redis_backend
    
    rate_limiter, redis_backend = await configure_rate_limiter()
    
    # Set up rate limiting middleware
    middleware = RateLimitMiddleware(
        app,
        rate_limiter=rate_limiter,
        skip_paths=["/health", "/metrics"],
        excluded_paths=["/docs", "/openapi.json"]
    )
    app.user_middleware = [middleware] + [
        m for m in app.user_middleware
        if not isinstance(m, RateLimitMiddleware)
    ]
    
    print("✓ Rate limiter initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global redis_backend
    
    if redis_backend:
        await redis_backend.close()
        print("✓ Redis connection closed")


# Health check endpoint (excluded from rate limiting)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rate_limiter": {
            "algorithm": rate_limiter.algorithm if rate_limiter else "none",
            "max_requests": rate_limiter.max_requests if rate_limiter else 0,
        }
    }


# Metrics endpoint (excluded from rate limiting)
@app.get("/metrics")
async def metrics():
    """Rate limiter metrics."""
    return {
        "redis_available": False,  # Would need to track this
        "fallback_active": rate_limiter.backend is None if rate_limiter else True,
    }


# Rate-limited endpoints
@app.get("/api/limited")
async def rate_limited_endpoint(request: Request):
    """
    This endpoint is rate limited by the middleware.
    
    Returns the current rate limit status in the response headers.
    """
    return {
        "message": "This endpoint is rate limited",
        "client_ip": request.client.host if request.client else "unknown",
    }


@app.get("/api/limited/{resource_id}")
async def rate_limited_resource(
    request: Request,
    resource_id: str,
    user_id: str = None
):
    """
    Rate-limited endpoint with path parameter.
    
    Rate limits are applied per resource.
    """
    return {
        "message": f"Resource {resource_id} accessed",
        "resource_id": resource_id,
        "user_id": user_id,
        "client_ip": request.client.host if request.client else "unknown",
    }


@app.post("/api/limited")
async def rate_limited_post(
    request: Request,
    data: dict
):
    """
    Rate-limited POST endpoint.
    
    Demonstrates rate limiting for POST requests.
    """
    return {
        "message": "POST request processed",
        "data_received": len(str(data)) < 1000,  # Truncate for logging
        "client_ip": request.client.host if request.client else "unknown",
    }


# Custom rate-limited endpoint with decorator
from distributedratelimiter.middleware import rate_limit

@app.get("/api/decorated")
@rate_limit(max_requests=5, window_seconds=10.0, key_source="client_ip")
async def decorated_endpoint(request: Request):
    """
    This endpoint uses the @rate_limit decorator.
    
    Different rate limit settings from the middleware.
    """
    return {
        "message": "Decorated rate-limited endpoint",
        "rate_limit": "5 requests per 10 seconds",
    }


# Manual rate limiting example
@app.get("/api/manual-rate-limit")
async def manual_rate_limit(request: Request):
    """
    This endpoint demonstrates manual rate limiting.
    
    Shows how to check rate limits programmatically.
    """
    global rate_limiter
    
    if rate_limiter:
        # Manual rate limit check
        key = f"ip:{request.client.host}" if request.client else "unknown"
        result = await rate_limiter.acquire(key, endpoint="/api/manual-rate-limit")
        
        if not result.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": result.retry_after,
                },
                headers={
                    "Retry-After": str(int(result.retry_after)),
                }
            )
        
        return {
            "message": "Manual rate limiting example",
            "allowed": True,
            "remaining": result.remaining,
            "reset_at": result.reset_at,
        }
    
    return {"message": "Rate limiter not available"}


# Custom error handler for rate limiting
@app.exception_handler(429)
async def rate_limit_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": exc.detail.get("message", "Rate limit exceeded"),
            "retry_after": exc.detail.get("retry_after", 0),
        },
        headers={
            "Retry-After": str(exc.detail.get("retry_after", 0)),
            "X-RateLimit-Remaining": "0",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "example.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
