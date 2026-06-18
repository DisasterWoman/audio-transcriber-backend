from datetime import UTC, datetime

from app.repositories.job_repository import (
    get_job,
    get_next_job_id,
    list_jobs,
    save_job,
)
from app.schemas.job import JobCreate
from app.schemas.job_status import JobStatus


ALLOWED_STATUS_TRANSITIONS = {
    JobStatus.queued: {JobStatus.processing, JobStatus.failed},
    JobStatus.processing: {JobStatus.done, JobStatus.failed},
    JobStatus.done: set(),
    JobStatus.failed: set(),
}

COMPLETED_STATUSES = {JobStatus.done, JobStatus.failed}


class InvalidJobStatusTransition(Exception):
    def __init__(self, current_status: JobStatus, new_status: JobStatus):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Cannot change job status from {current_status.value} to {new_status.value}"
        )


class InvalidJobTranscriptUpdate(Exception):
    def __init__(self, status: JobStatus):
        self.status = status
        super().__init__(
            f"Cannot update transcript when job status is {status.value}"
        )


def get_all_jobs():
    return list_jobs()


def get_job_by_id(job_id: int):
    return get_job(job_id)


def create_job(job_data: JobCreate):
    now = datetime.now(UTC)

    new_job = {
        "id": get_next_job_id(),
        "filename": job_data.filename,
        "original_filename": job_data.original_filename,
        "file_size_bytes": job_data.file_size_bytes,
        "language": job_data.language,
        "status": JobStatus.queued,
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

    now = datetime.now(UTC)

    job["status"] = status
    job["updated_at"] = now

    if status == JobStatus.processing:
        job["started_at"] = now

    if status in COMPLETED_STATUSES:
        job["completed_at"] = now

    if status == JobStatus.failed:
        job["error_message"] = error_message

    return job


def update_job_transcript(job_id: int, transcript_text: str):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] != JobStatus.processing:
        raise InvalidJobTranscriptUpdate(job["status"])

    job["transcript_text"] = transcript_text
    job["updated_at"] = datetime.now(UTC)

    return job
