"""
In-memory sliding window rate limiter for abuse protection (Phase 36).
Provides configurable endpoint-level and IP/User-level rate limiting with zero external dependencies.
"""

import time
import threading
from collections import defaultdict, deque
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger("fraudlens.rate_limiter")


class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding window rate limiter.
    Tracks request timestamps per key (IP address or user identifier).
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._records = defaultdict(deque)
        self.enabled = True

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        Check if a request is allowed under the rate limit.
        Returns:
            (is_allowed: bool, remaining_requests: int, retry_after_seconds: int)
        """
        if not self.enabled:
            return True, max_requests, 0

        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._records[key]

            # Evict timestamps older than the sliding window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            current_count = len(timestamps)
            if current_count >= max_requests:
                # Rate limit exceeded
                oldest_timestamp = timestamps[0]
                retry_after = max(1, int(oldest_timestamp + window_seconds - now))
                return False, 0, retry_after

            # Register current request timestamp
            timestamps.append(now)
            remaining = max_requests - (current_count + 1)
            return True, remaining, 0

    def reset(self, key: Optional[str] = None):
        """Reset records for a specific key or all keys (useful in testing)."""
        with self._lock:
            if key:
                if key in self._records:
                    del self._records[key]
            else:
                self._records.clear()


# Global rate limiter instance
limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int, window_seconds: int, key_func: Optional[Callable[[Request], str]] = None):
    """
    FastAPI dependency for rate limiting endpoints.
    
    Usage:
        @router.post("/login", dependencies=[Depends(rate_limit(10, 60))])
    """
    async def dependency(request: Request):
        if not limiter.enabled:
            return

        if key_func:
            client_key = key_func(request)
        else:
            # Default to client IP or Authorization header prefix
            client_ip = request.client.host if request.client else "unknown"
            auth_header = request.headers.get("Authorization", "")
            path = request.url.path
            client_key = f"{path}:{client_ip}:{auth_header[:20]}"

        allowed, remaining, retry_after = limiter.is_allowed(client_key, max_requests, window_seconds)
        if not allowed:
            logger.warning(f"Rate limit exceeded for key {client_key} on {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after), "X-RateLimit-Remaining": "0"}
            )

    return dependency
