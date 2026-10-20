import os
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_REDIS_URL = "redis://backend-redis:6379/0"
DEFAULT_CORS_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")
_DB_VARS = ("POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "PGPORT", "POSTGRES_DB")


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    storage_dir: Path
    cors_origins: tuple[str, ...]


def load_settings(env: Mapping[str, str]) -> Settings:
    database_url = env.get("DATABASE_URL")
    if not database_url:
        missing = [name for name in _DB_VARS if not env.get(name)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        user, password = quote(env["POSTGRES_USER"], safe=""), quote(env["POSTGRES_PASSWORD"], safe="")
        database_url = (
            f"postgresql+asyncpg://{user}:{password}@{env['POSTGRES_HOST']}:{env['PGPORT']}/{env['POSTGRES_DB']}"
        )

    origins = env.get("CORS_ORIGINS")
    cors_origins = (
        tuple(o.strip() for o in origins.split(",") if o.strip()) if origins else DEFAULT_CORS_ORIGINS
    )
    return Settings(
        database_url=database_url,
        redis_url=env.get("REDIS_URL") or DEFAULT_REDIS_URL,
        storage_dir=Path(env["STORAGE_DIR"]) if env.get("STORAGE_DIR") else BASE_DIR / "storage" / "files",
        cors_origins=cors_origins,
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings(os.environ)
