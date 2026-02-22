"""
Redis Backend for Distributed Rate Limiting.
"""

import asyncio
import time
import json
import redis
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from .limiter import RateLimiter, RateLimitResult, FixedWindowLimiter, SlidingWindowLogLimiter, TokenBucketLimiter


class RedisRateLimiter(RateLimiter):
    """
    Redis-backed Rate Limiter for distributed systems.
    
    Uses Redis for atomic operations and shared state across multiple instances.
    Supports all limiter algorithms through Lua scripts for atomicity.
    """
    
    # Lua script for fixed window rate limiting
    FIXED_WINDOW_SCRIPT = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])
    local window_start = tonumber(ARGV[4])
    local window_key = key .. ":" .. window_start
    
    -- Get current count
    local count = redis.call('GET', window_key)
    count = count and tonumber(count) or 0
    
    -- Check if rate limited
    if count >= limit then
        local reset_at = window_start + window
        local retry_after = reset_at - current_time
        return {0, limit - count, reset_at, retry_after}
    end
    
    -- Increment count
    local new_count = redis.call('INCR', window_key)
    redis.call('EXPIRE', window_key, math.ceil(window) + 1)
    
    return {1, limit - new_count, window_start + window, nil}
    """
    
    # Lua script for sliding window log rate limiting
    SLIDING_WINDOW_SCRIPT = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])
    local window_start = current_time - window
    
    -- Remove expired timestamps
    redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
    
    -- Get current count
    local count = redis.call('ZCARD', key)
    
    -- Check if rate limited
    if count >= limit then
        local oldest = redis.call('ZMIN', key)
        local reset_at = tonumber(oldest) + window
        local retry_after = reset_at - current_time
        return {0, 0, reset_at, retry_after}
    end
    
    -- Add new timestamp
    redis.call('ZADD', key, current_time, current_time .. '_' .. math.random())
    redis.call('EXPIRE', key, math.ceil(window) + 1)
    
    return {1, limit - count - 1, current_time + window, nil}
    """
    
    # Lua script for token bucket rate limiting
    TOKEN_BUCKET_SCRIPT = """
    local key = KEYS[1]
    local limit = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local current_time = tonumber(ARGV[3])
    
    -- Get current bucket state
    local bucket = redis.call('HGETALL', key)
    local tokens = limit
    local last_update = current_time
    
    if #bucket > 0 then
        for i = 1, #bucket, 2 do
            if bucket[i] == 'tokens' then
                tokens = tonumber(bucket[i+1])
            elseif bucket[i] == 'last_update' then
                last_update = tonumber(bucket[i+1])
            end
        end
    end
    
    -- Calculate tokens to add
    local elapsed = current_time - last_update
    local tokens_to_add = elapsed * (limit / window)
    tokens = math.min(limit, tokens + tokens_to_add)
    
    -- Check if we have enough tokens
    if tokens < 1 then
        local tokens_needed = 1 - tokens
        local retry_after = tokens_needed / (limit / window)
        local reset_at = current_time + retry_after
        return {0, 0, reset_at, retry_after}
    end
    
    -- Consume a token
    tokens = tokens - 1
    redis.call('HSET', key, 'tokens', tokens, 'last_update', current_time)
    redis.call('EXPIRE', key, math.ceil(window) + 1)
    
    return {1, math.floor(tokens), current_time + window, nil}
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        algorithm: str = "token_bucket",
        connection_pool: Optional[redis.ConnectionPool] = None
    ):
        """
        Initialize Redis rate limiter.
        
        Args:
            redis_url: Redis connection URL
            algorithm: One of 'fixed_window', 'sliding_window_log', 'token_bucket'
            connection_pool: Optional Redis connection pool
        """
        self._redis_url = redis_url
        self._algorithm = algorithm
        
        if connection_pool:
            self._redis = redis.Redis(connection_pool=connection_pool)
        else:
            self._redis = redis.from_url(redis_url)
        
        # Register Lua scripts
        self._scripts = {
            'fixed_window': self._redis.register_script(self.FIXED_WINDOW_SCRIPT),
            'sliding_window_log': self._redis.register_script(self.SLIDING_WINDOW_SCRIPT),
            'token_bucket': self._redis.register_script(self.TOKEN_BUCKET_SCRIPT)
        }
        
        self._script = self._scripts[algorithm]
    
    def _make_key(self, identifier: str) -> str:
        """Generate Redis key for an identifier."""
        return f"ratelimit:{self._algorithm}:{identifier}"
    
    async def is_allowed(self, identifier: str, limit: int, window: float) -> RateLimitResult:
        """
        Check if a request is allowed using Redis backend.
        
        Args:
            identifier: Unique identifier for the rate limit subject
            limit: Maximum number of requests in the window
            window: Window size in seconds
            
        Returns:
            RateLimitResult with allowed status and metadata
        """
        key = self._make_key(identifier)
        current_time = time.time()
        window_start = (current_time // window) * window if self._algorithm == 'fixed_window' else current_time - window
        
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            self._script,
            keys=[key],
            args=[limit, window, current_time, window_start]
        )
        
        allowed = bool(result[0])
        remaining = int(result[1])
        reset_at = float(result[2])
        retry_after = float(result[3]) if result[3] else None
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=retry_after
        )
    
    async def get_stats(self, identifier: str, limit: int, window: float) -> RateLimitResult:
        """
        Get current rate limit stats from Redis.
        
        Args:
            identifier: Unique identifier for the rate limit subject
            limit: Maximum number of requests in the window
            window: Window size in seconds
            
        Returns:
            RateLimitResult with current stats
        """
        key = self._make_key(identifier)
        current_time = time.time()
        
        if self._algorithm == 'fixed_window':
            window_start = (current_time // window) * window
            window_key = f"{key}:{window_start}"
            
            count = await asyncio.get_event_loop().run_in_executor(
                None,
                self._redis.get,
                window_key
            )
            count = int(count) if count else 0
            
        elif self._algorithm == 'sliding_window_log':
            window_start = current_time - window
            count = await asyncio.get_event_loop().run_in_executor(
                None,
                self._redis.zcount,
                key, window_start, '+inf'
            )
            
        else:  # token_bucket
            bucket = await asyncio.get_event_loop().run_in_executor(
                None,
                self._redis.hgetall,
                key
            )
            if bucket:
                tokens = float(bucket.get(b'tokens', limit))
                last_update = float(bucket.get(b'last_update', current_time))
                elapsed = current_time - last_update
                tokens_to_add = elapsed * (limit / window)
                count = int(min(limit, tokens + tokens_to_add))
            else:
                count = limit
        
        return RateLimitResult(
            allowed=count < limit,
            remaining=max(0, limit - count),
            reset_at=current_time + window
        )
    
    async def reset(self, identifier: str) -> None:
        """Reset the rate limit for an identifier."""
        key = self._make_key(identifier)
        await asyncio.get_event_loop().run_in_executor(
            None,
            self._redis.delete,
            key
        )
    
    async def reset_window(self, identifier: str, window: float) -> None:
        """Reset only the current window for an identifier."""
        if self._algorithm == 'fixed_window':
            current_time = time.time()
            window_start = (current_time // window) * window
            window_key = f"{self._make_key(identifier)}:{window_start}"
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._redis.delete,
                window_key
            )
        else:
            await self.reset(identifier)
    
    @asynccontextmanager
    async def pipeline(self):
        """Context manager for Redis pipeline operations."""
        pipe = await asyncio.get_event_loop().run_in_executor(
            None,
            self._redis.pipeline
        )
        yield pipe
        await asyncio.get_event_loop().run_in_executor(None, pipe.execute)
    
    @property
    def redis_client(self) -> redis.Redis:
        """Get the underlying Redis client."""
        return self._redis


class RedisBackend:
    """
    Redis backend wrapper for rate limiting operations.
    
    Provides connection management and utility methods.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        pool_size: int = 10,
        timeout: int = 5
    ):
        """
        Initialize Redis backend.
        
        Args:
            redis_url: Redis connection URL
            pool_size: Maximum number of connections in the pool
            timeout: Connection timeout in seconds
        """
        self._redis_url = redis_url
        self._pool_size = pool_size
        self._timeout = timeout
        
        self._pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=pool_size,
            socket_timeout=timeout
        )
        self._client = redis.Redis(connection_pool=self._pool)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self) -> None:
        """Close the connection pool."""
        await asyncio.get_event_loop().run_in_executor(None, self._pool.disconnect)
    
    async def ping(self) -> bool:
        """Check if Redis is reachable."""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                self._client.ping
            )
            return bool(result)
        except redis.ConnectionError:
            return False
    
    async def get_connection_pool(self) -> redis.ConnectionPool:
        """Get the connection pool."""
        return self._pool
    
    async def keys(self, pattern: str) -> List[str]:
        """Get all keys matching a pattern."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._client.keys,
            pattern
        )
    
    async def delete(self, key: str) -> int:
        """Delete a key."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._client.delete,
            key
        )
    
    async def ttl(self, key: str) -> int:
        """Get TTL of a key."""
        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._client.ttl,
            key
        )
