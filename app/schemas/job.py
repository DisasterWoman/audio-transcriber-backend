from datetime import datetime

from pydantic import ConfigDict, Field, model_validator

from app.schemas.base import AppBaseModel
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.pagination import PaginationMeta
from app.schemas.sorting import JobSortField, SortDirection


class JobCreate(AppBaseModel):
    filename: str
    original_filename: str
    file_size_bytes: int = Field(ge=0)
    content_type: str
    language: LanguageCode


class JobCreateRequest(AppBaseModel):
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


class JobTranscript(AppBaseModel):
    job_id: int
    transcript_text: str
    character_count: int = Field(ge=0)
    word_count: int = Field(ge=0)


class JobTranscriptMetadata(AppBaseModel):
    job_id: int
    character_count: int = Field(ge=0)
    word_count: int = Field(ge=0)


class JobTranscriptTopWord(AppBaseModel):
    word: str
    count: int = Field(ge=1)


class JobTranscriptAnalysis(AppBaseModel):
    job_id: int
    character_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    paragraph_count: int = Field(ge=0)
    estimated_reading_time_seconds: int = Field(ge=0)
    unique_word_count: int = Field(ge=0)
    top_words: list[JobTranscriptTopWord]


class JobTranscriptSearchMatch(AppBaseModel):
    start_index: int = Field(ge=0)
    end_index: int = Field(ge=0)
    snippet: str


class JobTranscriptSearchResult(AppBaseModel):
    job_id: int
    query: str
    total_matches: int = Field(ge=0)
    returned_matches: int = Field(ge=0)
    matches: list[JobTranscriptSearchMatch]


class JobActionState(AppBaseModel):
    enabled: bool
    reason: str | None = None


class JobActions(AppBaseModel):
    job_id: int
    process: JobActionState
    retry: JobActionState
    download_transcript: JobActionState
    download_audio: JobActionState
    processing_attempts: int = Field(ge=0)
    max_processing_attempts: int = Field(ge=1)
    retry_attempts_remaining: int = Field(ge=0)


class JobStatusDetail(AppBaseModel):
    job_id: int
    status: JobStatus
    is_terminal: bool
    processing_attempts: int = Field(ge=0)
    max_processing_attempts: int = Field(ge=1)
    retry_attempts_remaining: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    processing_duration_seconds: int | None = Field(default=None, ge=0)
    total_duration_seconds: int | None = Field(default=None, ge=0)
    failure_summary: str | None
    has_transcript: bool


class JobListQuery(AppBaseModel):
    status: JobStatus | None = None
    language: LanguageCode | None = None
    search: str | None = Field(default=None, min_length=1, max_length=100)
    created_from: datetime | None = None
    created_to: datetime | None = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: JobSortField = JobSortField.created_at
    sort_direction: SortDirection = SortDirection.desc

    @model_validator(mode="after")
    def validate_created_range(self):
        if (
            self.created_from is not None
            and self.created_to is not None
            and self.created_from > self.created_to
        ):
            raise ValueError("created_from must be before or equal to created_to")

        return self


class Job(AppBaseModel):
    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    content_type: str
    language: LanguageCode
    status: JobStatus
    processing_attempts: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    is_terminal: bool
    processing_duration_seconds: int | None = Field(default=None, ge=0)
    total_duration_seconds: int | None = Field(default=None, ge=0)
    error_message: str | None
    failure_summary: str | None
    has_transcript: bool
    transcript_text: str | None
    transcript_preview: str | None


class JobListItem(AppBaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    filename: str
    original_filename: str
    file_size_bytes: int
    content_type: str
    language: LanguageCode
    status: JobStatus
    processing_attempts: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    is_terminal: bool
    processing_duration_seconds: int | None = Field(default=None, ge=0)
    total_duration_seconds: int | None = Field(default=None, ge=0)
    error_message: str | None
    failure_summary: str | None
    has_transcript: bool
    transcript_preview: str | None


class JobList(PaginationMeta):
    items: list[JobListItem]


class JobStats(AppBaseModel):
    total: int = Field(ge=0)
    queued: int = Field(ge=0)
    processing: int = Field(ge=0)
    done: int = Field(ge=0)
    failed: int = Field(ge=0)


class JobSummary(AppBaseModel):
    stats: JobStats
    recent_jobs: JobList
