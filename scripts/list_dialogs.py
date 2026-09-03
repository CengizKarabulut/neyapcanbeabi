from __future__ import annotations

import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Eksik ortam değişkeni: {name}")
    return value


async def main() -> None:
    api_id = int(required("TELEGRAM_API_ID"))
    api_hash = required("TELEGRAM_API_HASH")
    session = required("TELEGRAM_SESSION")

    client = TelegramClient(StringSession(session), api_id, api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram oturumu yetkilendirilmemiş.")

        print("\nTelegram sohbetleri / grupları:\n")
        async for dialog in client.iter_dialogs():
            print(f"{dialog.id:>16} | {dialog.name}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
