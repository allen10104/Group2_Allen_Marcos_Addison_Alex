"""Application configuration.

Everything environment-specific lives here and nowhere else. No other module reads
os.environ directly — they import `settings` from here. One place to see every knob,
and the Lambda (which gets config from AWS env vars, not a .env file) works with zero
code changes.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# backend/app/config.py -> backend/ -> the project root, where .env lives.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _load_env_file() -> None:
    """Load `.env` into os.environ. Local development only.

    Runs at import, BEFORE the Settings dataclass below is defined, because its
    field defaults call os.getenv while the class body is being executed.

    `override=False` means a real environment variable always beats the file, so
    the Lambda's AWS-provided env vars win and this is a no-op there. python-dotenv
    is a dev dependency and Lambda has no .env, so either one being absent is the
    normal deployed case, not an error.
    """
    if not ENV_FILE.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError:
        return
    # utf-8-sig, not utf-8: this .env is saved with a BOM, which would otherwise
    # end up inside the first variable's NAME (\ufeffMONGODB_URI) and that key
    # would then never be found by os.getenv("MONGODB_URI").
    load_dotenv(ENV_FILE, override=False, encoding="utf-8-sig")


_load_env_file()


def _split_csv(raw: str) -> list[str]:
    """Turn "a, b ,c" into ["a","b","c"], dropping blanks.

    Trimming matters: a stray space in an env var is invisible and silently breaks a
    CORS origin match."""
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "noticeboard")

    # DEV-ONLY fallback. On AWS this comes from a Lambda environment variable.
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-only-insecure-secret-change-me")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    cors_allowed_origins: list[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:4173")
        )
    )

    # "memory" for Phase 2, "mongo" from Phase 3 on. Swapping the entire persistence
    # layer is this one value.
    repository: str = os.getenv("REPOSITORY", "memory")


settings = Settings()

