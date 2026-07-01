"""Claude provider for public API mode."""

import asyncio
from typing import Any
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider
from .response_normalizer import ResponseNormalizer
from .retry_utils import RetryConfig

logger = get_logger(__name__)


class ClaudeProvider(BaseProvider):
    """Provider for Anthropic Claude API."""

    def __init__(self):
        """Initialize Claude provider with API key."""
        super().__init__()
        self.provider_name = "claude"
        self.api_key = settings.CLAUDE_API_KEY
        self.model = settings.CLAUDE_MODEL
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not set in environment")

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        # Get per-provider timeout from config
        self.timeout_seconds = settings.PROVIDER_TIMEOUTS.get("claude", 45)
        self.retry_config = RetryConfig(max_retries=settings.RETRY_ATTEMPTS)

    async def generate(self, prompt: str, system: str = "", task: str = "conversion") -> dict[str, Any]:
        """
        Generate response from Claude with retry logic and health logging.

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
                # Run Claude API call in executor to avoid blocking
                loop = asyncio.get_event_loop()

                def _create_message():
                    return self.client.messages.create(
                        model=self.model,
                        max_tokens=2048,
                        system=system if system else None,
                        messages=[{"role": "user", "content": prompt}],
                    )

                message = await asyncio.wait_for(
                    loop.run_in_executor(None, _create_message),
                    timeout=self.timeout_seconds,
                )

                response_text = message.content[0].text if message.content else ""
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
                    "error": "Claude request timed out",
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
                        "error": "Claude authentication failed",
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

                logger.exception("[%s] Claude request failed", self.provider_name)
                return {
                    "error": "Claude API request failed",
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
                "error": "Claude max retries exhausted",
                "detail": str(last_error),
            }

        return {"error": "Claude unknown error"}
