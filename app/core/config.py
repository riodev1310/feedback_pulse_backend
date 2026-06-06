from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def _default_sample_workbook() -> str | None:
    candidate = Path("/Users/vietannguyen/Downloads/TongHopYKien_Hocky2,nam2022-2023.xlsx")
    return str(candidate) if candidate.exists() else None


def _default_trained_model_path() -> str:
    candidates = [
        BASE_DIR / "model" / "vsfc_tfidf_svm_pipeline.pkl",
        BASE_DIR.parent / "trained_model" / "vsfc_tfidf_svm_pipeline.pkl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(candidates[0])


def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://127.0.0.1:3000,http://localhost:3000")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _database_url() -> str:
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url.strip()

    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    sslmode = os.getenv("POSTGRES_SSLMODE", "require").strip()

    if host and port and database and user and password:
        return (
            f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}@"
            f"{host}:{port}/{database}?sslmode={quote_plus(sslmode)}"
        )

    sqlite_path = BASE_DIR / "app.db"
    return f"sqlite+pysqlite:///{sqlite_path}"


@dataclass(frozen=True)
class Settings:
    app_name: str = "Feedback Pulse API"
    api_prefix: str = "/api"
    cors_origins: list[str] = None  # type: ignore[assignment]
    sample_workbook_path: str | None = None
    sentiment_provider: str = "openai"
    openai_sentiment_model: str = "ft:gpt-4o-mini-2024-07-18:personal::Cje33mEn"
    openai_api_key: str | None = None
    openai_sentiment_batch_size: int = 20
    openai_request_timeout_seconds: float = 45.0
    trained_model_sentiment_model_path: str = ""
    show_label_progress: bool = False
    database_url: str = ""
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7
    auth_cookie_name: str = "feedback_pulse_session"
    auth_cookie_secure: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "cors_origins", _cors_origins())
        object.__setattr__(
            self,
            "sample_workbook_path",
            os.getenv("SAMPLE_WORKBOOK_PATH") or _default_sample_workbook(),
        )
        object.__setattr__(
            self,
            "sentiment_provider",
            os.getenv("SENTIMENT_PROVIDER", "openai").strip().lower(),
        )
        object.__setattr__(
            self,
            "openai_sentiment_model",
            os.getenv(
                "OPENAI_SENTIMENT_MODEL",
                "ft:gpt-4o-mini-2024-07-18:personal::Cje33mEn",
            ).strip(),
        )
        object.__setattr__(self, "openai_api_key", os.getenv("OPENAI_API_KEY"))
        object.__setattr__(
            self,
            "openai_sentiment_batch_size",
            max(1, int(os.getenv("OPENAI_SENTIMENT_BATCH_SIZE", "20"))),
        )
        object.__setattr__(
            self,
            "openai_request_timeout_seconds",
            float(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "45")),
        )
        object.__setattr__(
            self,
            "trained_model_sentiment_model_path",
            (
                os.getenv("TRAINED_MODEL_SENTIMENT_MODEL_PATH")
                or os.getenv("PICKLE_SENTIMENT_MODEL_PATH")
                or _default_trained_model_path()
            ).strip(),
        )
        object.__setattr__(
            self,
            "show_label_progress",
            os.getenv("SHOW_LABEL_PROGRESS", "false").strip().lower() in {"1", "true", "yes", "on"},
        )
        object.__setattr__(self, "database_url", _database_url())
        object.__setattr__(self, "jwt_secret", os.getenv("JWT_SECRET", "change-me-in-production"))
        object.__setattr__(self, "jwt_algorithm", os.getenv("JWT_ALGORITHM", "HS256"))
        object.__setattr__(
            self,
            "access_token_expire_minutes",
            int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))),
        )
        object.__setattr__(
            self,
            "auth_cookie_name",
            os.getenv("AUTH_COOKIE_NAME", "feedback_pulse_session"),
        )
        object.__setattr__(
            self,
            "auth_cookie_secure",
            os.getenv("AUTH_COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"},
        )


settings = Settings()
