from app.schemas.job_status import JobStatus
from app.services import job_service


def test_get_job_stats_returns_total_and_status_counts(monkeypatch):
    monkeypatch.setattr(
        job_service,
        "get_job_status_counts",
        lambda: {
            JobStatus.queued: 2,
            JobStatus.processing: 1,
            JobStatus.done: 3,
            JobStatus.failed: 4,
        },
    )

    stats = job_service.get_job_stats()

    assert stats == {
        "total": 10,
        "queued": 2,
        "processing": 1,
        "done": 3,
        "failed": 4,
    }
