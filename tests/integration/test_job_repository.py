from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.job import JobModel
from app.repositories import job_repository
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection

pytestmark = pytest.mark.integration


def cleanup_integration_jobs() -> None:
    with SessionLocal() as session:
        session.execute(
            delete(JobModel).where(
                JobModel.original_filename.like("integration-%")
            )
        )
        session.commit()


@pytest.fixture(autouse=True)
def clean_jobs():
    cleanup_integration_jobs()
    yield
    cleanup_integration_jobs()


def make_job(
    original_filename: str,
    status: JobStatus = JobStatus.queued,
    created_at: datetime | None = None,
) -> dict:
    now = created_at or datetime.now(UTC)

    return {
        "filename": f"stored-{original_filename}",
        "original_filename": original_filename,
        "file_size_bytes": 123,
        "content_type": "audio/mpeg",
        "language": LanguageCode.en,
        "status": status,
        "processing_attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "transcript_text": None,
    }


def test_repository_save_get_list_and_delete_job():
    saved_job = job_repository.save_job(make_job("integration-alpha.mp3"))

    found_job = job_repository.get_job(saved_job["id"])

    assert found_job is not None
    assert found_job["original_filename"] == "integration-alpha.mp3"

    listed_jobs = job_repository.list_jobs(
        language=LanguageCode.en,
        search="alpha",
        limit=10,
        offset=0,
        sort_by=JobSortField.created_at,
        sort_direction=SortDirection.desc,
    )

    assert listed_jobs["total"] == 1
    assert listed_jobs["items"][0]["id"] == saved_job["id"]

    assert job_repository.delete_job(saved_job["id"]) is True
    assert job_repository.get_job(saved_job["id"]) is None


def test_repository_filters_by_status_and_created_range():
    now = datetime.now(UTC)
    old_job = job_repository.save_job(
        make_job(
            "integration-old.mp3",
            status=JobStatus.done,
            created_at=now - timedelta(days=10),
        )
    )
    recent_job = job_repository.save_job(
        make_job(
            "integration-recent.mp3",
            status=JobStatus.done,
            created_at=now,
        )
    )

    listed_jobs = job_repository.list_jobs(
        status=JobStatus.done,
        created_from=now - timedelta(days=1),
        created_to=now + timedelta(days=1),
        limit=10,
        offset=0,
    )

    listed_ids = {job["id"] for job in listed_jobs["items"]}

    assert recent_job["id"] in listed_ids
    assert old_job["id"] not in listed_ids


def test_repository_counts_jobs_by_status():
    job_repository.save_job(make_job("integration-queued.mp3", JobStatus.queued))
    job_repository.save_job(make_job("integration-done.mp3", JobStatus.done))
    job_repository.save_job(make_job("integration-failed.mp3", JobStatus.failed))

    counts = job_repository.get_job_status_counts()

    assert counts[JobStatus.queued] >= 1
    assert counts[JobStatus.done] >= 1
    assert counts[JobStatus.failed] >= 1
    assert counts[JobStatus.processing] >= 0
