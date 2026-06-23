from pathlib import Path

from app.core.errors import BadRequestError, FileTooLargeError
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
        raise BadRequestError("Unsupported file extension")


def validate_audio_content_type(content_type: str | None) -> None:
    if not content_type:
        raise BadRequestError("Missing file content type")

    normalized_content_type = content_type.lower()

    if normalized_content_type not in settings.allowed_audio_mime_type_set:
        raise BadRequestError("Unsupported file content type")


def validate_audio_file_size(file_size_bytes: int) -> None:
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file_size_bytes > max_size_bytes:
        raise FileTooLargeError(
            f"File is too large. Maximum size is {settings.max_upload_size_mb} MB"
        )
