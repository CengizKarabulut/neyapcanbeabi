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
CATCHUP_SECONDS = 6 * 60
CHECK_INTERVAL_SECONDS = 5
HEARTBEAT_SECONDS = 5 * 60
SENDER_TIMEOUT_SECONDS = int(os.getenv("ASELS_SENDER_TIMEOUT_SECONDS", "100"))
MAX_RUNTIME_MINUTES = int(os.getenv("ASELS_LOOP_RUNTIME_MINUTES", "240"))
HANDOFF_LEAD_SECONDS = int(os.getenv("ASELS_HANDOFF_LEAD_SECONDS", "60"))
WORKFLOW_FILE = "asels-live-loop.yml"


@dataclass(frozen=True)
class Slot:
    hhmm: str
    commands: str
    dedupe_minutes: int
    label: str


def daily_slots() -> list[Slot]:
    slots: list[Slot] = []

    for hhmm in ("09:40", "09:45", "09:50", "09:55", "09:58"):
        slots.append(Slot(hhmm, "teorik", 2, "preopen"))

    # Gun ici 90 dakikada bir; kapanis sonrasi 18:15 tek kontrol.
    first_intraday = datetime(2000, 1, 1, 10, 5)
    for offset_minutes in range(0, 8 * 60, 90):
        target = first_intraday + timedelta(minutes=offset_minutes)
        slots.append(Slot(target.strftime("%H:%M"), "akd,derinlik,kurum", 14, "intraday"))

    slots.append(Slot("17:55", "akd,derinlik,kurum", 14, "preclose"))
    slots.append(Slot("18:15", "akd,derinlik,kurum", 9, "closing"))

    slots.append(Slot("19:30", "takas", 60, "eod"))
    return slots


def slot_datetime(now: datetime, hhmm: str) -> datetime:
    hour, minute = map(int, hhmm.split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def run_one_command(command: str, slot: Slot) -> bool:
    env = os.environ.copy()
    env.update(
        {
            "TELEGRAM_CHAT_ID": CHAT_ID,
            "SYMBOL": SYMBOL,
            "COMMANDS": command,
            "COMMAND_DELAY_SECONDS": "0",
            "DEDUPE_WINDOW_MINUTES": str(slot.dedupe_minutes),
        }
    )

    for attempt in range(1, 4):
        stamp = datetime.now(ISTANBUL).strftime("%F %T %Z")
        print(
            f"[{stamp}] SEND slot={slot.hhmm} label={slot.label} "
            f"command={command} attempt={attempt}/3 timeout={SENDER_TIMEOUT_SECONDS}s",
            flush=True,
        )

        try:
            result = subprocess.run(
                [sys.executable, "-m", "src.main"],
                env=env,
                check=False,
                timeout=SENDER_TIMEOUT_SECONDS,
            )
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            returncode = 124
            print(
                f"[{datetime.now(ISTANBUL):%F %T}] SEND TIMEOUT slot={slot.hhmm} "
                f"command={command}; sender process was terminated.",
                flush=True,
            )

        if returncode == 0:
            print(
                f"[{datetime.now(ISTANBUL):%F %T}] SEND OK "
                f"slot={slot.hhmm} command={command}",
                flush=True,
            )
            return True

        print(
            f"[{datetime.now(ISTANBUL):%F %T}] SEND FAILED slot={slot.hhmm} "
            f"command={command} returncode={returncode}",
            flush=True,
        )
        if attempt < 3:
            time.sleep(10)

    return False


def run_sender(slot: Slot) -> bool:
    commands = [part.strip() for part in slot.commands.split(",") if part.strip()]

    for index, command in enumerate(commands):
        if not run_one_command(command, slot):
            return False
        if index < len(commands) - 1:
            time.sleep(10)

    return True


def dispatch_successor() -> bool:
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    token = os.getenv("GH_TOKEN", "").strip()
    if not repository or not token:
        print(
            "SELF-HANDOFF FAILED: GITHUB_REPOSITORY or GH_TOKEN is missing.",
            flush=True,
        )
        return False

    env = os.environ.copy()
    for attempt in range(1, 4):
        stamp = datetime.now(ISTANBUL).strftime("%F %T %Z")
        print(f"[{stamp}] SELF-HANDOFF attempt={attempt}/3", flush=True)
        try:
            result = subprocess.run(
                [
                    "gh",
                    "workflow",
                    "run",
                    WORKFLOW_FILE,
                    "--repo",
                    repository,
                    "--ref",
                    "main",
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            print(
                f"[{datetime.now(ISTANBUL):%F %T}] SELF-HANDOFF TIMEOUT",
                flush=True,
            )
            if attempt < 3:
                time.sleep(10)
            continue

        if result.returncode == 0:
            print(
                f"[{datetime.now(ISTANBUL):%F %T}] SELF-HANDOFF OK; successor queued.",
                flush=True,
            )
            return True

        detail = (result.stderr or result.stdout or "").strip()
        print(
            f"[{datetime.now(ISTANBUL):%F %T}] SELF-HANDOFF FAILED "
            f"returncode={result.returncode} detail={detail}",
            flush=True,
        )
        if attempt < 3:
            time.sleep(10)

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
    handoff_at = stop_at - timedelta(seconds=HANDOFF_LEAD_SECONDS)
    next_heartbeat = started
    next_handoff_retry = handoff_at
    handoff_done = False

    print(
        f"ASELS resilient scheduler started={started:%F %T %Z} "
        f"stop_at={stop_at:%F %T %Z} handoff_at={handoff_at:%F %T %Z} "
        f"catchup={CATCHUP_SECONDS}s sender_timeout={SENDER_TIMEOUT_SECONDS}s",
        flush=True,
    )

    while datetime.now(ISTANBUL) < stop_at:
        now = datetime.now(ISTANBUL)

        if now >= next_heartbeat:
            print(
                f"[{now:%F %T %Z}] HEARTBEAT weekday={now.isoweekday()} "
                f"sent_slots={len(sent_keys)} handoff_done={handoff_done}",
                flush=True,
            )
            next_heartbeat = now + timedelta(seconds=HEARTBEAT_SECONDS)

        if not handoff_done and now >= next_handoff_retry:
            if dispatch_successor():
                handoff_done = True
            else:
                next_handoff_retry = datetime.now(ISTANBUL) + timedelta(seconds=30)

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

    if not handoff_done:
        print(
            f"[{datetime.now(ISTANBUL):%F %T %Z}] Final self-handoff attempt before exit.",
            flush=True,
        )
        handoff_done = dispatch_successor()

    if not handoff_done:
        print(
            f"[{datetime.now(ISTANBUL):%F %T %Z}] ERROR: successor could not be queued. "
            "Recovery schedule must repair the chain.",
            flush=True,
        )
        return 2

    print(
        f"[{datetime.now(ISTANBUL):%F %T %Z}] Runtime block completed; "
        "successor already queued.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
