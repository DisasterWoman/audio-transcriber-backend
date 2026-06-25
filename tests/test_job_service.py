from datetime import UTC, datetime

import pytest

from app.schemas.job import JobCreate
from app.schemas.job_event import JobEventType
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.services import job_service
from tests.factories import make_job


def test_create_job_starts_queued(monkeypatch):
    saved_jobs = []
    saved_events = []

    def fake_save_job(job: dict):
        saved_jobs.append(job)
        return {**job, "id": 1}

    monkeypatch.setattr(job_service, "save_job", fake_save_job)
    monkeypatch.setattr(
        job_service,
        "record_job_event",
        lambda job_id, event_type, message=None: saved_events.append(
            {
                "job_id": job_id,
                "event_type": event_type,
                "message": message,
            }
        ),
    )

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
    assert saved_events == [
        {
            "job_id": 1,
            "event_type": JobEventType.job_created,
            "message": "Job was created and queued for transcription",
        }
    ]


def test_update_job_status_records_processing_time(monkeypatch):
    stored_job = make_job(JobStatus.queued)
    saved_events = []

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_service, "update_job", lambda job: job)
    monkeypatch.setattr(
        job_service,
        "record_job_event",
        lambda job_id, event_type, message=None: saved_events.append(
            (job_id, event_type, message)
        ),
    )

    job = job_service.update_job_status(1, JobStatus.processing)

    assert job["status"] == JobStatus.processing
    assert job["started_at"] is not None
    assert job["completed_at"] is None
    assert saved_events == [
        (
            1,
            JobEventType.status_changed,
            "Status changed from queued to processing",
        )
    ]


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
    monkeypatch.setattr(job_service, "record_job_event", lambda *args: None)

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


def test_update_job_transcript_records_event(monkeypatch):
    stored_job = make_job(JobStatus.processing)
    saved_events = []

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_service, "update_job", lambda job: job)
    monkeypatch.setattr(
        job_service,
        "record_job_event",
        lambda job_id, event_type, message=None: saved_events.append(
            (job_id, event_type, message)
        ),
    )

    job = job_service.update_job_transcript(1, "Hello transcript")

    assert job["transcript_text"] == "Hello transcript"
    assert saved_events == [
        (1, JobEventType.transcript_updated, "Transcript was saved")
    ]


def test_get_events_for_job_returns_none_when_job_does_not_exist(monkeypatch):
    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: None)

    events = job_service.get_events_for_job(1)

    assert events is None


def test_get_events_for_job_returns_job_events(monkeypatch):
    stored_job = make_job(JobStatus.queued)
    calls = []

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(
        job_service,
        "list_job_events",
        lambda job_id, **kwargs: calls.append({"job_id": job_id, **kwargs})
        or {"items": [], "total": 0, "limit": kwargs["limit"], "offset": 5},
    )

    events = job_service.get_events_for_job(
        1,
        event_type=JobEventType.status_changed,
        limit=10,
        offset=5,
    )

    assert events == {"items": [], "total": 0, "limit": 10, "offset": 5}
    assert calls == [
        {
            "job_id": 1,
            "event_type": JobEventType.status_changed,
            "limit": 10,
            "offset": 5,
            "sort_direction": job_service.SortDirection.asc,
        }
    ]
