import os
from dataclasses import dataclass
from typing import Set


def _parse_admin_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    result: set[int] = set()
    for part in value.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            result.add(int(part))
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class Settings:
    telegram_token: str = os.environ.get("TELEGRAM_TOKEN", "")
    openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "")
    webhook_secret: str = os.environ.get("WEBHOOK_SECRET", "change-me-secret")
    openrouter_model: str = os.environ.get("OPENROUTER_IMAGE_MODEL", "google/gemini-3-pro-image")
    app_title: str = os.environ.get("APP_TITLE", "Telegram Nano Banana Pro Bot")
    max_prompt_chars: int = int(os.environ.get("MAX_PROMPT_CHARS", "1800"))
    max_parallel_generations: int = int(os.environ.get("MAX_PARALLEL_GENERATIONS", "2"))
    db_path: str = os.environ.get("DB_PATH", "bot_data.sqlite3")
    admin_user_ids: set[int] = None  # type: ignore[assignment]

    def __post_init__(self):
        object.__setattr__(self, "admin_user_ids", _parse_admin_ids(os.environ.get("ADMIN_USER_IDS")))


settings = Settings()
