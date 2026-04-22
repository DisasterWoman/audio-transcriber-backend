from fastapi import HTTPException
from app.core.settings import settings


def is_allowed_audio_extension(filename: str) -> bool:
    if "." not in filename:
        return False

    extension = filename.split(".")[-1].lower()

    allowed_extensions = [
        ext.strip() for ext in settings.allowed_audio_extensions.split(",")
    ]

    return extension in allowed_extensions


def validate_audio_file(filename: str) -> None:
    if not is_allowed_audio_extension(filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file extension",
        )