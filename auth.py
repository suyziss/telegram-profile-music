
import asyncio
import getpass
from pathlib import Path

import qrcode
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    AuthTokenExpiredError,
)

SESSION_DIR = Path.home() / ".tg_profile_music"
SESSION_DIR.mkdir(parents=True, exist_ok=True)
SESSION = SESSION_DIR / "music_session"


async def main():
    api_id = int(input("API ID: ").strip())
    api_hash = getpass.getpass("API Hash: ").strip()

    client = TelegramClient(str(SESSION), api_id, api_hash)
    await client.connect()

    try:
        if not await client.is_user_authorized():
            while True:
                qr = await client.qr_login()

                print("\nTelegram → Настройки → Устройства")
                print("→ Подключить устройство\n")

                qr_code = qrcode.QRCode(border=2)
                qr_code.add_data(qr.url)
                qr_code.make(fit=True)
                qr_code.print_ascii(invert=True)

                try:
                    await qr.wait(timeout=60)
                    break
                except AuthTokenExpiredError:
                    print("QR-код истёк. Создаём новый...")
                except asyncio.TimeoutError:
                    print("Время истекло. Создаём новый QR...")
                except SessionPasswordNeededError:
                    password = getpass.getpass(
                        "Пароль двухэтапной защиты: "
                    )
                    await client.sign_in(password=password)
                    break

        me = await client.get_me()
        print(f"\nВход выполнен: {me.first_name}")
        print(f"Сессия сохранена: {SESSION}.session")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
