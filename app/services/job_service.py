from datetime import UTC, datetime

from app.core.errors import ConflictError
from app.repositories.job_repository import (
    delete_job,
    get_job,
    get_job_status_counts,
    list_jobs,
    save_job,
    update_job,
)
from app.schemas.job import JobCreate
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection
from app.services.file_storage import delete_stored_file

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


def get_all_jobs(
    status: JobStatus | None = None,
    language: LanguageCode | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: JobSortField = JobSortField.created_at,
    sort_direction: SortDirection = SortDirection.desc,
):
    return list_jobs(
        status=status,
        language=language,
        search=search,
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

    return save_job(new_job)


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

    return update_job(job)


def record_job_processing_attempt(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    job["processing_attempts"] += 1
    job["updated_at"] = datetime.now(UTC)

    return update_job(job)


def retry_failed_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.failed:
        raise InvalidJobStatusTransition(job["status"], JobStatus.queued)

    now = datetime.now(UTC)

    job["status"] = JobStatus.queued
    job["updated_at"] = now
    job["started_at"] = None
    job["completed_at"] = None
    job["error_message"] = None
    job["transcript_text"] = None

    return update_job(job)


def update_job_transcript(job_id: int, transcript_text: str):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.processing:
        raise InvalidJobTranscriptUpdate(job["status"])

    job["transcript_text"] = transcript_text
    job["updated_at"] = datetime.now(UTC)

    return update_job(job)
