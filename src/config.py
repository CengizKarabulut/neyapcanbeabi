from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Eksik ortam değişkeni: {name}")
    return value


def parse_chat_target(value: str) -> int | str:
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        return value


@dataclass(frozen=True)
class Settings:
    api_id: int
    api_hash: str
    session: str
    chat_target: int | str
    symbol: str
    commands: tuple[str, ...]
    command_delay_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        commands = tuple(
            part.strip().lstrip("/")
            for part in os.getenv("COMMANDS", "akd,derinlik").split(",")
            if part.strip()
        )
        if not commands:
            raise RuntimeError("COMMANDS en az bir komut içermeli.")

        symbol = os.getenv("SYMBOL", "ZGYO").strip().upper()
        delay = float(os.getenv("COMMAND_DELAY_SECONDS", "5"))

        return cls(
            api_id=int(_required("TELEGRAM_API_ID")),
            api_hash=_required("TELEGRAM_API_HASH"),
            session=_required("TELEGRAM_SESSION"),
            chat_target=parse_chat_target(_required("TELEGRAM_CHAT_ID")),
            symbol=symbol,
            commands=commands,
            command_delay_seconds=delay,
        )
