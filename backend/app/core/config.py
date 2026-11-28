from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
STORAGE_DIR = PROJECT_DIR / "storage"


class Settings(BaseSettings):

    APP_NAME: str = "DocuMind AI"
    APP_VERSION: str = "2.0.0"

    LM_STUDIO_BASE_URL: str = "http://localhost:1234/v1"
    LM_STUDIO_MODEL: str = "auto"

    MAX_UPLOAD_SIZE_MB: int = 50

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        extra="ignore"
    )


settings = Settings()

UPLOAD_DIR = STORAGE_DIR / "uploads"
EXTRACTED_DIR = STORAGE_DIR / "extracted"
DATABASE_DIR = STORAGE_DIR / "database"

for directory in [
    UPLOAD_DIR,
    EXTRACTED_DIR,
    DATABASE_DIR
]:
    directory.mkdir(parents=True, exist_ok=True)