import os
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
load_dotenv(root_dir / ".env")

class Settings:
    PROJECT_NAME: str = "Video2Doc MultiLang API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "video2doc-multilang-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./video2doc.db")
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")
    LOCAL_STORAGE_PATH: str = os.getenv("LOCAL_STORAGE_PATH", "./storage")

settings = Settings()
