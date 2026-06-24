from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app.core.errors import FileStorageError, FileTooLargeError
from app.services import file_storage


def make_upload_file(filename: str = "interview.mp3") -> UploadFile:
    return UploadFile(
        filename=filename,
        file=BytesIO(b"fake audio bytes"),
        headers={"content-type": "audio/mpeg"},
    )


class BrokenWriteBuffer:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def write(self, chunk: bytes) -> None:
        raise OSError("Disk is full")


class BrokenWritePath:
    def __init__(self, path: Path):
        self.path = path
        self.deleted = False

    def __truediv__(self, filename: str):
        return self

    def open(self, mode: str):
        return BrokenWriteBuffer()

    def unlink(self, missing_ok: bool = False) -> None:
        self.deleted = True


@pytest.mark.anyio
async def test_save_uploaded_file_removes_partial_file_on_app_error(monkeypatch):
    broken_path = BrokenWritePath(Path("uploads/stored.mp3"))

    monkeypatch.setattr(file_storage, "ensure_upload_dir", lambda: broken_path)
    monkeypatch.setattr(
        file_storage,
        "generate_stored_filename",
        lambda filename: "stored.mp3",
    )
    monkeypatch.setattr(
        file_storage,
        "validate_audio_file_size",
        lambda size: (_ for _ in ()).throw(FileTooLargeError("Too large")),
    )

    with pytest.raises(FileTooLargeError):
        await file_storage.save_uploaded_file(make_upload_file())

    assert broken_path.deleted is True


@pytest.mark.anyio
async def test_save_uploaded_file_wraps_os_error(monkeypatch):
    broken_path = BrokenWritePath(Path("uploads/stored.mp3"))

    monkeypatch.setattr(file_storage, "ensure_upload_dir", lambda: broken_path)
    monkeypatch.setattr(
        file_storage,
        "generate_stored_filename",
        lambda filename: "stored.mp3",
    )

    with pytest.raises(FileStorageError) as error:
        await file_storage.save_uploaded_file(make_upload_file())

    assert str(error.value) == "Could not save uploaded file"
    assert broken_path.deleted is True
