from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    tmdb_read_token: str
    database_path: str = "movievoter.db"
    error_report_chat_id: int | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        bot_token = os.getenv("BOT_TOKEN", "").strip()
        tmdb_read_token = os.getenv("TMDB_READ_TOKEN", "").strip()
        error_report_chat_id_raw = os.getenv("ERROR_REPORT_CHAT_ID", "").strip()

        missing = [
            name
            for name, value in (
                ("BOT_TOKEN", bot_token),
                ("TMDB_READ_TOKEN", tmdb_read_token),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            bot_token=bot_token,
            tmdb_read_token=tmdb_read_token,
            database_path=os.getenv("DATABASE_PATH", "movievoter.db").strip() or "movievoter.db",
            error_report_chat_id=int(error_report_chat_id_raw) if error_report_chat_id_raw else None,
        )
