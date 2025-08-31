# core/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Ścieżka do pliku .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "SkillSense API"
    PROJECT_VERSION: str = "7.0.0"

    # Ustawienia Bazy Danych
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # Ustawienia Bezpieczeństwa (JWT)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-that-should-be-in-env-file")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Ustawienia Uploadu Plików
    UPLOAD_DIR: Path = Path("uploads/cvs")
    MAX_FILE_SIZE_MB: int = 5
    ALLOWED_FILE_TYPES: list = ["application/pdf"]

settings = Settings()

# Upewnij się, że katalog do uploadu istnieje
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
