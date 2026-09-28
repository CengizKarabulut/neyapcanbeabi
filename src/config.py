from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Eksik ortam değişkeni: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    chat_target: str
    target_bot_username: str
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
        chat_target = os.getenv("TELEGRAM_CHAT_ID", "@aselsanhissee").strip()
        if not chat_target:
            raise RuntimeError("TELEGRAM_CHAT_ID boş olamaz.")

        target_bot_username = os.getenv(
            "TELEGRAM_TARGET_BOT_USERNAME",
            "ucretsizderinlikbot",
        ).strip().lstrip("@")
        if not target_bot_username:
            raise RuntimeError("TELEGRAM_TARGET_BOT_USERNAME boş olamaz.")

        return cls(
            bot_token=_required("TELEGRAM_BOT_TOKEN"),
            chat_target=chat_target,
            target_bot_username=target_bot_username,
            symbol=symbol,
            commands=commands,
            command_delay_seconds=delay,
        )
