from datetime import UTC, datetime

from app.core.errors import ConflictError
from app.core.settings import settings
from app.repositories.job_event_repository import list_job_events, save_job_event
from app.repositories.job_repository import (
    delete_job,
    get_job,
    get_job_status_counts,
    list_jobs,
    save_job,
    update_job,
)
from app.schemas.job import JobCreate
from app.schemas.job_event import JobEventCreate, JobEventType
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection
from app.services.file_storage import delete_stored_file, stored_file_exists
from app.services.transcript_service import (
    analyze_transcript,
    get_transcript_metadata,
    search_transcript,
)

ALLOWED_STATUS_TRANSITIONS = {
    JobStatus.queued: {JobStatus.processing, JobStatus.failed},
    JobStatus.processing: {JobStatus.done, JobStatus.failed},
    JobStatus.done: set(),
    JobStatus.failed: set(),
}

COMPLETED_STATUSES = {JobStatus.done, JobStatus.failed}


class InvalidJobStatusTransition(ConflictError):
    def __init__(self, current_status: JobStatus, new_status: JobStatus):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            "Cannot change job status from "
            f"{current_status.value} to {new_status.value}"
        )


class InvalidJobTranscriptUpdate(ConflictError):
    def __init__(self, status: JobStatus):
        self.status = status
        super().__init__(f"Cannot update transcript when job status is {status.value}")


class MissingJobTranscript(ConflictError):
    def __init__(self):
        super().__init__("Cannot mark job as done before transcript is saved")


class JobTranscriptNotReady(ConflictError):
    def __init__(self, status: JobStatus):
        self.status = status
        super().__init__(f"Transcript is not ready when job status is {status.value}")


class MaxProcessingAttemptsReached(ConflictError):
    def __init__(self, max_attempts: int):
        self.max_attempts = max_attempts
        super().__init__(
            f"Cannot retry job after {max_attempts} processing attempts"
        )


def get_all_jobs(
    status: JobStatus | None = None,
    language: LanguageCode | None = None,
    search: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: JobSortField = JobSortField.created_at,
    sort_direction: SortDirection = SortDirection.desc,
):
    return list_jobs(
        status=status,
        language=language,
        search=search,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


def get_job_by_id(job_id: int):
    return get_job(job_id)


def get_job_transcript(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.done or not job["transcript_text"]:
        raise JobTranscriptNotReady(job["status"])

    return {
        "job_id": job["id"],
        "transcript_text": job["transcript_text"],
        **get_transcript_metadata(job["transcript_text"]),
    }


def get_job_transcript_metadata(job_id: int):
    transcript = get_job_transcript(job_id)

    if transcript is None:
        return None

    return {
        "job_id": transcript["job_id"],
        "character_count": transcript["character_count"],
        "word_count": transcript["word_count"],
    }


def get_job_transcript_analysis(job_id: int):
    transcript = get_job_transcript(job_id)

    if transcript is None:
        return None

    return {
        "job_id": transcript["job_id"],
        **analyze_transcript(transcript["transcript_text"]),
    }


def search_job_transcript(job_id: int, query: str, limit: int = 10):
    transcript = get_job_transcript(job_id)

    if transcript is None:
        return None

    return {
        "job_id": transcript["job_id"],
        **search_transcript(
            transcript["transcript_text"],
            query,
            limit=limit,
        ),
    }


def get_job_stats() -> dict:
    counts = get_job_status_counts()

    return {
        "total": sum(counts.values()),
        "queued": counts[JobStatus.queued],
        "processing": counts[JobStatus.processing],
        "done": counts[JobStatus.done],
        "failed": counts[JobStatus.failed],
    }


def get_job_summary(recent_limit: int = 5) -> dict:
    return {
        "stats": get_job_stats(),
        "recent_jobs": get_all_jobs(
            limit=recent_limit,
            offset=0,
            sort_by=JobSortField.created_at,
            sort_direction=SortDirection.desc,
        ),
    }


def get_job_actions(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    attempts_remaining = get_retry_attempts_remaining(job)

    return {
        "job_id": job["id"],
        "process": build_action_state(
            job["status"] == JobStatus.queued,
            f"Cannot process job when status is {job['status'].value}",
        ),
        "retry": build_action_state(
            job["status"] == JobStatus.failed and attempts_remaining > 0,
            get_retry_disabled_reason(job, attempts_remaining),
        ),
        "download_transcript": build_action_state(
            job["status"] == JobStatus.done and bool(job["transcript_text"]),
            "Transcript is only available after the job is done",
        ),
        "download_audio": build_action_state(
            stored_file_exists(job["filename"]),
            "Stored audio file is missing",
        ),
        "processing_attempts": job["processing_attempts"],
        "max_processing_attempts": settings.max_processing_attempts,
        "retry_attempts_remaining": attempts_remaining,
    }


def get_job_status_detail(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    return {
        "job_id": job["id"],
        "status": job["status"],
        "is_terminal": job["is_terminal"],
        "processing_attempts": job["processing_attempts"],
        "max_processing_attempts": settings.max_processing_attempts,
        "retry_attempts_remaining": get_retry_attempts_remaining(job),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "processing_duration_seconds": job["processing_duration_seconds"],
        "total_duration_seconds": job["total_duration_seconds"],
        "failure_summary": job["failure_summary"],
        "has_transcript": job["has_transcript"],
    }


def get_events_for_job(
    job_id: int,
    event_type: JobEventType | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_direction: SortDirection = SortDirection.asc,
):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    return list_job_events(
        job_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
        sort_direction=sort_direction,
    )


def delete_job_by_id(job_id: int) -> bool:
    job = get_job_by_id(job_id)

    if job is None:
        return False

    deleted = delete_job(job_id)

    if deleted:
        delete_stored_file(job["filename"])

    return deleted


def create_job(job_data: JobCreate):
    now = datetime.now(UTC)

    new_job = {
        "filename": job_data.filename,
        "original_filename": job_data.original_filename,
        "file_size_bytes": job_data.file_size_bytes,
        "content_type": job_data.content_type,
        "language": job_data.language,
        "status": JobStatus.queued,
        "processing_attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "transcript_text": None,
    }

    saved_job = save_job(new_job)
    record_job_event(
        saved_job["id"],
        JobEventType.job_created,
        "Job was created and queued for transcription",
    )

    return saved_job


def update_job_status(
    job_id: int,
    status: JobStatus,
    error_message: str | None = None,
):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    current_status = job["status"]

    if status == current_status:
        return job

    allowed_next_statuses = ALLOWED_STATUS_TRANSITIONS[current_status]

    if status not in allowed_next_statuses:
        raise InvalidJobStatusTransition(current_status, status)

    if status == JobStatus.done and not job["transcript_text"]:
        raise MissingJobTranscript()

    now = datetime.now(UTC)

    job["status"] = status
    job["updated_at"] = now

    if status == JobStatus.processing:
        job["started_at"] = now

    if status in COMPLETED_STATUSES:
        job["completed_at"] = now

    if status == JobStatus.failed:
        job["error_message"] = error_message

    updated_job = update_job(job)

    if updated_job is not None:
        record_job_event(
            job_id,
            JobEventType.status_changed,
            f"Status changed from {current_status.value} to {status.value}",
        )

    return updated_job


def record_job_processing_attempt(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    job["processing_attempts"] += 1
    job["updated_at"] = datetime.now(UTC)

    updated_job = update_job(job)

    if updated_job is not None:
        record_job_event(
            job_id,
            JobEventType.processing_attempt_started,
            f"Processing attempt {updated_job['processing_attempts']} started",
        )

    return updated_job


def retry_failed_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.failed:
        raise InvalidJobStatusTransition(job["status"], JobStatus.queued)

    if get_retry_attempts_remaining(job) == 0:
        raise MaxProcessingAttemptsReached(settings.max_processing_attempts)

    now = datetime.now(UTC)

    job["status"] = JobStatus.queued
    job["updated_at"] = now
    job["started_at"] = None
    job["completed_at"] = None
    job["error_message"] = None
    job["transcript_text"] = None

    updated_job = update_job(job)

    if updated_job is not None:
        record_job_event(job_id, JobEventType.job_retried, "Job was queued for retry")

    return updated_job


def update_job_transcript(job_id: int, transcript_text: str):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.processing:
        raise InvalidJobTranscriptUpdate(job["status"])

    job["transcript_text"] = transcript_text
    job["updated_at"] = datetime.now(UTC)

    updated_job = update_job(job)

    if updated_job is not None:
        record_job_event(
            job_id,
            JobEventType.transcript_updated,
            "Transcript was saved",
        )

    return updated_job


def record_job_event(
    job_id: int,
    event_type: JobEventType,
    message: str | None = None,
):
    return save_job_event(
        JobEventCreate(
            job_id=job_id,
            event_type=event_type,
            message=message,
        )
    )


def get_retry_attempts_remaining(job: dict) -> int:
    return max(settings.max_processing_attempts - job["processing_attempts"], 0)


def get_retry_disabled_reason(job: dict, attempts_remaining: int) -> str:
    if job["status"] != JobStatus.failed:
        return f"Can only retry failed jobs, current status is {job['status'].value}"

    if attempts_remaining == 0:
        return "Maximum processing attempts reached"

    return ""


def build_action_state(enabled: bool, disabled_reason: str) -> dict:
    return {
        "enabled": enabled,
        "reason": None if enabled else disabled_reason,
    }

