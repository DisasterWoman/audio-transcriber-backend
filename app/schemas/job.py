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


class Job(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    language: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
