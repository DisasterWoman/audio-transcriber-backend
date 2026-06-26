from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.base import AppBaseModel
from app.schemas.pagination import PaginationMeta
from app.schemas.sorting import SortDirection


class JobEventType(str, Enum):
    job_created = "job_created"
    status_changed = "status_changed"
    transcript_updated = "transcript_updated"
    processing_attempt_started = "processing_attempt_started"
    job_retried = "job_retried"
    job_canceled = "job_canceled"


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


class JobEventListQuery(AppBaseModel):
    event_type: JobEventType | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_direction: SortDirection = SortDirection.asc


class JobEventList(PaginationMeta):
    items: list[JobEvent]
