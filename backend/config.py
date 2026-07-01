import os
from dataclasses import dataclass
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parent / ".env"


def _read_env_value(key: str) -> str | None:
    if not ENV_FILE.is_file():
        return None

    for raw_line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        name, value = line.split("=", maxsplit=1)
        if name.strip() == key:
            return value.strip().strip("\"'")

    return None


@dataclass(frozen=True)
class Settings:
    database_url: str


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL") or _read_env_value("DATABASE_URL")
    if not database_url:
        raise RuntimeError(f"DATABASE_URL is not configured in {ENV_FILE}.")

    return Settings(database_url=database_url)


settings = get_settings()
