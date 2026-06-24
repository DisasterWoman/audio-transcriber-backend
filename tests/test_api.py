from fastapi.testclient import TestClient

from app.api import jobs as jobs_api
from app.main import app
from app.schemas.job_status import JobStatus
from app.services.file_storage import StoredFile
from tests.factories import make_job

client = TestClient(app)


def test_health_response_has_request_id_header():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


def test_not_found_uses_consistent_error_shape(monkeypatch):
    monkeypatch.setattr(jobs_api, "get_job_by_id", lambda job_id: None)

    response = client.get("/api/jobs/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
    assert response.json()["error"]["message"] == "Job not found"
    assert response.json()["error"]["request_id"]


def test_validation_error_uses_consistent_error_shape():
    response = client.get("/api/jobs/?limit=0")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["message"] == "Request validation failed"
    assert response.json()["error"]["details"]


def test_job_stats_endpoint(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_stats",
        lambda: {
            "total": 4,
            "queued": 1,
            "processing": 1,
            "done": 1,
            "failed": 1,
        },
    )

    response = client.get("/api/jobs/stats")

    assert response.status_code == 200
    assert response.json() == {
        "total": 4,
        "queued": 1,
        "processing": 1,
        "done": 1,
        "failed": 1,
    }


def test_jobs_list_accepts_search_query(monkeypatch):
    calls = []

    def fake_get_all_jobs(**kwargs):
        calls.append(kwargs)
        return {
            "items": [],
            "total": 0,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
        }

    monkeypatch.setattr(jobs_api, "get_all_jobs", fake_get_all_jobs)

    response = client.get(
        "/api/jobs/?search=interview&language=en&limit=10"
        "&created_from=2026-06-01T00:00:00Z"
        "&created_to=2026-06-30T23:59:59Z"
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 10,
        "offset": 0,
    }
    assert calls[0]["search"] == "interview"
    assert calls[0]["language"] == "en"
    assert calls[0]["created_from"].year == 2026
    assert calls[0]["created_to"].year == 2026


def test_jobs_list_rejects_invalid_created_range():
    response = client.get(
        "/api/jobs/?created_from=2026-06-30T00:00:00Z"
        "&created_to=2026-06-01T00:00:00Z"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_download_transcript_returns_text_file(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_transcript",
        lambda job_id: {
            "job_id": job_id,
            "transcript_text": "Hello from transcript",
        },
    )

    response = client.get("/api/jobs/1/transcript/download")

    assert response.status_code == 200
    assert response.text == "Hello from transcript"
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    assert (
        response.headers["content-disposition"]
        == 'attachment; filename="job-1-transcript.txt"'
    )


def test_upload_can_skip_auto_processing(monkeypatch):
    created_job = make_job(JobStatus.queued)
    process_calls = []

    async def fake_save_uploaded_file(file):
        return StoredFile(
            filename="stored.mp3",
            original_filename="interview.mp3",
            size_bytes=123,
            content_type="audio/mpeg",
        )

    def fake_process_job(job_id: int):
        process_calls.append(job_id)

    monkeypatch.setattr(jobs_api, "save_uploaded_file", fake_save_uploaded_file)
    monkeypatch.setattr(jobs_api, "create_job", lambda job_data: created_job)
    monkeypatch.setattr(jobs_api, "process_job", fake_process_job)

    response = client.post(
        "/api/jobs/upload",
        files={"file": ("interview.mp3", b"fake audio bytes", "audio/mpeg")},
        data={"language": "en", "auto_process": "false"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert process_calls == []


def test_process_endpoint_schedules_background_task(monkeypatch):
    processing_job = make_job(JobStatus.processing)
    process_calls = []

    monkeypatch.setattr(
        jobs_api,
        "start_job_processing",
        lambda job_id: processing_job,
    )
    monkeypatch.setattr(
        jobs_api,
        "process_job",
        lambda job_id: process_calls.append(job_id),
    )

    response = client.post("/api/jobs/1/process")

    assert response.status_code == 200
    assert response.json()["status"] == "processing"
    assert process_calls == [1]


def test_delete_job_returns_no_content(monkeypatch):
    monkeypatch.setattr(jobs_api, "delete_job_by_id", lambda job_id: True)

    response = client.delete("/api/jobs/1")

    assert response.status_code == 204
    assert response.content == b""
