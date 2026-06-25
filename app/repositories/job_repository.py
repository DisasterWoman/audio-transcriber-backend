from datetime import datetime

from sqlalchemy import func, select, text

from app.db.session import SessionLocal, engine
from app.models.job import JobModel
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection

TERMINAL_STATUSES = {JobStatus.done, JobStatus.failed}

JOB_SORT_COLUMNS = {
    JobSortField.created_at: JobModel.created_at,
    JobSortField.updated_at: JobModel.updated_at,
    JobSortField.file_size_bytes: JobModel.file_size_bytes,
}


def init_job_repository() -> None:
    with engine.connect():
        pass


def is_database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return False

    return True


def list_jobs(
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
    filters = []

    if status is not None:
        filters.append(JobModel.status == status.value)

    if language is not None:
        filters.append(JobModel.language == language.value)

    if search is not None:
        filters.append(JobModel.original_filename.ilike(f"%{search}%"))

    if created_from is not None:
        filters.append(JobModel.created_at >= created_from)

    if created_to is not None:
        filters.append(JobModel.created_at <= created_to)

    sort_column = JOB_SORT_COLUMNS[sort_by]

    if sort_direction == SortDirection.desc:
        sort_column = sort_column.desc()

    total_statement = select(func.count()).select_from(JobModel).where(*filters)
    jobs_statement = (
        select(JobModel)
        .where(*filters)
        .order_by(sort_column)
        .limit(limit)
        .offset(offset)
    )

    with SessionLocal() as session:
        total = session.scalar(total_statement) or 0
        jobs = session.scalars(jobs_statement).all()

    return {
        "items": [model_to_job(job) for job in jobs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_job_status_counts() -> dict[JobStatus, int]:
    statement = select(JobModel.status, func.count()).group_by(JobModel.status)

    with SessionLocal() as session:
        rows = session.execute(statement).all()

    counts = {status: 0 for status in JobStatus}

    for status, count in rows:
        counts[JobStatus(status)] = count

    return counts


def get_job(job_id: int):
    with SessionLocal() as session:
        job = session.get(JobModel, job_id)

        if job is None:
            return None

        return model_to_job(job)


def save_job(job: dict):
    with SessionLocal() as session:
        job_model = JobModel(**job_to_model_values(job))
        session.add(job_model)
        session.commit()
        session.refresh(job_model)
        return model_to_job(job_model)


def update_job(job: dict):
    with SessionLocal() as session:
        job_model = session.get(JobModel, job["id"])

        if job_model is None:
            return None

        for field, value in job_to_model_values(job).items():
            setattr(job_model, field, value)

        session.commit()
        session.refresh(job_model)
        return model_to_job(job_model)


def delete_job(job_id: int) -> bool:
    with SessionLocal() as session:
        job_model = session.get(JobModel, job_id)

        if job_model is None:
            return False

        session.delete(job_model)
        session.commit()

    return True


def job_to_model_values(job: dict) -> dict:
    return {
        "filename": job["filename"],
        "original_filename": job["original_filename"],
        "file_size_bytes": job["file_size_bytes"],
        "content_type": job["content_type"],
        "language": job["language"].value,
        "status": job["status"].value,
        "processing_attempts": job["processing_attempts"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "error_message": job["error_message"],
        "transcript_text": job["transcript_text"],
    }


def model_to_job(job: JobModel) -> dict:
    status = JobStatus(job.status)

    return {
        "id": job.id,
        "filename": job.filename,
        "original_filename": job.original_filename,
        "file_size_bytes": job.file_size_bytes,
        "content_type": job.content_type,
        "language": LanguageCode(job.language),
        "status": status,
        "processing_attempts": job.processing_attempts,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "is_terminal": status in TERMINAL_STATUSES,
        "processing_duration_seconds": calculate_duration_seconds(
            job.started_at,
            job.completed_at,
        ),
        "total_duration_seconds": calculate_duration_seconds(
            job.created_at,
            job.completed_at,
        ),
        "error_message": job.error_message,
        "transcript_text": job.transcript_text,
    }


def calculate_duration_seconds(
    started_at: datetime | None,
    completed_at: datetime | None,
) -> int | None:
    if started_at is None or completed_at is None:
        return None

    return max(int((completed_at - started_at).total_seconds()), 0)
