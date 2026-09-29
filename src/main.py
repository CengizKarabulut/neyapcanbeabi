from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.errors import ChatIdInvalidError
from telethon.sessions import StringSession

from src.config import Settings

ISTANBUL = ZoneInfo("Europe/Istanbul")
CONNECT_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_CONNECT_TIMEOUT_SECONDS", "20"))
REQUEST_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_REQUEST_TIMEOUT_SECONDS", "20"))
DEDUP_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_DEDUP_TIMEOUT_SECONDS", "20"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("telegram-market-commands")


def now_istanbul() -> str:
    return datetime.now(ISTANBUL).strftime("%Y-%m-%d %H:%M:%S %Z")


def build_message(command: str, symbol: str) -> str:
    command = command.strip().lstrip("/")
    if command.lower() == "kurum":
        return f"/{command}"
    return f"/{command} {symbol}"


def web_k_to_telethon_id(chat_id: int) -> int | None:
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


async def _recently_sent_impl(client: TelegramClient, target, text: str, minutes: int) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    async for msg in client.iter_messages(target, limit=100):
        if msg.date and msg.date < cutoff:
            break
        if msg.out and (msg.raw_text or "").strip() == text.strip():
            return True
    return False


async def recently_sent(client: TelegramClient, target, text: str, minutes: int) -> bool:
    if minutes <= 0:
        return False
    return await asyncio.wait_for(
        _recently_sent_impl(client, target, text, minutes),
        timeout=DEDUP_TIMEOUT_SECONDS,
    )


async def main() -> None:
    settings = Settings.from_env()
    if settings.api_id is None or not settings.api_hash or not settings.session:
        raise RuntimeError(
            "TELEGRAM_API_ID, TELEGRAM_API_HASH ve TELEGRAM_SESSION zorunludur."
        )

    messages = [build_message(command, settings.symbol) for command in settings.commands]
    dedupe_minutes = int(os.getenv("DEDUPE_WINDOW_MINUTES", "0") or "0")

    client = TelegramClient(
        StringSession(settings.session),
        settings.api_id,
        settings.api_hash,
        timeout=10,
        request_retries=2,
        connection_retries=2,
        retry_delay=1,
        auto_reconnect=False,
    )

    try:
        logger.info("[%s] Telegram kullanıcı oturumu bağlanıyor.", now_istanbul())
        await asyncio.wait_for(client.connect(), timeout=CONNECT_TIMEOUT_SECONDS)

        authorized = await asyncio.wait_for(
            client.is_user_authorized(),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if not authorized:
            raise RuntimeError("TELEGRAM_SESSION geçerli değil veya yetkilendirilmemiş.")

        me = await asyncio.wait_for(client.get_me(), timeout=REQUEST_TIMEOUT_SECONDS)
        logger.info(
            "[%s] Kullanıcı oturumu hazır: id=%s username=@%s",
            now_istanbul(),
            getattr(me, "id", "?"),
            getattr(me, "username", "") or "-",
        )

        target = await asyncio.wait_for(
            resolve_target(client, settings.chat_target),
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        logger.info(
            "[%s] Hedef hazır: %s (Telegram entity id=%s)",
            now_istanbul(),
            getattr(target, "title", settings.chat_target),
            getattr(target, "id", "?"),
        )

        for index, message in enumerate(messages):
            try:
                duplicate = await recently_sent(client, target, message, dedupe_minutes)
            except asyncio.TimeoutError:
                logger.warning(
                    "[%s] Dedupe kontrolü zaman aşımına uğradı; gönderime devam ediliyor: %s",
                    now_istanbul(),
                    message,
                )
                duplicate = False

            if duplicate:
                logger.info(
                    "[%s] Tekrar engellendi (%s dk pencere): %s",
                    now_istanbul(),
                    dedupe_minutes,
                    message,
                )
                continue

            await asyncio.wait_for(
                client.send_message(target, message),
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            logger.info("[%s] Gönderildi: %s", now_istanbul(), message)

            if index < len(messages) - 1 and settings.command_delay_seconds > 0:
                await asyncio.sleep(settings.command_delay_seconds)
    finally:
        if client.is_connected():
            try:
                await asyncio.wait_for(client.disconnect(), timeout=5)
            except Exception:
                logger.warning("Telegram bağlantısı kapatılırken hata/zaman aşımı oluştu.")


if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=90))
    except asyncio.TimeoutError as exc:
        raise SystemExit("Telegram gönderim işlemi 90 saniyede tamamlanamadı.") from exc
