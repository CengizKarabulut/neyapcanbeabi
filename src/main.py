from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from src.config import Settings

ISTANBUL = ZoneInfo("Europe/Istanbul")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_REQUEST_TIMEOUT_SECONDS", "20"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("telegram-market-commands")


def now_istanbul() -> str:
    return datetime.now(ISTANBUL).strftime("%Y-%m-%d %H:%M:%S %Z")


def telegram_api(token: str, method: str, payload: dict[str, str]) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    body = urlencode(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw).get("description", raw)
        except json.JSONDecodeError:
            detail = raw
        raise RuntimeError(f"Telegram Bot API HTTP {exc.code}: {detail}") from None
    except URLError as exc:
        raise RuntimeError(f"Telegram Bot API bağlantı hatası: {exc.reason}") from None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Telegram Bot API geçersiz JSON yanıtı döndürdü.") from exc

    if not data.get("ok"):
        raise RuntimeError(
            f"Telegram Bot API hatası: {data.get('description', 'bilinmeyen hata')}"
        )

    result = data.get("result")
    if not isinstance(result, dict):
        raise RuntimeError("Telegram Bot API beklenmeyen sonuç döndürdü.")
    return result


def main() -> None:
    settings = Settings.from_env()
    messages = [f"/{command} {settings.symbol}" for command in settings.commands]

    me = telegram_api(settings.bot_token, "getMe", {})
    bot_username = me.get("username", "?")
    logger.info("[%s] Bot hazır: @%s", now_istanbul(), bot_username)

    chat = telegram_api(
        settings.bot_token,
        "getChat",
        {"chat_id": settings.chat_target},
    )
    chat_title = chat.get("title") or chat.get("username") or settings.chat_target
    logger.info(
        "[%s] Hedef hazır: %s (chat_id=%s)",
        now_istanbul(),
        chat_title,
        chat.get("id", "?"),
    )

    for index, message in enumerate(messages):
        result = telegram_api(
            settings.bot_token,
            "sendMessage",
            {
                "chat_id": settings.chat_target,
                "text": message,
            },
        )
        logger.info(
            "[%s] Gönderildi: %s (message_id=%s)",
            now_istanbul(),
            message,
            result.get("message_id", "?"),
        )

        if index < len(messages) - 1 and settings.command_delay_seconds > 0:
            time.sleep(settings.command_delay_seconds)


if __name__ == "__main__":
    main()
