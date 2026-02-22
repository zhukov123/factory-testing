from __future__ import annotations

import logging
import textwrap
from typing import Dict

import uvicorn
import yaml
from fastapi import FastAPI

from distributedratelimiter.config import load_config
from distributedratelimiter.limiter import RateLimiter
from distributedratelimiter.middleware import RateLimiterMiddleware
from distributedratelimiter.redis_backend import RedisBackend


DEFAULT_CONFIG = textwrap.dedent(
    """
    redis:
      url: "redis://localhost:6379/0"
      keyPrefix: "rl:"
      connectTimeoutMs: 50
      commandTimeoutMs: 50
      poolSize: 10
    defaultRule:
      algorithm: fixed_window
      limit: 20
      windowSeconds: 60
    rules:
      - name: "auth-write"
        match:
          endpoint: "POST /api/*"
          apiKey: "*"
        rate:
          algorithm: sliding_window
          limit: 5
          windowSeconds: 10
      - name: "premium-users"
        match:
          endpoint: "GET /api/orders"
          userId: "*"
          labels:
            tier: "premium"
        rate:
          algorithm: token_bucket
          limit: 100
          refillRate: 5
          burstSize: 20
    fallback:
      mode: local
      localLimit: 10
      localWindowSeconds: 60
    observability:
      metricsEnabled: false
    """
)

config = load_config(yaml.safe_load(DEFAULT_CONFIG))
backend = RedisBackend(config.redis, logger=logging.getLogger("distributedratelimiter"))
limiter = RateLimiter(config, backend)

app = FastAPI(title="Distributed Rate Limiter Demo")
app.add_middleware(RateLimiterMiddleware, limiter=limiter)


@app.get("/api/ping")
async def ping() -> Dict[str, str]:
    return {"message": "pong"}


@app.post("/api/orders")
async def create_order() -> Dict[str, str]:
    return {"status": "queued"}


@app.get("/api/orders")
async def list_orders() -> Dict[str, str]:
    return {"orders": "placeholder"}


@app.on_event("shutdown")
async def shutdown() -> None:
    await limiter.close()


if __name__ == "__main__":
    uvicorn.run("example.server:app", host="0.0.0.0", port=8000, reload=False)
