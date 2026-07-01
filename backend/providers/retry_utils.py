"""Lightweight retry utility for provider failures.

Retries only on:
- Timeouts
- Transient API errors (5xx)
- Parse failures

Does NOT retry on:
- Authentication failures
- Bad requests (4xx client errors)
- Invalid prompts
"""

import asyncio
import httpx
from typing import Callable, Any, TypeVar, Coroutine
from ..utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 2,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier


class RetryableError(Exception):
    """Base class for errors that should trigger a retry."""
    pass


class TransientError(RetryableError):
    """Transient error (e.g., 5xx, timeout) - should retry."""
    pass


class PermanentError(Exception):
    """Permanent error (e.g., auth, bad request) - should NOT retry."""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error should trigger a retry.

    Retryable:
    - Timeout
    - Transient HTTP errors (5xx)
    - TransientError subclasses
    - Generic transient network errors

    Not retryable:
    - Authentication (401)
    - Forbidden (403)
    - Bad request (400)
    - Invalid API key
    - PermanentError subclasses
    """
    # Timeouts are retryable
    if isinstance(error, (asyncio.TimeoutError, TimeoutError)):
        return True

    # HTTP status errors
    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        # 5xx errors are transient
        if 500 <= status < 600:
            return True
        # 4xx are permanent
        if 400 <= status < 500:
            return False

    # Connection errors are transient
    if isinstance(error, (httpx.ConnectError, httpx.NetworkError)):
        return True

    # Explicit error types
    if isinstance(error, TransientError):
        return True
    if isinstance(error, PermanentError):
        return False

    # Default: be conservative, don't retry unknown errors
    return False


async def with_retry(
    coro_func: Callable[..., Coroutine[Any, Any, T]],
    provider_name: str = "unknown",
    config: RetryConfig | None = None,
    *args,
    **kwargs,
) -> T:
    """
    Execute async function with retry logic.

    Args:
        coro_func: Async function to call
        provider_name: Name of provider (for logging)
        config: RetryConfig with max_retries, backoff, etc.
        *args, **kwargs: Arguments to pass to coro_func

    Returns:
        Result from coro_func

    Raises:
        Exception: Last exception encountered after max retries exhausted
    """
    if config is None:
        config = RetryConfig()

    last_error = None
    backoff = config.initial_backoff

    for attempt in range(1, config.max_retries + 2):  # +2 for initial attempt + 1
        try:
            return await coro_func(*args, **kwargs)
        except Exception as error:
            last_error = error

            if not is_retryable_error(error):
                logger.warning(
                    "[%s] Permanent error, not retrying: %s",
                    provider_name,
                    type(error).__name__,
                )
                raise

            if attempt > config.max_retries + 1:
                logger.error(
                    "[%s] Max retries exhausted after %d attempts",
                    provider_name,
                    attempt - 1,
                )
                raise

            logger.warning(
                "[%s] Retryable error (attempt %d/%d): %s, waiting %.1fs before retry",
                provider_name,
                attempt,
                config.max_retries + 1,
                type(error).__name__,
                backoff,
            )

            await asyncio.sleep(backoff)
            backoff *= config.backoff_multiplier

    # Should not reach here, but just in case
    if last_error:
        raise last_error
    raise RuntimeError(f"[{provider_name}] Unexpected retry failure")
