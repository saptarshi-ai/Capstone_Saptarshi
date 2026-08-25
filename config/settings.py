"""
Configuration Settings.
Loads all environment variables from .env using Pydantic BaseSettings.
Supports OpenAI (default) OR Ollama local (set USE_OLLAMA=true in .env).
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE_PATH, env_file_encoding="utf-8", extra="ignore")

    # --- OpenAI (Vocareum key) ---
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-ada-002"

    # --- Ollama (local, free, already set up on your machine) ---
    USE_OLLAMA: bool = False                          # set to true in .env to go local
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"  # ollama pull nomic-embed-text

    # --- RAG chunking ---
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # --- Storage ---
    DB_PATH: str = "data/db/eval_runs.db"
    CHROMA_PATH: str = "data/db/chroma"

    @property
    def llm_base_url(self) -> str:
        return self.OLLAMA_BASE_URL if self.USE_OLLAMA else self.OPENAI_BASE_URL

    @property
    def llm_api_key(self) -> str:
        return "ollama" if self.USE_OLLAMA else self.OPENAI_API_KEY

    @property
    def llm_model(self) -> str:
        return self.OLLAMA_MODEL if self.USE_OLLAMA else self.DEFAULT_MODEL

settings = Settings()
