"""
Configuration settings for the medical vector database application.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "Medical Vector Database API"
    API_VERSION: str = "1.0.0"
    
    # Database Settings
    CHROMA_DB_PATH: str = "./data/chroma_db"
    VECTOR_DIMENSION: int = 768
    
    # OCR Settings
    OCR_LANGUAGE: str = "eng"
    OCR_CONFIG: str = "--psm 6"
    TESSERACT_PATH: Optional[str] = None
    
    # NER Settings
    NER_MODEL: str = "en_core_web_sm"
    MEDICAL_NER_MODEL: str = "en_core_sci_md"
    CONFIDENCE_THRESHOLD: float = 0.7
    
    # File Processing
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"]
    UPLOAD_DIR: str = "./data/raw"
    PROCESSED_DIR: str = "./data/processed"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Processing
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 4
    
    # Critical Performance Settings
    REQUEST_TIMEOUT: int = 30  # seconds
    CONNECTION_POOL_SIZE: int = 20
    MAX_CONCURRENT_REQUESTS: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [
        settings.UPLOAD_DIR,
        settings.PROCESSED_DIR,
        settings.CHROMA_DB_PATH,
        os.path.dirname(settings.LOG_FILE),
        "./data/models",
        "./logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
ensure_directories() 