from datetime import UTC, datetime

from app.schemas.job import JobCreate
from app.schemas.job_status import JobStatus

jobs = []


def get_all_jobs():
    return jobs


def get_job_by_id(job_id: int):
    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def create_job(job_data: JobCreate):
    now = datetime.now(UTC)

    new_job = {
        "id": len(jobs) + 1,
        "filename": job_data.filename,
        "original_filename": job_data.original_filename,
        "file_size_bytes": job_data.file_size_bytes,
        "language": job_data.language,
        "status": JobStatus.queued,
        "created_at": now,
        "updated_at": now,
    }
    jobs.append(new_job)
    return new_job


def update_job_status(job_id: int, status: JobStatus):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    job["status"] = status
    job["updated_at"] = datetime.now(UTC)

    return job
