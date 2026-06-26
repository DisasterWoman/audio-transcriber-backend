from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models.job import JobEventModel, JobModel, TranscriptRevisionModel
from app.repositories import (
    job_event_repository,
    job_repository,
    transcript_revision_repository,
)
from app.schemas.audio_source import AudioSource
from app.schemas.job_event import JobEventCreate, JobEventType
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection

pytestmark = pytest.mark.integration


def cleanup_integration_jobs() -> None:
    with SessionLocal() as session:
        session.execute(
            delete(TranscriptRevisionModel).where(
                TranscriptRevisionModel.job_id.in_(
                    select(JobModel.id).where(
                        JobModel.original_filename.like("integration-%")
                    )
                )
            )
        )
        session.execute(
            delete(JobEventModel).where(
                JobEventModel.message.like("integration-%")
            )
        )
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
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> dict:
    now = created_at or datetime.now(UTC)

    return {
        "filename": f"stored-{original_filename}",
        "original_filename": original_filename,
        "file_size_bytes": 123,
        "content_type": "audio/mpeg",
        "audio_source": AudioSource.uploaded_file,
        "duration_seconds": None,
        "language": LanguageCode.en,
        "status": status,
        "processing_attempts": 0,
        "created_at": now,
        "updated_at": now,
        "started_at": started_at,
        "completed_at": completed_at,
        "error_message": None,
        "transcript_text": None,
    }


def test_repository_save_get_list_and_delete_job():
    job_data = make_job("integration-alpha.mp3")
    job_data["audio_source"] = AudioSource.in_app_recording
    job_data["duration_seconds"] = 42
    saved_job = job_repository.save_job(job_data)

    found_job = job_repository.get_job(saved_job["id"])

    assert found_job is not None
    assert found_job["original_filename"] == "integration-alpha.mp3"
    assert found_job["audio_source"] == AudioSource.in_app_recording
    assert found_job["duration_seconds"] == 42

    listed_jobs = job_repository.list_jobs(
        language=LanguageCode.en,
        audio_source=AudioSource.in_app_recording,
        search="alpha",
        limit=10,
        offset=0,
        sort_by=JobSortField.created_at,
        sort_direction=SortDirection.desc,
    )

    assert listed_jobs["total"] == 1
    assert listed_jobs["count"] == 1
    assert listed_jobs["has_next"] is False
    assert listed_jobs["has_previous"] is False
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
    job_repository.save_job(make_job("integration-canceled.mp3", JobStatus.canceled))

    counts = job_repository.get_job_status_counts()

    assert counts[JobStatus.queued] >= 1
    assert counts[JobStatus.done] >= 1
    assert counts[JobStatus.failed] >= 1
    assert counts[JobStatus.canceled] >= 1
    assert counts[JobStatus.processing] >= 0


def test_repository_returns_derived_job_timing_fields():
    created_at = datetime.now(UTC) - timedelta(seconds=45)
    started_at = created_at + timedelta(seconds=15)
    completed_at = started_at + timedelta(seconds=30)
    saved_job = job_repository.save_job(
        make_job(
            "integration-duration.mp3",
            status=JobStatus.done,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
        )
    )

    assert saved_job["is_terminal"] is True
    assert saved_job["processing_duration_seconds"] == 30
    assert saved_job["total_duration_seconds"] == 45


def test_repository_saves_lists_and_cascades_job_events():
    saved_job = job_repository.save_job(make_job("integration-events.mp3"))

    first_event = job_event_repository.save_job_event(
        JobEventCreate(
            job_id=saved_job["id"],
            event_type=JobEventType.job_created,
            message="integration-created",
        )
    )
    second_event = job_event_repository.save_job_event(
        JobEventCreate(
            job_id=saved_job["id"],
            event_type=JobEventType.status_changed,
            message="integration-status-changed",
        )
    )

    events = job_event_repository.list_job_events(saved_job["id"])

    assert events["total"] == 2
    assert events["count"] == 2
    assert events["limit"] == 50
    assert events["offset"] == 0
    assert events["has_next"] is False
    assert events["has_previous"] is False
    assert [event["id"] for event in events["items"]] == [
        first_event["id"],
        second_event["id"],
    ]
    assert events["items"][0]["event_type"] == JobEventType.job_created

    job_repository.delete_job(saved_job["id"])

    events_after_delete = job_event_repository.list_job_events(saved_job["id"])

    assert events_after_delete == {
        "items": [],
        "total": 0,
        "count": 0,
        "limit": 50,
        "offset": 0,
        "has_next": False,
        "has_previous": False,
        "next_offset": None,
        "previous_offset": None,
    }


def test_repository_filters_paginates_and_sorts_job_events():
    saved_job = job_repository.save_job(make_job("integration-event-filters.mp3"))

    job_event_repository.save_job_event(
        JobEventCreate(
            job_id=saved_job["id"],
            event_type=JobEventType.job_created,
            message="integration-created",
        )
    )
    first_status_event = job_event_repository.save_job_event(
        JobEventCreate(
            job_id=saved_job["id"],
            event_type=JobEventType.status_changed,
            message="integration-status-one",
        )
    )
    second_status_event = job_event_repository.save_job_event(
        JobEventCreate(
            job_id=saved_job["id"],
            event_type=JobEventType.status_changed,
            message="integration-status-two",
        )
    )

    events = job_event_repository.list_job_events(
        saved_job["id"],
        event_type=JobEventType.status_changed,
        limit=1,
        offset=0,
        sort_direction=SortDirection.desc,
    )

    assert events["total"] == 2
    assert events["count"] == 1
    assert events["limit"] == 1
    assert events["offset"] == 0
    assert events["has_next"] is True
    assert events["has_previous"] is False
    assert events["next_offset"] == 1
    assert events["previous_offset"] is None
    assert [event["id"] for event in events["items"]] == [second_status_event["id"]]
    assert first_status_event["id"] != second_status_event["id"]


def test_repository_saves_lists_gets_and_cascades_transcript_revisions():
    saved_job = job_repository.save_job(make_job("integration-revisions.mp3"))

    first_revision = transcript_revision_repository.save_transcript_revision(
        saved_job["id"],
        "integration first transcript",
    )
    second_revision = transcript_revision_repository.save_transcript_revision(
        saved_job["id"],
        "integration second transcript",
    )

    revisions = transcript_revision_repository.list_transcript_revisions(
        saved_job["id"],
        limit=10,
        offset=0,
        sort_direction=SortDirection.asc,
    )
    revision = transcript_revision_repository.get_transcript_revision(
        saved_job["id"],
        version=2,
    )

    assert first_revision["version"] == 1
    assert second_revision["version"] == 2
    assert revisions["total"] == 2
    assert [item["version"] for item in revisions["items"]] == [1, 2]
    assert revisions["items"][0]["transcript_preview"] == "integration first transcript"
    assert revision["transcript_text"] == "integration second transcript"

    job_repository.delete_job(saved_job["id"])

    revisions_after_delete = transcript_revision_repository.list_transcript_revisions(
        saved_job["id"]
    )

    assert revisions_after_delete["total"] == 0
