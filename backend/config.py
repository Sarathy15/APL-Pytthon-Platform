import platform
import shutil
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(".env") if Path(".env").exists() else Path(".env.example")
DEFAULT_DYALOG_EXECUTABLE = shutil.which("Dyalog.exe") or shutil.which("dyalog") or (
    r"C:\Program Files\Dyalog\Dyalog APL-64 20.0 Unicode\dyalog.exe"
    if platform.system() == "Windows" else "dyalog"
)

class Settings(BaseSettings):
    PROJECT_NAME: str = "APL Migration Platform"
    
    # AI Mode Configuration
    AI_MODE: str = "private"  # "private" or "public"
    AI_PROVIDER: str = "ollama"  # "ollama", "claude", "openai", "gemini"
    
    # Ollama (Private Mode)
    OLLAMA_URL: str = "http://localhost:11434"
    MODEL_NAME: str = "qwen2.5-coder:3b"
    
    # Claude (Public Mode)
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4"
    
    # OpenAI (Public Mode)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo"
    
    # Gemini (Public Mode)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-pro"
    
    # Database
    DB_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/apl_migration"
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Provider Timeouts (seconds) - per-provider configuration
    # Ollama supports longer timeouts for complex multiline APL
    # Public APIs need shorter timeouts for cost/latency reasons
    # Provider Timeouts (seconds) - per-provider configuration
    # Ollama supports longer timeouts for complex multiline APL
    # Public APIs need shorter timeouts for cost/latency reasons
    PROVIDER_TIMEOUTS: dict[str, int] = {
        "ollama": 120,   # was 60 - real prompt takes ~70s on qwen2.5-coder:3b
        "claude": 45,
        "openai": 45,
        "gemini": 45,
    }

    # Global fallback timeout
    TIMEOUT_SECONDS: int = 120
    RETRY_ATTEMPTS: int = 1  # was 2 - avoid retrying slow-but-working calls
    ENVIRONMENT: str = "development"
    DYALOG_EXECUTABLE: str = DEFAULT_DYALOG_EXECUTABLE
    PYTHON_EXECUTABLE: str = "python"
    OUTPUT_DIR: Path = Path("outputs")
    REPORTS_DIR: Path = OUTPUT_DIR / "reports"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), 
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from .env (like VITE_* frontend vars)
    )

settings = Settings()
