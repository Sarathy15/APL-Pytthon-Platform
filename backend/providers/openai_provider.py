"""OpenAI provider for public API mode."""

import asyncio
from typing import Any
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider
from .response_normalizer import ResponseNormalizer
from .retry_utils import RetryConfig

logger = get_logger(__name__)


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI API (GPT-5, etc.)."""

    def __init__(self):
        """Initialize OpenAI provider with API key."""
        super().__init__()
        self.provider_name = "openai"
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        # Get per-provider timeout from config
        self.timeout_seconds = settings.PROVIDER_TIMEOUTS.get("openai", 45)
        self.retry_config = RetryConfig(max_retries=settings.RETRY_ATTEMPTS)

    async def generate(self, prompt: str, system: str = "", task: str = "conversion") -> dict[str, Any]:
        """
        Generate response from OpenAI with retry logic and health logging.

        Args:
            prompt: User prompt
            system: System prompt
            task: 'conversion' or 'understanding'

        Returns:
            dict with normalized response or error
        """
        start_time = self._log_request_started(self.provider_name, len(prompt))
        last_error = None
        backoff = 1.0

        for attempt in range(1, self.retry_config.max_retries + 2):
            try:
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})

                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2048,
                    ),
                    timeout=self.timeout_seconds,
                )

                response_text = response.choices[0].message.content if response.choices else ""
                self._log_response_received(
                    self.provider_name,
                    start_time,
                    len(response_text),
                )

                # Normalize the response according to the intended task
                if task == "understanding":
                    normalized = ResponseNormalizer.normalize_understanding_response(
                        {"response": response_text},
                        provider_name=self.provider_name,
                    )
                else:
                    normalized = ResponseNormalizer.normalize_conversion_response(
                        {"response": response_text},
                        provider_name=self.provider_name,
                    )
                return normalized

            except asyncio.TimeoutError as exc:
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
                    "error": "OpenAI request timed out",
                    "detail": f"Timeout after {self.timeout_seconds}s",
                    "timeout": self.timeout_seconds,
                }

            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()

                # Check for permanent errors
                if any(
                    keyword in error_str
                    for keyword in ["api key", "auth", "permission", "401", "403", "forbidden", "unauthorized"]
                ):
                    logger.error(
                        "[%s] Authentication/permission error, not retrying: %s",
                        self.provider_name,
                        exc,
                    )
                    return {
                        "error": "OpenAI authentication failed",
                        "detail": str(exc),
                    }

                # Retry on other errors
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

                logger.exception("[%s] OpenAI request failed", self.provider_name)
                return {
                    "error": "OpenAI API request failed",
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
                "error": "OpenAI max retries exhausted",
                "detail": str(last_error),
            }

        return {"error": "OpenAI unknown error"}
