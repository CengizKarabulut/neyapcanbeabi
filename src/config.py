from __future__ import annotations

import os
from dataclasses import dataclass


def parse_chat_target(value: str) -> int | str:
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        return value


@dataclass(frozen=True)
class Settings:
    bot_token: str | None
    target_bot_username: str
    api_id: int | None
    api_hash: str | None
    session: str | None
    chat_target: int | str
    symbol: str
    commands: tuple[str, ...]
    command_delay_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        commands = tuple(
            part.strip().lstrip("/")
            for part in os.getenv("COMMANDS", "akd,derinlik,kurum").split(",")
            if part.strip()
        )
        if not commands:
            raise RuntimeError("COMMANDS en az bir komut içermeli.")

        symbol = os.getenv("SYMBOL", "ASELS").strip().upper()
        delay = float(os.getenv("COMMAND_DELAY_SECONDS", "10"))
        chat_target_raw = os.getenv("TELEGRAM_CHAT_ID", "@aselsanhissee").strip()
        if not chat_target_raw:
            raise RuntimeError("TELEGRAM_CHAT_ID boş olamaz.")

        target_bot_username = os.getenv(
            "TELEGRAM_TARGET_BOT_USERNAME",
            "ucretsizderinlikbot",
        ).strip().lstrip("@")

        api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()

        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None,
            target_bot_username=target_bot_username,
            api_id=int(api_id_raw) if api_id_raw else None,
            api_hash=os.getenv("TELEGRAM_API_HASH", "").strip() or None,
            session=os.getenv("TELEGRAM_SESSION", "").strip() or None,
            chat_target=parse_chat_target(chat_target_raw),
            symbol=symbol,
            commands=commands,
            command_delay_seconds=delay,
        )
