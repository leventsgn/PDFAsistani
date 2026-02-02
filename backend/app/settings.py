from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/rag")
    files_dir: str = os.getenv("FILES_DIR", "../storage")

    embeddings_provider: str = os.getenv("EMBEDDINGS_PROVIDER", "none")  # none | openai_compatible
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "changeme")
    openai_model: str = os.getenv("OPENAI_MODEL", "text-embedding-3-small")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "1536"))

    chat_base_url: str = os.getenv("CHAT_BASE_URL", "http://localhost:11434/v1")
    chat_api_key: str = os.getenv("CHAT_API_KEY", "changeme")
    chat_model: str = os.getenv("CHAT_MODEL", "gpt-oss-20b")

settings = Settings()

class RuntimeSettings(BaseModel):
    chat_base_url: str | None = None
    chat_api_key: str | None = None
    chat_model: str | None = None

runtime_settings = RuntimeSettings()

def get_chat_settings() -> dict:
    return {
        "chat_base_url": runtime_settings.chat_base_url or settings.chat_base_url,
        "chat_api_key": runtime_settings.chat_api_key or settings.chat_api_key,
        "chat_model": runtime_settings.chat_model or settings.chat_model,
    }

def update_chat_settings(data: dict) -> RuntimeSettings:
    for key in ["chat_base_url", "chat_api_key", "chat_model"]:
        if key in data and data[key] is not None:
            setattr(runtime_settings, key, data[key])
    return runtime_settings
