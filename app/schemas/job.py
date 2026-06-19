from datetime import datetime

from pydantic import Field, model_validator
from app.schemas.base import AppBaseModel
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection


class JobCreate(AppBaseModel):
    filename: str
    original_filename: str
    file_size_bytes: int = Field(ge=0)
    content_type: str
    language: LanguageCode


class JobStatusUpdate(AppBaseModel):
    status: JobStatus
    error_message: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validate_error_message(self):
        if self.status == JobStatus.failed and not self.error_message:
            raise ValueError("error_message is required when status is failed")

        if self.status != JobStatus.failed and self.error_message is not None:
            raise ValueError("error_message is only allowed when status is failed")

        return self


class JobTranscriptUpdate(AppBaseModel):
    transcript_text: str = Field(min_length=1)


class JobListQuery(AppBaseModel):
    status: JobStatus | None = None
    language: LanguageCode | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: JobSortField = JobSortField.created_at
    sort_direction: SortDirection = SortDirection.desc


class Job(AppBaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    content_type: str
    language: LanguageCode
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    transcript_text: str | None


class JobList(AppBaseModel):
    items: list[Job]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
