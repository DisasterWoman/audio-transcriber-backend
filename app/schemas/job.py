from datetime import datetime

from pydantic import BaseModel, Field
from app.schemas.job_status import JobStatus


class JobCreate(BaseModel):
    filename: str
    original_filename: str
    file_size_bytes: int = Field(ge=0)
    language: str


class JobStatusUpdate(BaseModel):
    status: JobStatus
    error_message: str | None = Field(default=None, max_length=1000)


class Job(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    language: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
