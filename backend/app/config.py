from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"

# Ensure runtime directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)



class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Ollama settings (default local)
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.1:latest"
    ollama_embed_model: str = "nomic-embed-text"

    # Groq API settings (fallback cloud option)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Preferred provider: 'auto', 'ollama', 'groq', 'offline'
    preferred_provider: str = "auto"

    # Vector DB settings
    chroma_collection_name: str = "study_documents"
    chunk_size: int = 800
    chunk_overlap: int = 150

    # Security & CORS
    allowed_origins: list[str] | str = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://localhost",
    ]
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25MB
    rate_limit_default: str = "120/minute"
    rate_limit_upload: str = "15/minute"
    rate_limit_chat: str = "45/minute"

    # Logging
    log_level: str = "INFO"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = AppSettings()
