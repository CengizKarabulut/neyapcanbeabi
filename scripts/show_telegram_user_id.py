from __future__ import annotations

import asyncio
import os

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main() -> None:
    api_id_raw = os.getenv("TELEGRAM_API_ID", "").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
    session = os.getenv("TELEGRAM_SESSION", "").strip()

    if not api_id_raw or not api_hash or not session:
        raise RuntimeError("TELEGRAM_API_ID, TELEGRAM_API_HASH ve TELEGRAM_SESSION secret'ları gerekli.")

    client = TelegramClient(StringSession(session), int(api_id_raw), api_hash)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("Telegram kullanıcı oturumu yetkili değil.")

        me = await client.get_me()
        print(f"Telegram User ID: {me.id}")
        print(f"Username: @{me.username}" if me.username else "Username: -")
        print("Bu User ID, botla özel sohbet için TELEGRAM_APPROVAL_CHAT_ID olarak kullanılabilir.")
    finally:
        if client.is_connected():
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
