from dataclasses import dataclass

from aiogram.types import Message


@dataclass
class FileData:
    telegram_file_id: str
    file_type: str
    file_name: str | None = None


def extract_file(message: Message) -> FileData | None:
    if message.document:
        return FileData(
            telegram_file_id=message.document.file_id,
            file_type="document",
            file_name=message.document.file_name,
        )

    if message.photo:
        photo = message.photo[-1]

        return FileData(
            telegram_file_id=photo.file_id,
            file_type="photo",
        )

    if message.video:
        return FileData(
            telegram_file_id=message.video.file_id,
            file_type="video",
            file_name=message.video.file_name,
        )

    if message.audio:
        return FileData(
            telegram_file_id=message.audio.file_id,
            file_type="audio",
            file_name=message.audio.file_name,
        )

    if message.voice:
        return FileData(
            telegram_file_id=message.voice.file_id,
            file_type="voice",
        )

    if message.animation:
        return FileData(
            telegram_file_id=message.animation.file_id,
            file_type="animation",
            file_name=message.animation.file_name,
        )

    return None