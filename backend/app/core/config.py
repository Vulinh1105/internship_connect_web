"""Đọc cấu hình từ biến môi trường hoặc file .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

# Tự tìm file .env từ thư mục hiện tại lên các thư mục cha
load_dotenv(Path(__file__).resolve().parents[3] / ".env")

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class Settings:
    # --- Cơ sở dữ liệu ---
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/internship_connect?charset=utf8mb4",
    )
    AUTO_CREATE_TABLES: bool = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"

    # --- JWT ---
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-only-secret-change-me-please-0123456789")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # --- Web ---
    CORS_ORIGINS: list[str] = _split(os.getenv("CORS_ORIGINS", "*"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "data" / "runtime" / "uploads"))

    # --- AI ---
    VECTOR_BACKEND: str = os.getenv("VECTOR_BACKEND", "auto")  # auto | qdrant | memory
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", str(BACKEND_DIR / "qdrant_data"))
    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "openai")  # openai | hashing | sentence_transformers
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    OPENAI_TIMEOUT: float = float(os.getenv("OPENAI_TIMEOUT", "45"))
    OPENAI_MAX_RETRIES: int = int(os.getenv("OPENAI_MAX_RETRIES", "1"))


settings = Settings()
