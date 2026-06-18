from datetime import datetime

from pydantic import BaseModel, Field, model_validator
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode


class JobCreate(BaseModel):
    filename: str
    original_filename: str
    file_size_bytes: int = Field(ge=0)
    language: LanguageCode


class JobStatusUpdate(BaseModel):
    status: JobStatus
    error_message: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_error_message(self):
        if self.status == JobStatus.failed and not self.error_message:
            raise ValueError("error_message is required when status is failed")

        if self.status != JobStatus.failed and self.error_message is not None:
            raise ValueError("error_message is only allowed when status is failed")

        return self


class JobTranscriptUpdate(BaseModel):
    transcript_text: str = Field(min_length=1)


class Job(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    language: LanguageCode
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    transcript_text: str | None
