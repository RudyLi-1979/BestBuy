"""
Rate Limiter for Best Buy API
Implements rate limiting to comply with Best Buy API restrictions:
- 5 requests per second
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
    Token bucket rate limiter for Best Buy API
    
    Best Buy API Limits:
    - 5 requests per second
    - 50,000 requests per day
    """
    
    def __init__(
        self,
        requests_per_second: int = 5,
        requests_per_day: int = 50000
    ):
        """
        Initialize rate limiter
        
        Args:
            requests_per_second: Maximum requests per second (default: 5)
            requests_per_day: Maximum requests per day (default: 50,000)
        """
        self.requests_per_second = requests_per_second
        self.requests_per_day = requests_per_day
        
        # Track requests in the last second
        self.recent_requests: deque = deque()
        
        # Track daily requests
        self.daily_requests: deque = deque()
        self.daily_reset_time = time.time() + 86400  # 24 hours from now
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
        
        logger.info(
            f"Rate limiter initialized: {requests_per_second} req/s, "
            f"{requests_per_day} req/day"
        )
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request
        Blocks until request can be made within rate limits
        """
        async with self.lock:
            current_time = time.time()
            
            # Reset daily counter if needed
            if current_time >= self.daily_reset_time:
                logger.info("Resetting daily request counter")
                self.daily_requests.clear()
                self.daily_reset_time = current_time + 86400
            
            # Check daily limit
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
            
            # Remove requests older than 1 second
            while self.recent_requests and current_time - self.recent_requests[0] > 1.0:
                self.recent_requests.popleft()
            
            # Check per-second limit
            if len(self.recent_requests) >= self.requests_per_second:
                # Calculate wait time
                oldest_request = self.recent_requests[0]
                wait_time = 1.0 - (current_time - oldest_request)
                
                if wait_time > 0:
                    logger.debug(
                        f"Rate limit: {len(self.recent_requests)}/{self.requests_per_second} "
                        f"requests in last second. Waiting {wait_time:.3f}s"
                    )
                    await asyncio.sleep(wait_time)
                    current_time = time.time()
                    
                    # Clean up old requests after waiting
                    while self.recent_requests and current_time - self.recent_requests[0] > 1.0:
                        self.recent_requests.popleft()
            
            # Record this request
            self.recent_requests.append(current_time)
            self.daily_requests.append(current_time)
            
            logger.debug(
                f"Request allowed. Recent: {len(self.recent_requests)}/{self.requests_per_second}, "
                f"Daily: {len(self.daily_requests)}/{self.requests_per_day}"
            )
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics"""
        current_time = time.time()
        
        # Clean up old requests
        while self.recent_requests and current_time - self.recent_requests[0] > 1.0:
            self.recent_requests.popleft()
        
        return {
            "requests_last_second": len(self.recent_requests),
            "requests_per_second_limit": self.requests_per_second,
            "requests_today": len(self.daily_requests),
            "requests_per_day_limit": self.requests_per_day,
            "daily_reset_in_seconds": max(0, self.daily_reset_time - current_time)
        }
