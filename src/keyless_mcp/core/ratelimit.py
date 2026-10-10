"""A tiny per-adapter rate limiter: spaces calls evenly to honour ``rate_limit_per_minute``."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable


class RateLimiter:
    """Allow at most ``per_minute`` calls per minute by enforcing a minimum gap between calls."""

    def __init__(
        self,
        per_minute: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if per_minute <= 0:
            raise ValueError("per_minute must be positive")
        self._gap = 60.0 / per_minute
        self._clock = clock
        self._sleep = sleep
        self._next_slot = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = self._clock()
            wait = self._next_slot - now
            if wait > 0:
                await self._sleep(wait)
                now = self._next_slot
            self._next_slot = now + self._gap
