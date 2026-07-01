"""Ollama provider for local private mode."""

import asyncio
import time
from typing import Any
import httpx
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider
from .response_normalizer import ResponseNormalizer
from .retry_utils import RetryConfig, is_retryable_error

logger = get_logger(__name__)


class OllamaProvider(BaseProvider):
    """Provider for Ollama local models (Qwen, etc.)."""

    def __init__(self):
        super().__init__()
        self.provider_name = "ollama"
        # Get per-provider timeout from config
        self.timeout_seconds = settings.PROVIDER_TIMEOUTS.get("ollama", 60)
        self.retry_config = RetryConfig(max_retries=settings.RETRY_ATTEMPTS)

    async def generate(self, prompt: str, system: str = "", task: str = "conversion") -> dict[str, Any]:
        """
        Generate response from Ollama with retry logic and health logging.

        Args:
            prompt: User prompt
            system: System prompt
            task: 'conversion' or 'understanding'

        Returns:
            dict with normalized response or error
        """
        url = f"{settings.OLLAMA_URL}/api/generate"
        payload = {
            "model": settings.MODEL_NAME,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "num_predict": 600,  # cap output tokens to avoid rambling/over-generation
            },
        }

        timeout = httpx.Timeout(self.timeout_seconds, connect=self.timeout_seconds)
        start_time = self._log_request_started(self.provider_name, len(prompt))
        last_error = None
        backoff = 1.0

        for attempt in range(1, self.retry_config.max_retries + 2):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()

                    response_data = response.json()
                    self._log_response_received(
                        self.provider_name,
                        start_time,
                        len(response_data.get("response", "")),
                    )

                    # Normalize the response according to the intended task
                    if task == "understanding":
                        normalized = ResponseNormalizer.normalize_understanding_response(
                            response_data,
                            provider_name=self.provider_name,
                        )
                    else:
                        normalized = ResponseNormalizer.normalize_conversion_response(
                            response_data,
                            provider_name=self.provider_name,
                        )
                    return normalized

            except httpx.TimeoutException as exc:
                last_error = exc
                self._log_timeout(self.provider_name, self.timeout_seconds)

                if attempt <= self.retry_config.max_retries:
                    self._log_retry_triggered(
                        self.provider_name,
                        attempt,
                        "timeout",
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                return {
                    "error": "Ollama request timed out",
                    "detail": f"Timeout after {self.timeout_seconds}s",
                    "timeout": self.timeout_seconds,
                }

            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code

                # Only retry on 5xx errors
                if 500 <= status < 600 and attempt <= self.retry_config.max_retries:
                    self._log_retry_triggered(
                        self.provider_name,
                        attempt,
                        f"http_{status}",
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                # Don't retry on 4xx errors
                error_text = exc.response.text
                logger.error(
                    "[%s] HTTP %d: %s",
                    self.provider_name,
                    status,
                    error_text[:200],
                )
                return {
                    "error": f"Ollama HTTP {status}",
                    "detail": error_text[:500],
                }

            except httpx.ConnectError as exc:
                last_error = exc
                if attempt <= self.retry_config.max_retries:
                    self._log_retry_triggered(
                        self.provider_name,
                        attempt,
                        "connection_error",
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                return {
                    "error": "Ollama service unreachable",
                    "detail": str(exc),
                }

            except Exception as exc:
                last_error = exc
                if attempt <= self.retry_config.max_retries:
                    self._log_retry_triggered(
                        self.provider_name,
                        attempt,
                        type(exc).__name__,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2.0
                    continue

                logger.exception("[%s] Unexpected error", self.provider_name)
                return {
                    "error": "Ollama request failed",
                    "detail": str(exc),
                }

        # Max retries exhausted
        if last_error:
            logger.error(
                "[%s] Max retries exhausted: %s",
                self.provider_name,
                str(last_error),
            )
            return {
                "error": "Ollama max retries exhausted",
                "detail": str(last_error),
            }

        return {"error": "Ollama unknown error"}