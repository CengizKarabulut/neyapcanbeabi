from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.sessions import StringSession

from src.config import Settings

ISTANBUL = ZoneInfo("Europe/Istanbul")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("telegram-market-commands")


def now_istanbul() -> str:
    return datetime.now(ISTANBUL).strftime("%Y-%m-%d %H:%M:%S %Z")


async def main() -> None:
    settings = Settings.from_env()
    messages = [f"/{command} {settings.symbol}" for command in settings.commands]

    client = TelegramClient(StringSession(settings.session), settings.api_id, settings.api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("TELEGRAM_SESSION geçerli değil veya yetkilendirilmemiş.")

        target = await client.get_entity(settings.chat_target)
        logger.info("[%s] Hedef hazır: %s", now_istanbul(), settings.chat_target)

        for i, message in enumerate(messages):
            await client.send_message(target, message)
            logger.info("[%s] Gönderildi: %s", now_istanbul(), message)
            if i < len(messages) - 1 and settings.command_delay_seconds > 0:
                await asyncio.sleep(settings.command_delay_seconds)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
