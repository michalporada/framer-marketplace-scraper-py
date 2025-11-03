"""Rate limiter for HTTP requests with randomization."""

import asyncio
import random
import time
from typing import Optional, Tuple

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter that enforces delays between requests with randomization."""

    def __init__(
        self,
        requests_per_second: Optional[float] = None,
        delay_range: Optional[Tuple[float, float]] = None,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (defaults to settings)
            delay_range: Tuple of (min, max) delay in seconds for randomization
        """
        self.requests_per_second = requests_per_second or settings.rate_limit
        self.min_delay = 1.0 / self.requests_per_second if self.requests_per_second > 0 else 1.0

        # Randomization range: 0.5x to 2x of base delay
        if delay_range is None:
            min_delay_factor = 0.5
            max_delay_factor = 2.0
            self.delay_range = (
                self.min_delay * min_delay_factor,
                self.min_delay * max_delay_factor,
            )
        else:
            self.delay_range = delay_range

        self.last_request_time: float = 0.0
        self.request_count: int = 0
        self.total_wait_time: float = 0.0

    def _calculate_delay(self) -> float:
        """Calculate randomized delay based on rate limit.

        Returns:
            Delay in seconds
        """
        # Randomize delay within the range
        delay = random.uniform(*self.delay_range)

        # Ensure minimum delay is respected
        if delay < self.min_delay:
            delay = self.min_delay

        return delay

    async def acquire(self) -> None:
        """Acquire permission to make a request (async)."""
        current_time = time.time()

        # Calculate time since last request
        time_since_last = current_time - self.last_request_time

        # Calculate required delay
        required_delay = self._calculate_delay()

        # If enough time has passed, no need to wait
        if time_since_last >= required_delay:
            wait_time = 0.0
        else:
            wait_time = required_delay - time_since_last

        # Wait if necessary
        if wait_time > 0:
            logger.debug(
                "rate_limiter_wait",
                wait_time=wait_time,
                delay_range=self.delay_range,
            )
            await asyncio.sleep(wait_time)
            self.total_wait_time += wait_time

        # Update last request time
        self.last_request_time = time.time()
        self.request_count += 1

    def acquire_sync(self) -> None:
        """Acquire permission to make a request (synchronous)."""
        current_time = time.time()

        # Calculate time since last request
        time_since_last = current_time - self.last_request_time

        # Calculate required delay
        required_delay = self._calculate_delay()

        # If enough time has passed, no need to wait
        if time_since_last >= required_delay:
            wait_time = 0.0
        else:
            wait_time = required_delay - time_since_last

        # Wait if necessary
        if wait_time > 0:
            logger.debug(
                "rate_limiter_wait",
                wait_time=wait_time,
                delay_range=self.delay_range,
            )
            time.sleep(wait_time)
            self.total_wait_time += wait_time

        # Update last request time
        self.last_request_time = time.time()
        self.request_count += 1

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "request_count": self.request_count,
            "total_wait_time": self.total_wait_time,
            "average_wait_time": (
                self.total_wait_time / self.request_count if self.request_count > 0 else 0.0
            ),
            "requests_per_second": self.requests_per_second,
        }

    def reset(self) -> None:
        """Reset rate limiter statistics."""
        self.last_request_time = 0.0
        self.request_count = 0
        self.total_wait_time = 0.0


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
