from app.schemas.job_status import JobStatus
from app.services import job_service
from tests.factories import make_job


def test_delete_job_by_id_removes_database_row_and_file(monkeypatch):
    stored_job = make_job(JobStatus.done)
    deleted_files = []

    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: stored_job)
    monkeypatch.setattr(job_service, "delete_job", lambda job_id: True)
    monkeypatch.setattr(
        job_service,
        "delete_stored_file",
        lambda filename: deleted_files.append(filename),
    )

    deleted = job_service.delete_job_by_id(1)

    assert deleted is True
    assert deleted_files == ["stored.mp3"]


def test_delete_job_by_id_returns_false_when_job_does_not_exist(monkeypatch):
    monkeypatch.setattr(job_service, "get_job_by_id", lambda job_id: None)

    deleted = job_service.delete_job_by_id(1)

    assert deleted is False
