from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ISTANBUL = ZoneInfo("Europe/Istanbul")
CHAT_ID = "@aselsanhissee"
SYMBOL = "ASELS"
CATCHUP_SECONDS = 4 * 60
CHECK_INTERVAL_SECONDS = 5
HEARTBEAT_SECONDS = 5 * 60
MAX_RUNTIME_MINUTES = int(os.getenv("ASELS_LOOP_RUNTIME_MINUTES", "240"))


@dataclass(frozen=True)
class Slot:
    hhmm: str
    commands: str
    dedupe_minutes: int
    label: str


def daily_slots() -> list[Slot]:
    slots: list[Slot] = []

    for hhmm in ("09:40", "09:45", "09:50", "09:55", "09:58"):
        slots.append(Slot(hhmm, "teorik", 4, "preopen"))

    for hour in range(10, 18):
        for minute in (5, 20, 35, 50):
            slots.append(Slot(f"{hour:02d}:{minute:02d}", "akd,derinlik,kurum", 14, "intraday"))

    for hhmm in ("18:05", "18:15"):
        slots.append(Slot(hhmm, "akd,derinlik,kurum", 14, "intraday"))

    slots.append(Slot("19:30", "takas", 60, "eod"))
    return slots


def slot_datetime(now: datetime, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def run_sender(slot: Slot) -> bool:
    env = os.environ.copy()
    env.update(
        {
            "TELEGRAM_CHAT_ID": CHAT_ID,
            "SYMBOL": SYMBOL,
            "COMMANDS": slot.commands,
            "COMMAND_DELAY_SECONDS": "10",
            "DEDUPE_WINDOW_MINUTES": str(slot.dedupe_minutes),
        }
    )

    for attempt in range(1, 4):
        stamp = datetime.now(ISTANBUL).strftime("%F %T %Z")
        print(
            f"[{stamp}] SEND slot={slot.hhmm} label={slot.label} "
            f"commands={slot.commands} attempt={attempt}/3",
            flush=True,
        )
        result = subprocess.run([sys.executable, "-m", "src.main"], env=env, check=False)
        if result.returncode == 0:
            print(f"[{datetime.now(ISTANBUL):%F %T}] SEND OK slot={slot.hhmm}", flush=True)
            return True

        print(
            f"[{datetime.now(ISTANBUL):%F %T}] SEND FAILED slot={slot.hhmm} "
            f"returncode={result.returncode}",
            flush=True,
        )
        if attempt < 3:
            time.sleep(15)

    return False


def main() -> int:
    required = ("TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION")
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise RuntimeError(f"Eksik secret: {', '.join(missing)}")

    slots = daily_slots()
    sent_keys: set[str] = set()
    failed_retry_after: dict[str, datetime] = {}
    started = datetime.now(ISTANBUL)
    stop_at = started + timedelta(minutes=MAX_RUNTIME_MINUTES)
    next_heartbeat = started

    print(
        f"ASELS resilient scheduler started={started:%F %T %Z} "
        f"stop_at={stop_at:%F %T %Z} catchup={CATCHUP_SECONDS}s",
        flush=True,
    )

    while datetime.now(ISTANBUL) < stop_at:
        now = datetime.now(ISTANBUL)

        if now >= next_heartbeat:
            print(
                f"[{now:%F %T %Z}] HEARTBEAT weekday={now.isoweekday()} "
                f"sent_slots={len(sent_keys)}",
                flush=True,
            )
            next_heartbeat = now + timedelta(seconds=HEARTBEAT_SECONDS)

        if now.isoweekday() <= 5:
            for slot in slots:
                target = slot_datetime(now, slot.hhmm)
                age = (now - target).total_seconds()
                key = f"{target:%F}|{slot.hhmm}|{slot.commands}"

                if key in sent_keys:
                    continue
                if age < 0 or age > CATCHUP_SECONDS:
                    continue

                retry_at = failed_retry_after.get(key)
                if retry_at is not None and now < retry_at:
                    continue

                if run_sender(slot):
                    sent_keys.add(key)
                    failed_retry_after.pop(key, None)
                else:
                    failed_retry_after[key] = datetime.now(ISTANBUL) + timedelta(seconds=30)

        time.sleep(CHECK_INTERVAL_SECONDS)

    print(
        f"[{datetime.now(ISTANBUL):%F %T %Z}] Runtime block completed normally. "
        "Recovery workflow will start the successor.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
