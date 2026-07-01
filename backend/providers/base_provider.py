"""Abstract base class for AI providers."""

import time
from abc import ABC, abstractmethod
from typing import Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BaseProvider(ABC):
    """Abstract base provider for all AI backends."""

    def __init__(self):
        """Initialize provider with health tracking."""
        self.last_request_time: float | None = None
        self.last_response_latency: float | None = None
        self.request_count: int = 0
        self.error_count: int = 0

    @abstractmethod
    async def generate(self, prompt: str, system: str = "", task: str = "conversion") -> dict[str, Any]:
        """
        Generate response from the provider.

        Args:
            prompt: User prompt
            system: System prompt
            task: 'conversion' or 'understanding'

        Returns:
            dict with keys:
            - For conversion: 'python_code', 'explanation', 'confidence_score'
            - For understanding: 'operator', 'meaning', 'category', 'explanation', 'confidence'
            - On error: 'error', 'detail'
        """
        pass

    def _log_request_started(self, provider_name: str, prompt_len: int) -> float:
        """
        Log request start and return timestamp for latency tracking.

        Args:
            provider_name: Name of the provider
            prompt_len: Length of the prompt

        Returns:
            Timestamp for later latency calculation
        """
        self.request_count += 1
        start_time = time.time()
        logger.info(
            "[PROVIDER REQUEST STARTED] provider=%s request_id=%d prompt_length=%d",
            provider_name,
            self.request_count,
            prompt_len,
        )
        return start_time

    def _log_response_received(
        self,
        provider_name: str,
        start_time: float,
        response_len: int = 0,
    ) -> None:
        """
        Log response received and calculate latency.

        Args:
            provider_name: Name of the provider
            start_time: Timestamp from _log_request_started
            response_len: Length of the response text
        """
        latency = time.time() - start_time
        self.last_response_latency = latency
        logger.info(
            "[PROVIDER RESPONSE RECEIVED] provider=%s latency_ms=%.1f response_length=%d",
            provider_name,
            latency * 1000,
            response_len,
        )

    def _log_timeout(self, provider_name: str, timeout_seconds: int) -> None:
        """Log timeout event."""
        self.error_count += 1
        logger.error(
            "[TIMEOUT] provider=%s timeout_seconds=%d error_count=%d",
            provider_name,
            timeout_seconds,
            self.error_count,
        )

    def _log_parse_error(self, provider_name: str, error_detail: str) -> None:
        """Log parse error event."""
        self.error_count += 1
        logger.error(
            "[PARSE ERROR] provider=%s error=%s error_count=%d",
            provider_name,
            error_detail,
            self.error_count,
        )

    def _log_retry_triggered(
        self,
        provider_name: str,
        attempt: int,
        error_type: str,
        backoff_seconds: float,
    ) -> None:
        """Log retry event."""
        logger.warning(
            "[RETRY TRIGGERED] provider=%s attempt=%d error_type=%s backoff_seconds=%.1f",
            provider_name,
            attempt,
            error_type,
            backoff_seconds,
        )

    def _log_fallback_triggered(self, provider_name: str, reason: str) -> None:
        """Log fallback to local converter."""
        logger.warning(
            "[FALLBACK TRIGGERED] provider=%s reason=%s",
            provider_name,
            reason,
        )

    def get_health_status(self) -> dict[str, Any]:
        """Get provider health status."""
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "last_response_latency_ms": (
                self.last_response_latency * 1000
                if self.last_response_latency is not None
                else None
            ),
        }
