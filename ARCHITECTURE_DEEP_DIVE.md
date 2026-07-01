## Architecture Deep Dive - Developer Reference

### 📚 Table of Contents
1. [System Architecture](#system-architecture)
2. [Provider Interface](#provider-interface)
3. [Factory Pattern](#factory-pattern)
4. [Provider Registry](#provider-registry)
5. [Error Handling](#error-handling)
6. [Adding New Providers](#adding-new-providers)
7. [Testing Strategy](#testing-strategy)

---

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────┐
│         Frontend / CLI              │
│   (User inputs APL code)            │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│    UnderstandingAgent.analyze()     │
│  (Parse APL semantics)              │
└────────────────┬────────────────────┘
                 │
                 ↓
     ┌───────────────────────┐
     │ ProviderFactory       │
     │ .get_provider()       │
     └───────────────────────┘
          │
    ┌─────┴─────┐
    ↓           ↓
  Config      Registry
  AI_MODE     Metadata
  AI_PROVIDER
    │
    ├─ private → OllamaProvider
    ├─ public + gemini → GeminiProvider
    ├─ public + claude → ClaudeProvider
    └─ public + openai → OpenAIProvider
                 │
                 ↓
      ┌──────────────────────┐
      │   Provider           │
      │   async generate()   │
      └──────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│   AI Backend (Ollama/Gemini/etc)    │
│   (Generates Python code)           │
└─────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│    ConversionAgent.convert()        │
│  (Validate & format response)       │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│      PythonRunner.execute()         │
│  (Run generated code, validate)     │
└────────────────┬────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────┐
│      Output & Results               │
│   (Confidence scores, traces)       │
└─────────────────────────────────────┘
```

---

## Provider Interface

### BaseProvider Abstract Class

```python
class BaseProvider(ABC):
    """All providers must implement this interface."""
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system: str = ""
    ) -> dict[str, Any]:
        """
        Generate a response from the provider.
        
        Args:
            prompt: User/task prompt
            system: System/instruction prompt
            
        Returns:
            {
                "response": str,        # Generated text
                "error": str,           # (optional) Error message
                "detail": str,          # (optional) Error details
                "finish_reason": str,   # (optional) Completion reason
                "usage": dict,          # (optional) Token usage
            }
        """
        pass
    
    @staticmethod
    def normalize_response(
        data: dict[str, Any], 
        response_type: str = "conversion"
    ) -> dict[str, Any]:
        """Normalize provider output to standard schema."""
        # Converts raw provider response to standard format
        # Ensures consistent structure across all providers
```

### Response Format Standards

#### For APL Understanding
```json
{
    "operator": "+/",
    "meaning": "sum all elements",
    "category": "reduction",
    "explanation": "APL reduction operator...",
    "confidence": 0.95
}
```

#### For Python Conversion
```json
{
    "python_code": "import numpy as np\nresult = np.sum(A)",
    "explanation": "Converts APL sum reduction to NumPy...",
    "confidence_score": 92,
    "syntax_valid": true
}
```

---

## Factory Pattern

### ProviderFactory Class

```python
class ProviderFactory:
    """
    Factory for creating and routing to correct provider.
    
    Responsibilities:
    1. Read AI_MODE and AI_PROVIDER from config
    2. Validate provider configuration
    3. Check API keys are configured
    4. Create appropriate provider instance
    5. Cache provider (avoid recreation)
    6. Handle errors gracefully
    """
    
    _provider_cache: Optional[BaseProvider] = None
    _current_mode: Optional[str] = None
    _current_provider: Optional[str] = None
    
    @staticmethod
    def get_provider() -> BaseProvider:
        """Main entry point for getting a provider."""
        # 1. Check cache first
        if cache_valid():
            return _provider_cache
        
        # 2. Validate configuration
        validate_provider_config()
        
        # 3. Route based on mode and provider
        if AI_MODE == "private":
            provider = OllamaProvider()
        elif AI_MODE == "public":
            if AI_PROVIDER == "gemini":
                provider = GeminiProvider()
            elif AI_PROVIDER == "claude":
                provider = ClaudeProvider()
            # ... etc
        
        # 4. Cache and return
        _provider_cache = provider
        return provider
    
    @staticmethod
    def reset_cache():
        """Clear cache (for testing/switching providers)."""
        _provider_cache = None
        _current_mode = None
        _current_provider = None
```

### Flow with Error Handling

```
get_provider()
    ↓
Is cache valid? → YES → Return cached provider
    ↓ NO
Validate configuration
    ↓ Invalid (e.g., API key missing)
    ↓ Raise ScaffoldedProviderError
    ↓ (Agent catches → falls back to semantics)
    ↓ Valid
Create appropriate provider instance
    ↓ Import error?
    ↓ Raise ImportError (package not installed)
    ↓ No errors
Cache provider instance
    ↓
Return provider
```

---

## Provider Registry

### ProviderRegistry Metadata

```python
class ProviderRegistry:
    """Centralized provider metadata and discovery."""
    
    _providers: Dict[str, Type[BaseProvider]] = {}
    _provider_metadata: Dict[str, Dict[str, Any]] = {}
    
    # Example registry entry:
    {
        "ollama": {
            "name": "ollama",
            "mode": "private",
            "requires_api_key": False,
            "api_key_env_var": ""
        },
        "gemini": {
            "name": "gemini",
            "mode": "public",
            "requires_api_key": True,
            "api_key_env_var": "GEMINI_API_KEY"
        }
    }
```

### Registry Usage

```python
# List all providers
providers = ProviderRegistry.list_providers()

# Check if provider requires configuration
if ProviderRegistry.get_provider_metadata("claude").get("requires_api_key"):
    # Check if API key is set
    api_key = getattr(settings, "CLAUDE_API_KEY", "")
    if not api_key:
        raise ScaffoldedProviderError("CLAUDE_API_KEY not configured")

# Get providers by mode
private = ProviderRegistry.get_providers_by_mode("private")  # [ollama]
public = ProviderRegistry.get_providers_by_mode("public")    # [gemini, claude, openai]
```

---

## Error Handling

### Error Hierarchy

```
Exception
├── ScaffoldedProviderError
│   └── Provider registered but API key not configured
│       Example: "Claude provider scaffolded but API not configured yet. 
│                Set CLAUDE_API_KEY environment variable."
│
├── ImportError
│   └── Required package not installed
│       Example: "anthropic package required. Install with: pip install anthropic"
│
└── ValueError
    ├── Invalid AI_MODE
    └── Invalid AI_PROVIDER
```

### Error Handling in Agents

```python
@staticmethod
async def convert(apl_code: str, understanding: dict[str, Any]) -> dict[str, Any]:
    try:
        provider = ProviderFactory.get_provider()
    except ScaffoldedProviderError as exc:
        # Provider not configured yet - fallback is available
        logger.warning(f"Provider not configured: {exc}")
        return {
            "python_code": "",
            "explanation": str(exc),
            "confidence_score": 0.0,
            "error": "provider_not_configured"
        }
    except Exception as exc:
        # Other errors
        logger.error(f"Provider error: {exc}")
        return {
            "python_code": "",
            "explanation": f"Failed to initialize AI provider: {str(exc)}",
            "confidence_score": 0.0,
            "error": "provider_error"
        }
    
    # Provider is available, proceed with generation...
    result = await provider.generate(user_prompt, system_prompt)
    
    # Check provider response for errors
    if "error" in result:
        # Provider returned an error
        logger.error(f"Provider error: {result.get('detail')}")
        return handle_provider_error(result)
    
    # Parse and validate response...
```

---

## Adding New Providers

### Step-by-Step Guide

#### 1. Create Provider Class

**File**: `backend/providers/vertex_provider.py`

```python
"""Google Vertex AI provider."""

from typing import Any
from ..utils.logger import get_logger
from ..config import settings
from .base_provider import BaseProvider

logger = get_logger(__name__)

class VertexProvider(BaseProvider):
    """Provider for Google Vertex AI API."""
    
    def __init__(self):
        """Initialize with credentials."""
        self.project_id = settings.VERTEX_PROJECT_ID
        self.location = settings.VERTEX_LOCATION or "us-central1"
        
        if not self.project_id:
            raise ValueError("VERTEX_PROJECT_ID not set in environment")
        
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            vertexai.init(
                project=self.project_id,
                location=self.location
            )
            self.client = GenerativeModel("gemini-pro")
        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform required. "
                "Install with: pip install google-cloud-aiplatform"
            )
    
    async def generate(self, prompt: str, system: str = "") -> dict[str, Any]:
        """Generate response from Vertex AI."""
        try:
            # Combine prompts
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            
            # Call Vertex AI (sync call wrapped in async)
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.generate_content(full_prompt)
            )
            
            return {
                "response": response.text,
                "finish_reason": "stop"
            }
        except Exception as exc:
            logger.error(f"Vertex AI error: {exc}")
            return {"error": "Vertex AI request failed", "detail": str(exc)}
```

#### 2. Update Configuration

**File**: `backend/config.py`

```python
# Add new settings
VERTEX_PROJECT_ID: str = ""
VERTEX_LOCATION: str = "us-central1"
```

#### 3. Register Provider

**File**: `backend/providers/provider_registry.py` (in `_register_default_providers()`)

```python
from .vertex_provider import VertexProvider

ProviderRegistry.register(
    name="vertex",
    provider_class=VertexProvider,
    mode="public",
    requires_api_key=True,
    api_key_env_var="VERTEX_PROJECT_ID",  # Actually project ID, not key
)
```

#### 4. Update Factory

**File**: `backend/providers/provider_factory.py` (in `get_provider()`)

```python
elif current_provider_name == "vertex":
    logger.info("Using PUBLIC mode with Vertex AI")
    ProviderFactory._provider_cache = VertexProvider()
    ProviderFactory._current_provider = "vertex"
else:
    raise ValueError(
        f"Invalid AI_PROVIDER '{current_provider_name}'. "
        "Must be one of: claude, openai, gemini, vertex"
    )
```

#### 5. Update .env.example

```bash
# Vertex AI Configuration
VERTEX_PROJECT_ID=""
VERTEX_LOCATION="us-central1"
```

#### 6. Test

```python
import os
os.environ["AI_MODE"] = "public"
os.environ["AI_PROVIDER"] = "vertex"
os.environ["VERTEX_PROJECT_ID"] = "your-project-id"

from backend.providers.provider_factory import ProviderFactory
provider = ProviderFactory.get_provider()
# Now you can use it!
```

---

## Testing Strategy

### Unit Testing Providers

```python
import pytest
from backend.providers.vertex_provider import VertexProvider

@pytest.fixture
def vertex_provider():
    """Create provider fixture."""
    # Mock credentials
    os.environ["VERTEX_PROJECT_ID"] = "test-project"
    return VertexProvider()

@pytest.mark.asyncio
async def test_vertex_generate(vertex_provider):
    """Test Vertex AI generation."""
    prompt = "What is 2+2?"
    result = await vertex_provider.generate(prompt)
    
    assert "response" in result or "error" in result
    assert isinstance(result, dict)
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_pipeline_vertex():
    """Test full pipeline with Vertex provider."""
    os.environ["AI_MODE"] = "public"
    os.environ["AI_PROVIDER"] = "vertex"
    os.environ["VERTEX_PROJECT_ID"] = "test-project"
    
    ProviderFactory.reset_cache()
    
    # Test understanding
    understanding = await UnderstandingAgent.analyze("+/A")
    assert understanding["operator"] == "+/"
    
    # Test conversion
    conversion = await ConversionAgent.convert("+/A", understanding)
    assert "np.sum" in conversion["python_code"]
```

### Testing Scaffolded Providers

```python
def test_scaffolded_vertex_not_configured():
    """Test that unconfigured Vertex shows clear message."""
    # Remove configuration
    os.environ["AI_MODE"] = "public"
    os.environ["AI_PROVIDER"] = "vertex"
    if "VERTEX_PROJECT_ID" in os.environ:
        del os.environ["VERTEX_PROJECT_ID"]
    
    ProviderFactory.reset_cache()
    
    with pytest.raises(ScaffoldedProviderError) as exc_info:
        ProviderFactory.get_provider()
    
    assert "VERTEX_PROJECT_ID" in str(exc_info.value)
```

---

## Configuration Schema

### Settings Model

```python
class Settings(BaseSettings):
    # Mode
    AI_MODE: str = "private"  # "private" or "public"
    AI_PROVIDER: str = "ollama"  # "ollama", "gemini", "claude", "openai", "vertex", ...
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen2.5-coder:3b"
    
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"
    
    # Claude
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    
    # Vertex AI (future)
    VERTEX_PROJECT_ID: str = ""
    VERTEX_LOCATION: str = "us-central1"
    
    # ... more settings
```

---

## Performance Considerations

### Provider Caching
- **Why**: Avoid recreating provider instances
- **How**: Factory caches based on (AI_MODE, AI_PROVIDER)
- **Invalidation**: `ProviderFactory.reset_cache()` when config changes

### Async/Await
- **Why**: Non-blocking operations, better concurrency
- **Pattern**: All provider methods are async
- **Wrapping sync**: Use `asyncio.run_in_executor()` for sync APIs

### Retry Logic
- **Ollama**: Exponential backoff with configurable retries
- **Others**: Provider-specific retry strategies
- **Config**: `RETRY_ATTEMPTS` and `TIMEOUT_SECONDS`

---

## Monitoring and Logging

### Log Levels
```python
logger.info("Using PUBLIC mode with Gemini")  # Configuration info
logger.warning("Provider error, falling back to semantics")  # Non-fatal
logger.error("Claude API error: 401 Unauthorized")  # Errors
```

### Debugging
```python
from backend.utils.logger import get_logger
logger = get_logger(__name__)

# Enable debug logging
os.environ["LOG_LEVEL"] = "DEBUG"
```

---

## Key Takeaways

1. **Factory Pattern**: Abstracts provider creation and routing
2. **Registry Pattern**: Centralized metadata management
3. **Strategy Pattern**: Each provider implements same interface
4. **Error Handling**: Graceful degradation with clear messages
5. **Async-First**: All operations are non-blocking
6. **Extensible**: Adding new providers is straightforward
7. **Type-Safe**: Full type hints throughout
8. **Testable**: Clear separation of concerns

This architecture ensures the system can:
- ✅ Support multiple AI backends
- ✅ Switch providers without code changes
- ✅ Handle provider failures gracefully
- ✅ Scale to new providers easily
- ✅ Maintain backward compatibility
