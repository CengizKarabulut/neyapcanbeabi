from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.errors import ChatIdInvalidError
from telethon.sessions import StringSession

from src.config import Settings

ISTANBUL = ZoneInfo("Europe/Istanbul")
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("telegram-market-commands")


def now_istanbul() -> str:
    return datetime.now(ISTANBUL).strftime("%Y-%m-%d %H:%M:%S %Z")


def web_k_to_telethon_id(chat_id: int) -> int | None:
    """Telegram Web K'daki -XXXXXXXXXX biçimini supergroup/channel peer ID'ye çevirir."""
    if chat_id >= 0:
        return None

    raw = str(abs(chat_id))
    if str(chat_id).startswith("-100"):
        return None

    return int(f"-100{raw}")


async def resolve_target(client: TelegramClient, chat_target: int | str):
    try:
        return await client.get_entity(chat_target)
    except ChatIdInvalidError:
        if not isinstance(chat_target, int):
            raise

        fallback = web_k_to_telethon_id(chat_target)
        if fallback is None:
            raise

        logger.warning(
            "Telegram Web chat ID biçimi algılandı: %s -> %s olarak yeniden deneniyor.",
            chat_target,
            fallback,
        )
        return await client.get_entity(fallback)


async def main() -> None:
    settings = Settings.from_env()
    messages = [f"/{command} {settings.symbol}" for command in settings.commands]

    client = TelegramClient(StringSession(settings.session), settings.api_id, settings.api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("TELEGRAM_SESSION geçerli değil veya yetkilendirilmemiş.")

        target = await resolve_target(client, settings.chat_target)
        logger.info(
            "[%s] Hedef hazır: %s (Telegram entity id=%s)",
            now_istanbul(),
            getattr(target, "title", settings.chat_target),
            getattr(target, "id", "?"),
        )

        for i, message in enumerate(messages):
            await client.send_message(target, message)
            logger.info("[%s] Gönderildi: %s", now_istanbul(), message)
            if i < len(messages) - 1 and settings.command_delay_seconds > 0:
                await asyncio.sleep(settings.command_delay_seconds)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
