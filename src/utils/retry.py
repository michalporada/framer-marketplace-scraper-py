"""Retry logic with exponential backoff using tenacity."""

import functools
import logging
import random
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry_on_network_error(
    max_retries: Optional[int] = None,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions on network errors with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (defaults to settings.max_retries)
        initial_wait: Initial wait time in seconds before first retry
        max_wait: Maximum wait time in seconds between retries
        exceptions: Tuple of exception types to retry on (defaults to common network errors)

    Returns:
        Decorator function
    """
    if max_retries is None:
        max_retries = settings.max_retries

    if exceptions is None:
        exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            Exception,  # Catch all for HTTP errors
        )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=initial_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.INFO),
            after=after_log(logger, logging.INFO),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator


async def retry_async(
    func: Callable[..., T],
    max_retries: Optional[int] = None,
    initial_wait: Optional[float] = None,
    max_wait: Optional[float] = None,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Retry async function with exponential backoff and jitter.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts (defaults to settings.max_retries)
        initial_wait: Initial wait time in seconds (defaults to settings.retry_initial_wait)
        max_wait: Maximum wait time in seconds (defaults to settings.retry_max_wait)
        exceptions: Tuple of exception types to retry on
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    if max_retries is None:
        max_retries = settings.max_retries
    if initial_wait is None:
        initial_wait = settings.retry_initial_wait
    if max_wait is None:
        max_wait = settings.retry_max_wait

    if exceptions is None:
        exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            Exception,
        )

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Exponential backoff: initial_wait * 2^attempt
                base_wait = min(initial_wait * (2**attempt), max_wait)
                
                # Add jitter if enabled (random 0-20% of base wait time)
                if settings.retry_jitter:
                    jitter = random.uniform(0, base_wait * 0.2)
                    wait_time = base_wait + jitter
                    jitter_value = round(jitter, 2)
                else:
                    wait_time = base_wait
                    jitter_value = 0
                
                logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_time=round(wait_time, 2),
                    base_wait=round(base_wait, 2),
                    jitter=jitter_value,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                import asyncio

                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    "retry_exhausted",
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

    # Should never reach here, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed without exception")


def retry_sync(
    func: Callable[..., T],
    max_retries: Optional[int] = None,
    initial_wait: float = 1.0,
    max_wait: float = 60.0,
    exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    *args: Any,
    **kwargs: Any,
) -> T:
    """Retry sync function with exponential backoff.

    Args:
        func: Sync function to retry
        max_retries: Maximum number of retry attempts
        initial_wait: Initial wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    if max_retries is None:
        max_retries = settings.max_retries

    if exceptions is None:
        exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,
            Exception,
        )

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                wait_time = min(initial_wait * (2**attempt), max_wait)
                logger.warning(
                    "retry_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    wait_time=wait_time,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                import time

                time.sleep(wait_time)
            else:
                logger.error(
                    "retry_exhausted",
                    max_retries=max_retries,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

    # Should never reach here, but type checker needs it
    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed without exception")
