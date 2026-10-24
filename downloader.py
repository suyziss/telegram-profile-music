
import asyncio
import getpass
import re
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import DocumentAttributeAudio

SESSION = Path.home() / ".tg_profile_music" / "music_session"
DOWNLOAD_DIR = Path.home() / "storage" / "shared" / "Music"

# В Termux storage/shared обычно указывает на общую память Android.
# Если каталог недоступен, используется папка Music внутри домашнего каталога.
if not (Path.home() / "storage" / "shared").exists():
    DOWNLOAD_DIR = Path.home() / "Music"

AUDIO_EXTENSIONS = {
    ".mp3", ".m4a", ".aac", ".flac",
    ".ogg", ".opus", ".wav", ".wma"
}


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "_", name)
    return name.strip(" .") or "audio"


def get_audio_name(message):
    doc = message.document
    if not doc:
        return None

    filename = None
    performer = None
    title = None

    for attr in doc.attributes:
        if isinstance(attr, DocumentAttributeAudio):
            performer = attr.performer
            title = attr.title
        if hasattr(attr, "file_name"):
            filename = attr.file_name

    if title:
        base = f"{performer or 'Unknown'} - {title}"
        ext = Path(filename).suffix if filename else ".m4a"
        if ext.lower() not in AUDIO_EXTENSIONS:
            ext = ".m4a"
        return safe_name(base) + ext

    if filename and Path(filename).suffix.lower() in AUDIO_EXTENSIONS:
        return safe_name(filename)

    mime = doc.mime_type or ""
    if mime.startswith("audio/"):
        return f"audio_{message.id}.m4a"

    return None


async def main():
    api_id = int(input("API ID: ").strip())
    api_hash = getpass.getpass("API Hash: ").strip()

    if not Path(str(SESSION) + ".session").exists():
        print("Сессия не найдена. Сначала запусти auth.py.")
        return

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(str(SESSION), api_id, api_hash)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            print("Сессия не авторизована. Запусти auth.py.")
            return

        profile = input("Профиль (@username или ID): ").strip()
        entity = await client.get_entity(profile)

        count = 0
        skipped = 0

        async for message in client.iter_messages(entity):
            if not message.document:
                continue

            filename = get_audio_name(message)
            if not filename:
                continue

            destination = DOWNLOAD_DIR / filename

            if destination.exists():
                skipped += 1
                continue

            print(f"Скачиваю: {filename}")

            try:
                result = await client.download_media(
                    message, file=str(destination)
                )
                if result:
                    count += 1
            except FloodWaitError as exc:
                print(f"Telegram ограничил запросы на {exc.seconds} сек.")
                await asyncio.sleep(exc.seconds + 1)
            except Exception as exc:
                print(f"Ошибка файла {filename}: {exc}")

        print(f"\nГотово. Скачано: {count}")
        print(f"Пропущено существующих: {skipped}")
        print(f"Папка: {DOWNLOAD_DIR}")

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

