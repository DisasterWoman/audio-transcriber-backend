from datetime import UTC, datetime

from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode


def make_job(status: JobStatus = JobStatus.queued) -> dict:
    now = datetime.now(UTC)
    is_terminal = status in {JobStatus.done, JobStatus.failed}

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
        "is_terminal": is_terminal,
        "processing_duration_seconds": None,
        "total_duration_seconds": None,
        "error_message": None,
        "transcript_text": None,
    }
