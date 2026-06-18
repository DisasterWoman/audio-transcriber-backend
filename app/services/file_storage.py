from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.settings import settings
from app.services.file_validation import validate_audio_file_size


CHUNK_SIZE_BYTES = 1024 * 1024


async def save_uploaded_file(file: UploadFile) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename or "uploaded_file"
    file_extension = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4()}{file_extension}"
    file_path = upload_dir / stored_filename

    bytes_written = 0

    try:
        with file_path.open("wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE_BYTES):
                bytes_written += len(chunk)
                validate_audio_file_size(bytes_written)
                buffer.write(chunk)
    except HTTPException:
        file_path.unlink(missing_ok=True)
        raise

    return stored_filename
