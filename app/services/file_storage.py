import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.errors import AppError
from app.core.settings import settings
from app.services.file_validation import validate_audio_file_size

CHUNK_SIZE_BYTES = 1024 * 1024


@dataclass(frozen=True)
class StoredFile:
    filename: str
    original_filename: str
    size_bytes: int
    content_type: str


async def save_uploaded_file(file: UploadFile) -> StoredFile:
    upload_dir = ensure_upload_dir()

    original_filename = file.filename or "uploaded_file"
    stored_filename = generate_stored_filename(original_filename)
    file_path = upload_dir / stored_filename

    bytes_written = 0

    try:
        with file_path.open("wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                bytes_written += len(chunk)
                validate_audio_file_size(bytes_written)
                buffer.write(chunk)
    except AppError:
        file_path.unlink(missing_ok=True)
        raise

    return StoredFile(
        filename=stored_filename,
        original_filename=original_filename,
        size_bytes=bytes_written,
        content_type=file.content_type or "application/octet-stream",
    )


def ensure_upload_dir() -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_stored_filename(original_filename: str) -> str:
    file_extension = Path(original_filename).suffix.lower()
    return f"{uuid4()}{file_extension}"


def get_stored_file_path(filename: str) -> Path:
    return Path(settings.upload_dir) / filename


def stored_file_exists(filename: str) -> bool:
    return get_stored_file_path(filename).is_file()


def is_upload_dir_ready() -> bool:
    upload_dir = Path(settings.upload_dir)
    return upload_dir.is_dir() and os.access(upload_dir, os.W_OK)
