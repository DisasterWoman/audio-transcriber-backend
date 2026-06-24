from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.base import AppBaseModel


class JobEventType(str, Enum):
    job_created = "job_created"
    status_changed = "status_changed"
    transcript_updated = "transcript_updated"
    processing_attempt_started = "processing_attempt_started"
    job_retried = "job_retried"


class JobEventCreate(AppBaseModel):
    job_id: int
    event_type: JobEventType
    message: str | None = Field(default=None, max_length=1000)


class JobEvent(AppBaseModel):
    id: int
    job_id: int
    event_type: JobEventType
    message: str | None
    created_at: datetime


class JobEventList(AppBaseModel):
    items: list[JobEvent]
    total: int = Field(ge=0)
