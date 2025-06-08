from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Local LLM
    OLLAMA_BASE_URL: str
    LLM_MODEL: str
    MAX_TOKENS: int
    TEMPERATURE: float

    # Vector Database
    VECTOR_DB_PATH: str
    EMBEDDING_MODEL: str
    CHUNK_SIZE: int
    CHUNK_OVERLAP: int

    # OCR Settings
    TESSERACT_PATH: Optional[str]
    POPPLER_PATH: Optional[str]
    DPI: int

    # Streaming
    STREAM_DELAY: float

    # Debug
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()