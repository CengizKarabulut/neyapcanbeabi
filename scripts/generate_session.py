from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("TELEGRAM_API_ID: ").strip())
api_hash = input("TELEGRAM_API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nTELEGRAM_SESSION:\n")
    print(client.session.save())
    print("\nBu değeri GitHub Secret olarak TELEGRAM_SESSION adıyla kaydet.\n")
