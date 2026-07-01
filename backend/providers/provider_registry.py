"""Provider registry for managing all AI backends."""

from typing import Dict, Type, Optional, Any
from ..utils.logger import get_logger
from .base_provider import BaseProvider

logger = get_logger(__name__)


class ProviderRegistry:
    """Central registry for all available AI providers."""

    _providers: Dict[str, Type[BaseProvider]] = {}
    _provider_metadata: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        provider_class: Type[BaseProvider],
        mode: str = "private",
        requires_api_key: bool = False,
        api_key_env_var: str = "",
    ) -> None:
        """
        Register a provider.

        Args:
            name: Provider name (e.g., "ollama", "claude", "openai", "gemini")
            provider_class: Provider class
            mode: "private" or "public"
            requires_api_key: Whether API key is required
            api_key_env_var: Environment variable name for API key
        """
        cls._providers[name.lower()] = provider_class
        cls._provider_metadata[name.lower()] = {
            "name": name,
            "mode": mode,
            "requires_api_key": requires_api_key,
            "api_key_env_var": api_key_env_var,
        }
        logger.info(f"Registered provider: {name} (mode={mode}, requires_key={requires_api_key})")

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type[BaseProvider]]:
        """Get provider class by name."""
        return cls._providers.get(name.lower())

    @classmethod
    def get_provider_metadata(cls, name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a provider."""
        return cls._provider_metadata.get(name.lower())

    @classmethod
    def list_providers(cls) -> Dict[str, Dict[str, Any]]:
        """List all registered providers."""
        return cls._provider_metadata.copy()

    @classmethod
    def is_private_mode(cls, name: str) -> bool:
        """Check if provider is private mode."""
        metadata = cls.get_provider_metadata(name)
        return metadata.get("mode") == "private" if metadata else False

    @classmethod
    def is_public_mode(cls, name: str) -> bool:
        """Check if provider is public mode."""
        metadata = cls.get_provider_metadata(name)
        return metadata.get("mode") == "public" if metadata else False

    @classmethod
    def get_providers_by_mode(cls, mode: str) -> Dict[str, Dict[str, Any]]:
        """Get all providers for a specific mode."""
        return {
            name: meta
            for name, meta in cls._provider_metadata.items()
            if meta.get("mode") == mode
        }

    @classmethod
    def reset(cls) -> None:
        """Clear registry (for testing)."""
        cls._providers.clear()
        cls._provider_metadata.clear()


# Register providers on import
def _register_default_providers():
    """Auto-register default providers."""
    from .ollama_provider import OllamaProvider
    from .gemini_provider import GeminiProvider
    from .claude_provider import ClaudeProvider
    from .openai_provider import OpenAIProvider

    ProviderRegistry.register(
        name="ollama",
        provider_class=OllamaProvider,
        mode="private",
        requires_api_key=False,
    )

    ProviderRegistry.register(
        name="gemini",
        provider_class=GeminiProvider,
        mode="public",
        requires_api_key=True,
        api_key_env_var="GEMINI_API_KEY",
    )

    ProviderRegistry.register(
        name="claude",
        provider_class=ClaudeProvider,
        mode="public",
        requires_api_key=True,
        api_key_env_var="CLAUDE_API_KEY",
    )

    ProviderRegistry.register(
        name="openai",
        provider_class=OpenAIProvider,
        mode="public",
        requires_api_key=True,
        api_key_env_var="OPENAI_API_KEY",
    )


# Auto-register on module import
_register_default_providers()
