"""
Example FastAPI server using the distributed rate limiter.
"""

import asyncio
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from distributedratelimiter import (
    Config,
    load_config,
    create_rate_limit_middleware,
    RateLimitMiddleware
)


# Sample configuration (in practice, this would be in a YAML file)
CONFIG = Config(
    rules=[
        {
            "path": "/api/public",
            "methods": ["GET"],
            "limit": 100,
            "window": 60.0,
            "algorithm": "token_bucket"
        },
        {
            "path": "/api/private",
            "methods": ["GET", "POST"],
            "limit": 20,
            "window": 60.0,
            "algorithm": "sliding_window_log"
        },
        {
            "path": "/api/admin",
            "methods": ["GET", "POST", "DELETE"],
            "limit": 5,
            "window": 60.0,
            "algorithm": "fixed_window"
        }
    ],
    middleware={
        "enabled": True,
        "header_prefix": "X-RateLimit",
        "include_stats_in_response": True,
        "skip_paths": ["/health", "/docs", "/openapi.json"]
    },
    fallback={
        "enabled": True,
        "algorithm": "token_bucket",
        "max_requests": 100,
        "window": 60.0
    }
)


# Create FastAPI app
app = FastAPI(
    title="Distributed Rate Limiter Example",
    description="Example API with distributed rate limiting",
    version="1.0.0"
)


# Add rate limiting middleware
RateLimitMiddlewareFactory = create_rate_limit_middleware(config=CONFIG)
app.add_middleware(RateLimitMiddlewareFactory)


# Health check endpoint (skipped from rate limiting)
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Distributed Rate Limiter Example API"}


# Public endpoint (100 requests/minute)
class PublicResponse(BaseModel):
    message: str
    endpoint: str
    timestamp: float


@app.get("/api/public")
async def public_endpoint(request: Request) -> PublicResponse:
    """Public endpoint with rate limit of 100 requests per minute."""
    return PublicResponse(
        message="This is a public endpoint",
        endpoint="api/public",
        timestamp=asyncio.get_event_loop().time()
    )


# Private endpoint (20 requests/minute)
class PrivateResponse(BaseModel):
    message: str
    endpoint: str
    user_id: Optional[str]
    timestamp: float


@app.get("/api/private")
async def private_endpoint(
    request: Request,
    user_id: Optional[str] = None
) -> PrivateResponse:
    """Private endpoint with rate limit of 20 requests per minute."""
    return PrivateResponse(
        message="This is a private endpoint",
        endpoint="api/private",
        user_id=user_id,
        timestamp=asyncio.get_event_loop().time()
    )


@app.post("/api/private")
async def private_post_endpoint(
    request: Request,
    data: dict
) -> PrivateResponse:
    """Private POST endpoint with rate limit of 20 requests per minute."""
    return PrivateResponse(
        message="Private POST successful",
        endpoint="api/private",
        user_id=data.get("user_id"),
        timestamp=asyncio.get_event_loop().time()
    )


# Admin endpoint (5 requests/minute)
class AdminResponse(BaseModel):
    message: str
    endpoint: str
    timestamp: float


@app.get("/api/admin")
async def admin_endpoint(request: Request) -> AdminResponse:
    """Admin endpoint with rate limit of 5 requests per minute."""
    return AdminResponse(
        message="This is an admin endpoint",
        endpoint="api/admin",
        timestamp=asyncio.get_event_loop().time()
    )


@app.post("/api/admin")
async def admin_post_endpoint(request: Request) -> AdminResponse:
    """Admin POST endpoint with rate limit of 5 requests per minute."""
    return AdminResponse(
        message="Admin POST successful",
        endpoint="api/admin",
        timestamp=asyncio.get_event_loop().time()
    )


@app.delete("/api/admin/{item_id}")
async def admin_delete_endpoint(
    request: Request,
    item_id: str
) -> AdminResponse:
    """Admin DELETE endpoint with rate limit of 5 requests per minute."""
    return AdminResponse(
        message=f"Item {item_id} deleted",
        endpoint=f"api/admin/{item_id}",
        timestamp=asyncio.get_event_loop().time()
    )


# Rate limit info endpoint
@app.get("/api/rate-limit-info")
async def rate_limit_info(request: Request) -> dict:
    """Get rate limit information for current request."""
    headers = {}
    for key in request.headers.keys():
        if key.startswith("X-RateLimit"):
            headers[key] = request.headers[key]
    
    return {
        "client_ip": request.client.host if request.client else "unknown",
        "path": request.url.path,
        "method": request.method,
        "rate_limit_headers": headers
    }


# Custom exception handler for rate limiting
@app.exception_handler(HTTPException)
async def rate_limit_exception_handler(request: Request, exc: HTTPException):
    """Handle rate limit exceptions."""
    if exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": exc.detail,
                "retry_after": request.headers.get("X-RateLimit-Retry-After")
            }
        )
    return exc


# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "example.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
