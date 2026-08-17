"""
DocVerify AI - Application Configuration
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DocVerify AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DEMO_MODE: bool = False

    # Security
    SECRET_KEY: str = "change-this-secret-key-in-production-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str = "sqlite:///./docverify.db"

    # Storage
    UPLOAD_DIR: str = "uploads"
    REPORT_DIR: str = "reports"
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png,pdf"

    # Feature Flags
    ENABLE_FACE_VERIFICATION: bool = False
    ENABLE_DEMO_WATERMARK: bool = True

    # OCR
    OCR_LANGUAGE: str = "en"
    OCR_GPU: bool = False

    # Logging
    LOG_LEVEL: str = "INFO"

    # Classification
    CLASSIFICATION_CONFIDENCE_SUPPORTED: float = 80.0
    CLASSIFICATION_CONFIDENCE_UNCERTAIN: float = 60.0

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(exist_ok=True)
        return p

    @property
    def report_path(self) -> Path:
        p = Path(self.REPORT_DIR)
        p.mkdir(exist_ok=True)
        return p

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_ext_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
