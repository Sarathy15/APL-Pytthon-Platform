"""Gemini provider for public API mode."""

import asyncio
from typing import Any
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider
from .response_normalizer import ResponseNormalizer
from .retry_utils import RetryConfig

logger = get_logger(__name__)


class GeminiProvider(BaseProvider):
    """Provider for Google Gemini API."""

    def __init__(self):
        """Initialize Gemini provider with API key."""
        super().__init__()
        self.provider_name = "gemini"
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        except ImportError:
            raise ImportError("google-generativeai package required. Install with: pip install google-generativeai")

        # Get per-provider timeout from config
        self.timeout_seconds = settings.PROVIDER_TIMEOUTS.get("gemini", 45)
        self.retry_config = RetryConfig(max_retries=settings.RETRY_ATTEMPTS)

    async def generate(self, prompt: str, system: str = "", task: str = "conversion") -> dict[str, Any]:
        """
        Generate response from Gemini with retry logic and health logging.

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
                # Run Gemini call in executor to avoid blocking
                loop = asyncio.get_event_loop()

                def _generate():
                    full_prompt = f"{system}\n\n{prompt}" if system else prompt
                    return self.client.generate_content(
                        full_prompt,
                        generation_config={
                            "max_output_tokens": 2048,
                            "temperature": 0.7,
                        },
                    )

                response = await asyncio.wait_for(
                    loop.run_in_executor(None, _generate),
                    timeout=self.timeout_seconds,
                )

                response_text = response.text if response else ""
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
                    "error": "Gemini request timed out",
                    "detail": f"Timeout after {self.timeout_seconds}s",
                    "timeout": self.timeout_seconds,
                }

            except Exception as exc:
                last_error = exc
                error_str = str(exc).lower()

                # Check for permanent errors
                if any(
                    keyword in error_str
                    for keyword in ["api key", "auth", "permission", "401", "403", "forbidden"]
                ):
                    logger.error(
                        "[%s] Authentication/permission error, not retrying: %s",
                        self.provider_name,
                        exc,
                    )
                    return {
                        "error": "Gemini authentication failed",
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

                logger.exception("[%s] Gemini request failed", self.provider_name)
                return {
                    "error": "Gemini API request failed",
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
                "error": "Gemini max retries exhausted",
                "detail": str(last_error),
            }

        return {"error": "Gemini unknown error"}
