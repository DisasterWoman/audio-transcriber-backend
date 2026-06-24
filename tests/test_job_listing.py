from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.schemas.sorting import JobSortField, SortDirection
from app.services import job_service


def test_get_all_jobs_passes_search_to_repository(monkeypatch):
    calls = []

    def fake_list_jobs(**kwargs):
        calls.append(kwargs)
        return {
            "items": [],
            "total": 0,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
        }

    monkeypatch.setattr(job_service, "list_jobs", fake_list_jobs)

    result = job_service.get_all_jobs(
        status=JobStatus.done,
        language=LanguageCode.en,
        search="interview",
        limit=10,
        offset=20,
        sort_by=JobSortField.updated_at,
        sort_direction=SortDirection.asc,
    )

    assert result == {
        "items": [],
        "total": 0,
        "limit": 10,
        "offset": 20,
    }
    assert calls == [
        {
            "status": JobStatus.done,
            "language": LanguageCode.en,
            "search": "interview",
            "limit": 10,
            "offset": 20,
            "sort_by": JobSortField.updated_at,
            "sort_direction": SortDirection.asc,
        }
    ]
