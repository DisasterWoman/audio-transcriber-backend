from app.schemas.job_status import JobStatus
from app.services import job_processing
from tests.factories import make_job


def test_process_job_fails_when_stored_file_is_missing(monkeypatch):
    stored_job = make_job(JobStatus.processing)
    updates = []

    monkeypatch.setattr(job_processing, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_processing, "stored_file_exists", lambda filename: False)
    monkeypatch.setattr(
        job_processing,
        "record_job_processing_attempt",
        lambda job_id: None,
    )
    monkeypatch.setattr(
        job_processing,
        "update_job_status",
        lambda job_id, status, error_message=None: updates.append(
            {
                "job_id": job_id,
                "status": status,
                "error_message": error_message,
            }
        ),
    )

    job_processing.process_job(1)

    assert updates == [
        {
            "job_id": 1,
            "status": JobStatus.failed,
            "error_message": "Stored audio file is missing: stored.mp3",
        }
    ]
