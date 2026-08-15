"""
Rate limiting module for Doc2SDK API.

Provides in-memory sliding window rate limiting for FastAPI endpoints.
Protects compute-heavy and external request endpoints (AI generation, scraping, playground)
against DoS attacks and resource exhaustion.
"""

import asyncio
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, Request


def get_client_identifier(request: Request) -> str:
    """
    Extract a unique identifier for the client from the request.
    Uses authenticated API key if present, otherwise falls back to client IP.
    """
    # Check for Authorization header first
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return f"token:{auth[7:].strip()}"

    # Check for X-Forwarded-For (proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Leftmost IP is the original client
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip:
            return f"ip:{client_ip}"

    # Check for X-Real-IP
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return f"ip:{real_ip.strip()}"

    # Direct client host
    if request.client and request.client.host:
        return f"ip:{request.client.host}"

    return "unknown"


class SlidingWindowRateLimiter:
    """
    In-memory thread-safe sliding window rate limiter.
    Tracks timestamps of requests within a rolling time window.
    """

    def __init__(self, requests_per_minute: int, window_seconds: float = 60.0):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self._records: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> Tuple[bool, int]:
        """
        Check if a request from 'key' is allowed.
        
        Returns:
            Tuple[bool, int]: (is_allowed, retry_after_seconds)
        """
        # A limit of 0 or negative disables rate limiting
        if self.requests_per_minute <= 0:
            return True, 0

        now = time.time()
        window_start = now - self.window_seconds

        async with self._lock:
            timestamps = self._records[key]

            # Prune timestamps outside the current sliding window
            self._records[key] = [t for t in timestamps if t > window_start]
            valid_timestamps = self._records[key]

            if len(valid_timestamps) < self.requests_per_minute:
                # Under limit: record request
                valid_timestamps.append(now)
                return True, 0
            else:
                # Over limit: compute time until oldest request in window expires
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(oldest_timestamp + self.window_seconds - now) + 1)
                return False, retry_after

    def reset(self) -> None:
        """Clear all stored rate limit records (useful for tests)."""
        self._records.clear()


class RateLimiterDependency:
    """FastAPI dependency wrapper for SlidingWindowRateLimiter."""

    def __init__(self, get_limit_fn, default_limit: int = 60):
        self._get_limit_fn = get_limit_fn
        self._default_limit = default_limit
        self._limiters: Dict[int, SlidingWindowRateLimiter] = {}
        self._lock = asyncio.Lock()

    def _get_limiter(self) -> SlidingWindowRateLimiter:
        limit = self._get_limit_fn()
        if limit not in self._limiters:
            self._limiters[limit] = SlidingWindowRateLimiter(requests_per_minute=limit)
        return self._limiters[limit]

    async def __call__(self, request: Request) -> None:
        client_key = get_client_identifier(request)
        limiter = self._get_limiter()
        allowed, retry_after = await limiter.is_allowed(client_key)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    def reset(self) -> None:
        for limiter in self._limiters.values():
            limiter.reset()


def _get_ai_limit() -> int:
    try:
        return int(os.getenv("RATE_LIMIT_AI", "10"))
    except ValueError:
        return 10


def _get_general_limit() -> int:
    try:
        return int(os.getenv("RATE_LIMIT_GENERAL", "30"))
    except ValueError:
        return 30


# Pre-configured dependencies for route injection
rate_limit_ai = RateLimiterDependency(_get_ai_limit, default_limit=10)
rate_limit_general = RateLimiterDependency(_get_general_limit, default_limit=30)
