from sqlalchemy import select

from app.db.session import SessionLocal, engine
from app.models.job import JobModel
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode


def init_job_repository() -> None:
    with engine.connect():
        pass


def list_jobs():
    with SessionLocal() as session:
        jobs = session.scalars(select(JobModel)).all()
        return [model_to_job(job) for job in jobs]


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


def job_to_model_values(job: dict) -> dict:
    return {
        "filename": job["filename"],
        "original_filename": job["original_filename"],
        "file_size_bytes": job["file_size_bytes"],
        "content_type": job["content_type"],
        "language": job["language"].value,
        "status": job["status"].value,
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "error_message": job["error_message"],
        "transcript_text": job["transcript_text"],
    }


def model_to_job(job: JobModel) -> dict:
    return {
        "id": job.id,
        "filename": job.filename,
        "original_filename": job.original_filename,
        "file_size_bytes": job.file_size_bytes,
        "content_type": job.content_type,
        "language": LanguageCode(job.language),
        "status": JobStatus(job.status),
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
        "error_message": job.error_message,
        "transcript_text": job.transcript_text,
    }
