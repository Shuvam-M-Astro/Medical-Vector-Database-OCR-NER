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
    
    # Retry and Circuit Breaker Settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_BASE_DELAY: float = 1.0  # seconds
    RETRY_MAX_DELAY: float = 60.0  # seconds
    RETRY_EXPONENTIAL_BASE: float = 2.0
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60  # seconds
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: bool = True
    
    # Health Check Settings
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 10  # seconds
    UNHEALTHY_THRESHOLD: int = 3
    
    # Resource Management
    MAX_MEMORY_USAGE: int = 80  # percentage
    DISK_SPACE_THRESHOLD: int = 90  # percentage
    TEMP_FILE_CLEANUP_INTERVAL: int = 3600  # seconds
    
    # Monitoring and Alerting
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    ALERT_EMAIL: Optional[str] = None
    SLACK_WEBHOOK_URL: Optional[str] = None
    
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