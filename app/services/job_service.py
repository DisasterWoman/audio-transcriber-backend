from datetime import UTC, datetime

from app.repositories.job_repository import (
    get_job,
    get_next_job_id,
    list_jobs,
    save_job,
)
from app.schemas.job import JobCreate
from app.schemas.job_status import JobStatus


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
    }

    return save_job(new_job)


def update_job_status(job_id: int, status: JobStatus):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    job["status"] = status
    job["updated_at"] = datetime.now(UTC)

    return job
