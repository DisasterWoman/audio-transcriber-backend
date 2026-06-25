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


def test_get_job_summary_returns_stats_and_recent_jobs(monkeypatch):
    calls = []

    monkeypatch.setattr(
        job_service,
        "get_job_stats",
        lambda: {
            "total": 1,
            "queued": 1,
            "processing": 0,
            "done": 0,
            "failed": 0,
        },
    )
    monkeypatch.setattr(
        job_service,
        "get_all_jobs",
        lambda **kwargs: calls.append(kwargs)
        or {
            "items": [],
            "total": 0,
            "count": 0,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
            "has_next": False,
            "has_previous": False,
            "next_offset": None,
            "previous_offset": None,
        },
    )

    summary = job_service.get_job_summary(recent_limit=3)

    assert summary["stats"]["total"] == 1
    assert summary["recent_jobs"]["limit"] == 3
    assert calls == [
        {
            "limit": 3,
            "offset": 0,
            "sort_by": job_service.JobSortField.created_at,
            "sort_direction": job_service.SortDirection.desc,
        }
    ]
