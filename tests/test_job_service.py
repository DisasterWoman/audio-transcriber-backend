from datetime import UTC, datetime

import pytest

from app.schemas.job import JobCreate
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.services import job_service


def make_job(status: JobStatus = JobStatus.queued) -> dict:
    now = datetime.now(UTC)

    return {
        "id": 1,
        "filename": "stored.mp3",
        "original_filename": "interview.mp3",
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


def test_create_job_starts_queued(monkeypatch):
    saved_jobs = []

    def fake_save_job(job: dict):
        saved_jobs.append(job)
        return {**job, "id": 1}

    monkeypatch.setattr(job_service, "save_job", fake_save_job)

    job = job_service.create_job(
        JobCreate(
            filename="stored.mp3",
            original_filename="interview.mp3",
            file_size_bytes=123,
            content_type="audio/mpeg",
            language=LanguageCode.en,
        )
    )

    assert job["status"] == JobStatus.queued
    assert job["processing_attempts"] == 0
    assert job["started_at"] is None
    assert job["completed_at"] is None
    assert saved_jobs[0]["filename"] == "stored.mp3"


def test_update_job_status_records_processing_time(monkeypatch):
    stored_job = make_job(JobStatus.queued)

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_service, "update_job", lambda job: job)

    job = job_service.update_job_status(1, JobStatus.processing)

    assert job["status"] == JobStatus.processing
    assert job["started_at"] is not None
    assert job["completed_at"] is None


def test_update_job_status_rejects_invalid_transition(monkeypatch):
    stored_job = make_job(JobStatus.queued)

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)

    with pytest.raises(job_service.InvalidJobStatusTransition):
        job_service.update_job_status(1, JobStatus.done)


def test_done_requires_transcript(monkeypatch):
    stored_job = make_job(JobStatus.processing)

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)

    with pytest.raises(job_service.MissingJobTranscript):
        job_service.update_job_status(1, JobStatus.done)


def test_retry_failed_job_resets_job_for_processing(monkeypatch):
    stored_job = make_job(JobStatus.failed)
    stored_job["processing_attempts"] = 1
    stored_job["started_at"] = datetime.now(UTC)
    stored_job["completed_at"] = datetime.now(UTC)
    stored_job["error_message"] = "Provider failed"
    stored_job["transcript_text"] = "old transcript"

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_service, "update_job", lambda job: job)

    job = job_service.retry_failed_job(1)

    assert job["status"] == JobStatus.queued
    assert job["processing_attempts"] == 1
    assert job["started_at"] is None
    assert job["completed_at"] is None
    assert job["error_message"] is None
    assert job["transcript_text"] is None


def test_retry_failed_job_rejects_non_failed_job(monkeypatch):
    stored_job = make_job(JobStatus.done)

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)

    with pytest.raises(job_service.InvalidJobStatusTransition):
        job_service.retry_failed_job(1)
