from pydantic import Field

from app.schemas.base import AppBaseModel


class UploadConstraints(AppBaseModel):
    max_upload_size_mb: int = Field(ge=1)
    max_upload_size_bytes: int = Field(ge=1)
    allowed_audio_extensions: list[str]
    allowed_audio_mime_types: list[str]
