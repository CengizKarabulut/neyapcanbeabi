from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.sessions import StringSession

from src.config import Settings
from src.main import ISTANBUL, now_istanbul, resolve_target

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("telegram-minute-commands")


def parse_end_time(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None

    parts = [int(part) for part in value.split(":")]
    if len(parts) == 2:
        hour, minute = parts
        second = 59
    elif len(parts) == 3:
        hour, minute, second = parts
    else:
        raise ValueError("WINDOW_END HH:MM veya HH:MM:SS biçiminde olmalı.")

    now = datetime.now(ISTANBUL)
    return now.replace(hour=hour, minute=minute, second=second, microsecond=0)


async def send_with_flood_wait(client: TelegramClient, target, message: str) -> None:
    while True:
        try:
            await client.send_message(target, message)
            logger.info("[%s] Gönderildi: %s", now_istanbul(), message)
            return
        except FloodWaitError as exc:
            wait_seconds = int(exc.seconds) + 1
            logger.warning("Telegram FloodWait: %s saniye beklenecek.", wait_seconds)
            await asyncio.sleep(wait_seconds)


async def main() -> None:
    settings = Settings.from_env()
    messages = [f"/{command} {settings.symbol}" for command in settings.commands]
    max_cycles = int(os.getenv("MAX_CYCLES", "0") or "0")
    end_at = parse_end_time(os.getenv("WINDOW_END", ""))

    if end_at and datetime.now(ISTANBUL) > end_at:
        logger.info("[%s] Çalışma penceresi zaten sona ermiş: %s", now_istanbul(), end_at.isoformat())
        return

    client = TelegramClient(StringSession(settings.session), settings.api_id, settings.api_hash)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise RuntimeError("TELEGRAM_SESSION geçerli değil veya yetkilendirilmemiş.")

        target = await resolve_target(client, settings.chat_target)
        logger.info(
            "[%s] Dakikalık akış başladı: %s | sembol=%s | bitiş=%s | max_cycles=%s",
            now_istanbul(),
            getattr(target, "title", settings.chat_target),
            settings.symbol,
            end_at.isoformat() if end_at else "manuel",
            max_cycles or "sınırsız",
        )

        loop = asyncio.get_running_loop()
        cycles = 0

        while True:
            if end_at and datetime.now(ISTANBUL) > end_at:
                break
            if max_cycles and cycles >= max_cycles:
                break

            cycle_started = loop.time()

            for index, message in enumerate(messages):
                await send_with_flood_wait(client, target, message)
                if index < len(messages) - 1 and settings.command_delay_seconds > 0:
                    await asyncio.sleep(settings.command_delay_seconds)

            cycles += 1

            if end_at and datetime.now(ISTANBUL) > end_at:
                break
            if max_cycles and cycles >= max_cycles:
                break

            sleep_seconds = max(0.0, 60.0 - (loop.time() - cycle_started))
            if sleep_seconds:
                await asyncio.sleep(sleep_seconds)

        logger.info("[%s] Dakikalık akış tamamlandı. Toplam tur: %s", now_istanbul(), cycles)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
