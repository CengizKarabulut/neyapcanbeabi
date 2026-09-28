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

        return cls(
            bot_token=_required("TELEGRAM_BOT_TOKEN"),
            chat_target=chat_target,
            symbol=symbol,
            commands=commands,
            command_delay_seconds=delay,
        )
