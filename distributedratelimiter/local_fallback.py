"""
In-memory fallback rate limiter.
"""

import time
import threading
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict

from .limiter import (
    RateLimiter,
    RateLimitResult,
    FixedWindowLimiter as FixedWindowLimiterImpl,
    SlidingWindowLogLimiter as SlidingWindowLogLimiterImpl,
    TokenBucketLimiter as TokenBucketLimiterImpl
)


@dataclass
class FallbackState:
    """State for fallback limiter."""
    requests: List[float] = field(default_factory=list)
    last_check: float = field(default_factory=time.time)
    failure_count: int = 0
    is_healthy: bool = True


class LocalFallbackLimiter(RateLimiter):
    """
    In-memory fallback rate limiter for when Redis is unavailable.
    
    Uses a combination of sliding window log and token bucket algorithms
    with automatic recovery tracking.
    """
    
    def __init__(
        self,
        algorithm: str = "token_bucket",
        max_requests: int = 100,
        window: float = 60.0,
        recovery_threshold: int = 10,
        recovery_window: float = 30.0
    ):
        """
        Initialize local fallback limiter.
        
        Args:
            algorithm: One of 'fixed_window', 'sliding_window_log', 'token_bucket'
            max_requests: Default max requests per window
            window: Default window size in seconds
            recovery_threshold: Number of successful requests to recover
            recovery_window: Window to count recovery requests
        """
        self._algorithm = algorithm
        self._max_requests = max_requests
        self._window = window
        self._recovery_threshold = recovery_threshold
        self._recovery_window = recovery_window
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        # State storage
        self._states: Dict[str, FallbackState] = {}
        
        # Algorithm-specific limiters
        self._limiters: Dict[str, RateLimiter] = {}
        self._create_limiters()
    
    def _create_limiters(self) -> None:
        """Create algorithm-specific limiters."""
        algorithms = {
            "fixed_window": FixedWindowLimiterImpl,
            "sliding_window_log": SlidingWindowLogLimiterImpl,
            "token_bucket": TokenBucketLimiterImpl
        }
        
        if self._algorithm not in algorithms:
            raise ValueError(f"Unknown algorithm: {self._algorithm}")
        
        # Create instance of selected algorithm
        self._main_limiter = algorithms[self._algorithm]()
    
    async def is_allowed(self, identifier: str, limit: int, window: float) -> RateLimitResult:
        """
        Check if request is allowed using fallback limiter.
        
        Args:
            identifier: Unique identifier for rate limit subject
            limit: Maximum requests in window
            window: Window size in seconds
            
        Returns:
            RateLimitResult
        """
        with self._lock:
            if identifier not in self._states:
                self._states[identifier] = FallbackState()
            
            state = self._states[identifier]
            
            # Update state
            current_time = time.time()
            state.last_check = current_time
            
            # Check recovery status
            if not state.is_healthy:
                if self._should_recover(state, current_time):
                    state.is_healthy = True
                    state.failure_count = 0
            
            # Use main limiter for algorithm-specific logic
            result = await self._main_limiter.is_allowed(identifier, limit, window)
            
            # Track failures for recovery
            if not result.allowed:
                state.failure_count += 1
                state.is_healthy = False
            
            return result
    
    async def get_stats(self, identifier: str, limit: int, window: float) -> RateLimitResult:
        """Get current rate limit stats."""
        return await self._main_limiter.get_stats(identifier, limit, window)
    
    async def _check_rate_limit(self, identifier: str, limit: int, window: float) -> RateLimitResult:
        """Check rate limit (alias for is_allowed for compatibility)."""
        return await self.is_allowed(identifier, limit, window)
    
    def _should_recover(self, state: FallbackState, current_time: float) -> bool:
        """Check if should recover from failure state."""
        # Count recent successful requests
        window_start = current_time - self._recovery_window
        recent_requests = [
            ts for ts in state.requests
            if ts > window_start
        ]
        
        # Check if we've had enough successful requests
        return len(recent_requests) >= self._recovery_threshold
    
    async def record_request(self, identifier: str, window: float) -> None:
        """Record a successful request for recovery tracking."""
        with self._lock:
            if identifier not in self._states:
                self._states[identifier] = FallbackState()
            
            state = self._states[identifier]
            state.requests.append(time.time())
            
            # Keep only requests within window
            window_start = time.time() - window
            state.requests = [ts for ts in state.requests if ts > window_start]
    
    async def is_healthy(self, identifier: str) -> bool:
        """Check if limiter is healthy for identifier."""
        with self._lock:
            if identifier not in self._states:
                return True
            return self._states[identifier].is_healthy
    
    async def get_failure_count(self, identifier: str) -> int:
        """Get failure count for identifier."""
        with self._lock:
            if identifier not in self._states:
                return 0
            return self._states[identifier].failure_count
    
    async def reset(self, identifier: str) -> None:
        """Reset state for identifier."""
        with self._lock:
            if identifier in self._states:
                del self._states[identifier]
            # Reset the main limiter's state for this identifier
            await self._main_limiter.reset(identifier)
    
    async def reset_all(self) -> None:
        """Reset all state."""
        with self._lock:
            self._states.clear()
            # Reset all limiters
            self._create_limiters()
    
    @property
    def is_healthy_global(self) -> bool:
        """Check if limiter is healthy globally."""
        with self._lock:
            if not self._states:
                return True
            return any(state.is_healthy for state in self._states.values())
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global stats."""
        with self._lock:
            return {
                "total_identifiers": len(self._states),
                "healthy_count": sum(1 for s in self._states.values() if s.is_healthy),
                "unhealthy_count": sum(1 for s in self._states.values() if not s.is_healthy),
                "total_failures": sum(s.failure_count for s in self._states.values())
            }


class LocalFallbackManager:
    """
    Manager for local fallback limiters across multiple services.
    
    Provides centralized control and monitoring.
    """
    
    def __init__(self):
        """Initialize manager."""
        self._limiters: Dict[str, LocalFallbackLimiter] = {}
        self._lock = threading.RLock()
    
    def get_limiter(
        self,
        name: str,
        algorithm: str = "token_bucket",
        max_requests: int = 100,
        window: float = 60.0
    ) -> LocalFallbackLimiter:
        """
        Get or create a fallback limiter.
        
        Args:
            name: Limiter name
            algorithm: Algorithm to use
            max_requests: Max requests per window
            window: Window size in seconds
            
        Returns:
            LocalFallbackLimiter instance
        """
        with self._lock:
            if name not in self._limiters:
                self._limiters[name] = LocalFallbackLimiter(
                    algorithm=algorithm,
                    max_requests=max_requests,
                    window=window
                )
            return self._limiters[name]
    
    async def check_rate_limit(
        self,
        name: str,
        identifier: str,
        limit: int,
        window: float
    ) -> RateLimitResult:
        """Check rate limit using named limiter."""
        limiter = self.get_limiter(name)
        return await limiter.is_allowed(identifier, limit, window)
    
    async def reset_limiter(self, name: str, identifier: str) -> None:
        """Reset named limiter for identifier."""
        if name in self._limiters:
            await self._limiters[name].reset(identifier)
    
    async def reset_all(self, name: str) -> None:
        """Reset all state for named limiter."""
        if name in self._limiters:
            await self._limiters[name].reset_all()
    
    async def get_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get stats for named limiter."""
        if name in self._limiters:
            return await self._limiters[name].get_global_stats()
        return None
    
    async def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all limiters."""
        stats = {}
        with self._lock:
            for name, limiter in self._limiters.items():
                stats[name] = await limiter.get_global_stats()
        return stats
    
    async def cleanup(self) -> None:
        """Clean up all limiters."""
        with self._lock:
            self._limiters.clear()


# Global manager instance
_manager = LocalFallbackManager()


def get_fallback_manager() -> LocalFallbackManager:
    """Get global fallback manager instance."""
    return _manager
