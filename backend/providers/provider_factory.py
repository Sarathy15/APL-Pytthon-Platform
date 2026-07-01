"""Provider factory - routes to correct AI backend based on configuration."""

from typing import Optional
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider
from .ollama_provider import OllamaProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .provider_registry import ProviderRegistry

logger = get_logger(__name__)


class ScaffoldedProviderError(Exception):
    """Raised when a provider is scaffolded but not fully configured."""
    pass


class ProviderFactory:
    """Factory for creating and managing AI providers."""

    _provider_cache: Optional[BaseProvider] = None
    _current_mode: Optional[str] = None
    _current_provider: Optional[str] = None

    @staticmethod
    def _validate_provider_config(provider_name: str) -> tuple[bool, str]:
        """
        Validate provider configuration.

        Returns:
            (is_valid, message)
        """
        provider_name_lower = provider_name.lower()
        metadata = ProviderRegistry.get_provider_metadata(provider_name_lower)

        if not metadata:
            return False, f"Provider '{provider_name}' not found in registry"

        if metadata.get("requires_api_key"):
            api_key_env = metadata.get("api_key_env_var")
            api_key_value = getattr(settings, api_key_env, "")

            if not api_key_value:
                msg = (
                    f"❌ {provider_name} provider scaffolded but API not configured yet. "
                    f"Set {api_key_env} environment variable."
                )
                return False, msg

        return True, "Provider configured"

    @staticmethod
    def get_provider() -> BaseProvider:
        """
        Get the appropriate provider based on configuration.

        Returns:
            BaseProvider instance (OllamaProvider, ClaudeProvider, OpenAIProvider, or GeminiProvider)

        Raises:
            ValueError: If AI_MODE is invalid or required API keys are missing
            ScaffoldedProviderError: If provider is scaffolded but not configured
        """
        ai_mode = getattr(settings, "AI_MODE", "private").lower()
        current_provider_name = getattr(settings, "AI_PROVIDER", "ollama").lower()

        # Check if we need to recreate the provider
        if (
            ProviderFactory._provider_cache is not None
            and ProviderFactory._current_mode == ai_mode
            and ProviderFactory._current_provider == current_provider_name
        ):
            return ProviderFactory._provider_cache

        # Validate provider config
        is_valid, config_msg = ProviderFactory._validate_provider_config(current_provider_name)
        if not is_valid:
            logger.warning(config_msg)
            raise ScaffoldedProviderError(config_msg)

        # Create new provider
        if ai_mode == "private":
            if current_provider_name != "ollama":
                raise ValueError(
                    f"PRIVATE mode only supports 'ollama' provider, got '{current_provider_name}'"
                )
            logger.info("Using PRIVATE mode with Ollama")
            ProviderFactory._provider_cache = OllamaProvider()
            ProviderFactory._current_provider = "ollama"

        elif ai_mode == "public":
            if current_provider_name == "claude":
                logger.info("Using PUBLIC mode with Claude")
                ProviderFactory._provider_cache = ClaudeProvider()
                ProviderFactory._current_provider = "claude"

            elif current_provider_name == "openai":
                logger.info("Using PUBLIC mode with OpenAI")
                ProviderFactory._provider_cache = OpenAIProvider()
                ProviderFactory._current_provider = "openai"

            elif current_provider_name == "gemini":
                logger.info("Using PUBLIC mode with Gemini")
                ProviderFactory._provider_cache = GeminiProvider()
                ProviderFactory._current_provider = "gemini"

            else:
                raise ValueError(
                    f"Invalid AI_PROVIDER '{current_provider_name}'. "
                    "Must be one of: claude, openai, gemini"
                )
            ProviderFactory._current_mode = ai_mode

        else:
            raise ValueError(
                f"Invalid AI_MODE '{ai_mode}'. Must be 'private' or 'public'."
            )

        return ProviderFactory._provider_cache

    @staticmethod
    def reset_cache():
        """Reset provider cache (useful for testing)."""
        ProviderFactory._provider_cache = None
        ProviderFactory._current_mode = None
        ProviderFactory._current_provider = None

    @staticmethod
    def get_mode() -> str:
        """Get current AI mode."""
        return getattr(settings, "AI_MODE", "private").lower()

    @staticmethod
    def get_active_provider_name() -> str:
        """Get name of currently active provider."""
        try:
            ProviderFactory.get_provider()  # Ensure cache is initialized
        except (ScaffoldedProviderError, ValueError):
            return "unknown"
        return ProviderFactory._current_provider or "unknown"

    @staticmethod
    def get_available_providers() -> dict:
        """Get all available providers and their status."""
        available = {}
        for provider_name, metadata in ProviderRegistry.list_providers().items():
            is_valid, msg = ProviderFactory._validate_provider_config(provider_name)
            available[provider_name] = {
                "metadata": metadata,
                "configured": is_valid,
                "status": msg,
            }
        return available
