"""
Rate Limiter for Best Buy API
Implements rate limiting to comply with Best Buy API restrictions:
- 5 requests per minute (free developer tier)
- 50,000 requests per day
"""
import asyncio
import time
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding-window rate limiter for Best Buy API.

    Best Buy free-tier API Limits:
    - 5 requests per minute
    - 50,000 requests per day
    """
    
    def __init__(
        self,
        requests_per_minute: int = 5,
        requests_per_day: int = 50000
    ):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests per minute (default: 5)
            requests_per_day:    Maximum requests per day   (default: 50,000)
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        
        # Sliding window: track timestamps of requests in the last 60 seconds
        self.recent_requests: deque = deque()
        
        # Track daily requests
        self.daily_requests: deque = deque()
        self.daily_reset_time = time.time() + 86400  # 24 hours from now
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        logger.info(
            f"Rate limiter initialized: {requests_per_minute} req/min, "
            f"{requests_per_day} req/day"
        )
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        Blocks until a request slot is available within the per-minute window.
        """
        async with self.lock:
            current_time = time.time()
            
            # ── Daily limit ──────────────────────────────────────────────────
            if current_time >= self.daily_reset_time:
                logger.info("Resetting daily request counter")
                self.daily_requests.clear()
                self.daily_reset_time = current_time + 86400
            
            if len(self.daily_requests) >= self.requests_per_day:
                wait_time = self.daily_reset_time - current_time
                logger.warning(
                    f"Daily limit reached ({self.requests_per_day} requests). "
                    f"Waiting {wait_time:.1f}s until reset"
                )
                await asyncio.sleep(wait_time)
                self.daily_requests.clear()
                self.daily_reset_time = time.time() + 86400
                current_time = time.time()
            
            # ── Per-minute sliding window (60 seconds) ───────────────────────
            WINDOW = 60.0  # seconds
            while self.recent_requests and current_time - self.recent_requests[0] >= WINDOW:
                self.recent_requests.popleft()
            
            if len(self.recent_requests) >= self.requests_per_minute:
                # Next slot opens when the oldest request in the window expires
                oldest = self.recent_requests[0]
                wait_time = WINDOW - (current_time - oldest) + 0.05  # tiny buffer
                logger.info(
                    f"Per-minute limit: {len(self.recent_requests)}/{self.requests_per_minute} "
                    f"requests in last 60s. Waiting {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)
                current_time = time.time()
                # Clean up again after waiting
                while self.recent_requests and current_time - self.recent_requests[0] >= WINDOW:
                    self.recent_requests.popleft()
            
            # Record this request
            self.recent_requests.append(current_time)
            self.daily_requests.append(current_time)
            
            logger.debug(
                f"Request allowed. Window({int(WINDOW)}s): {len(self.recent_requests)}/{self.requests_per_minute}, "
                f"Daily: {len(self.daily_requests)}/{self.requests_per_day}"
            )
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics"""
        current_time = time.time()
        WINDOW = 60.0
        while self.recent_requests and current_time - self.recent_requests[0] >= WINDOW:
            self.recent_requests.popleft()
        
        return {
            "requests_last_minute": len(self.recent_requests),
            "requests_per_minute_limit": self.requests_per_minute,
            "requests_today": len(self.daily_requests),
            "requests_per_day_limit": self.requests_per_day,
            "daily_reset_in_seconds": max(0, self.daily_reset_time - current_time)
        }
