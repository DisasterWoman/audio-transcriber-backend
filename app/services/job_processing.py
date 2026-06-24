import logging

from app.core.errors import ConflictError
from app.schemas.job_status import JobStatus
from app.services.file_storage import get_stored_file_path, stored_file_exists
from app.services.job_service import (
    get_job_by_id,
    record_job_processing_attempt,
    retry_failed_job,
    update_job_status,
    update_job_transcript,
)
from app.services.transcription_service import transcribe_audio

logger = logging.getLogger("app.jobs")


class JobProcessingAlreadyFinished(ConflictError):
    def __init__(self, status: JobStatus):
        super().__init__(f"Cannot process job when status is {status.value}")


class StoredAudioFileMissing(FileNotFoundError):
    def __init__(self, filename: str):
        super().__init__(f"Stored audio file is missing: {filename}")


def start_job_processing(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        return None

    if job["status"] == JobStatus.processing:
        return job

    if job["status"] != JobStatus.queued:
        raise JobProcessingAlreadyFinished(job["status"])

    return update_job_status(job_id, JobStatus.processing)


def process_job(job_id: int) -> None:
    job = get_job_by_id(job_id)

    if job is None:
        logger.warning("job processing skipped job_id=%s reason=not_found", job_id)
        return

    try:
        if job["status"] == JobStatus.queued:
            job = update_job_status(job_id, JobStatus.processing)

        if job is None or job["status"] != JobStatus.processing:
            logger.info(
                "job processing skipped job_id=%s status=%s",
                job_id,
                None if job is None else job["status"].value,
            )
            return

        record_job_processing_attempt(job_id)

        if not stored_file_exists(job["filename"]):
            raise StoredAudioFileMissing(job["filename"])

        file_path = get_stored_file_path(job["filename"])
        transcript_text = transcribe_audio(file_path, job["language"])

        update_job_transcript(job_id, transcript_text)
        update_job_status(job_id, JobStatus.done)

        logger.info("job processing completed job_id=%s", job_id)
    except Exception as error:
        logger.exception("job processing failed job_id=%s", job_id)
        fail_job_if_possible(job_id, str(error))


def fail_job_if_possible(job_id: int, error_message: str) -> None:
    job = get_job_by_id(job_id)

    if job is None or job["status"] not in {JobStatus.queued, JobStatus.processing}:
        return

    update_job_status(job_id, JobStatus.failed, error_message)


def retry_job_processing(job_id: int):
    job = retry_failed_job(job_id)

    if job is None:
        return None

    return start_job_processing(job_id)
