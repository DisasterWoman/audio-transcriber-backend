from pathlib import Path

from fastapi import HTTPException
from app.core.settings import settings


def is_allowed_audio_extension(filename: str | None) -> bool:
    if not filename:
        return False

    extension = Path(filename).suffix.lower().lstrip(".")

    if not extension:
        return False

    return extension in settings.allowed_audio_extension_set


def validate_audio_file(filename: str | None) -> None:
    if not is_allowed_audio_extension(filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file extension",
        )


def validate_audio_file_size(file_size_bytes: int) -> None:
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file_size_bytes > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File is too large. Maximum size is {settings.max_upload_size_mb} MB",
        )
