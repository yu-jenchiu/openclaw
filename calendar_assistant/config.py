"""Configuration helpers for the calendar assistant."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(slots=True)
class Settings:
    """Runtime configuration sourced from env vars or sensible defaults."""

    calendar_id: str = os.getenv("CALENDAR_ID", "")
    service_account_path: Path = Path(
        os.getenv("SERVICE_ACCOUNT_PATH", "secrets/service-account.json")
    )
    service_account_json: str = os.getenv("SERVICE_ACCOUNT_JSON", "")
    timezone: str = os.getenv("CALENDAR_TIMEZONE", "Asia/Taipei")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    @classmethod
    def load(cls) -> "Settings":
        settings = cls()
        settings.validate()
        return settings

    def validate(self) -> None:
        if not self.service_account_json and not self.service_account_path.exists():
            print(
                f"[config] Warning: service account credentials not found. "
                f"Set SERVICE_ACCOUNT_JSON 或建立 {self.service_account_path}."
            )
        if not self.calendar_id:
            print("[config] Warning: CALENDAR_ID is empty; write operations will fail.")

    def llm_enabled(self) -> bool:
        return bool(self.openai_api_key)

    def service_account_file(self) -> Path:
        return self.service_account_path.resolve()

    def service_account_info(self) -> Optional[dict]:
        if not self.service_account_json:
            return None
        return json.loads(self.service_account_json)


settings = Settings.load()
