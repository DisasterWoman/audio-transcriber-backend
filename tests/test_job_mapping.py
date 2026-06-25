from datetime import UTC, datetime, timedelta

from app.models.job import JobModel
from app.repositories.job_repository import (
    FAILURE_SUMMARY_LENGTH,
    TRANSCRIPT_PREVIEW_LENGTH,
    model_to_job,
)
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode


def test_model_to_job_adds_derived_timing_fields_for_completed_job():
    created_at = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)
    started_at = created_at + timedelta(seconds=5)
    completed_at = started_at + timedelta(seconds=30)

    job_model = JobModel(
        id=1,
        filename="stored.mp3",
        original_filename="interview.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        language=LanguageCode.en.value,
        status=JobStatus.done.value,
        processing_attempts=1,
        created_at=created_at,
        updated_at=completed_at,
        started_at=started_at,
        completed_at=completed_at,
        error_message=None,
        transcript_text="hello",
    )

    job = model_to_job(job_model)

    assert job["is_terminal"] is True
    assert job["processing_duration_seconds"] == 30
    assert job["total_duration_seconds"] == 35
    assert job["failure_summary"] is None
    assert job["transcript_preview"] == "hello"


def test_model_to_job_keeps_duration_fields_empty_for_queued_job():
    now = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)

    job_model = JobModel(
        id=1,
        filename="stored.mp3",
        original_filename="interview.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        language=LanguageCode.en.value,
        status=JobStatus.queued.value,
        processing_attempts=0,
        created_at=now,
        updated_at=now,
        started_at=None,
        completed_at=None,
        error_message=None,
        transcript_text=None,
    )

    job = model_to_job(job_model)

    assert job["is_terminal"] is False
    assert job["processing_duration_seconds"] is None
    assert job["total_duration_seconds"] is None
    assert job["failure_summary"] is None
    assert job["transcript_preview"] is None


def test_model_to_job_truncates_long_transcript_preview():
    now = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)
    transcript_text = f"{'word ' * 40}\n\nextra"

    job_model = JobModel(
        id=1,
        filename="stored.mp3",
        original_filename="interview.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        language=LanguageCode.en.value,
        status=JobStatus.done.value,
        processing_attempts=1,
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
        error_message=None,
        transcript_text=transcript_text,
    )

    job = model_to_job(job_model)

    assert job["transcript_preview"].endswith("...")
    assert "\n" not in job["transcript_preview"]
    assert len(job["transcript_preview"]) <= TRANSCRIPT_PREVIEW_LENGTH + 3


def test_model_to_job_adds_failure_summary_for_failed_job():
    now = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)

    job_model = JobModel(
        id=1,
        filename="stored.mp3",
        original_filename="interview.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        language=LanguageCode.en.value,
        status=JobStatus.failed.value,
        processing_attempts=1,
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
        error_message="Provider    timeout\nwhile transcribing audio",
        transcript_text=None,
    )

    job = model_to_job(job_model)

    assert job["failure_summary"] == "Provider timeout while transcribing audio"


def test_model_to_job_truncates_long_failure_summary():
    now = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)

    job_model = JobModel(
        id=1,
        filename="stored.mp3",
        original_filename="interview.mp3",
        file_size_bytes=123,
        content_type="audio/mpeg",
        language=LanguageCode.en.value,
        status=JobStatus.failed.value,
        processing_attempts=1,
        created_at=now,
        updated_at=now,
        started_at=now,
        completed_at=now,
        error_message="error " * 80,
        transcript_text=None,
    )

    job = model_to_job(job_model)

    assert job["failure_summary"].endswith("...")
    assert len(job["failure_summary"]) <= FAILURE_SUMMARY_LENGTH + 3
