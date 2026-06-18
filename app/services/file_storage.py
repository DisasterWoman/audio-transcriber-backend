from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.settings import settings


async def save_uploaded_file(file: UploadFile) -> str:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename or "uploaded_file"
    file_extension = Path(original_filename).suffix.lower()
    stored_filename = f"{uuid4()}{file_extension}"
    file_path = upload_dir / stored_filename

    content = await file.read()
    file_path.write_bytes(content)

    return stored_filename
