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


def test_job_summary_endpoint(monkeypatch):
    calls = []
    job = make_job(JobStatus.done)
    job["transcript_text"] = "Full transcript should not be in summary response"
    job["transcript_preview"] = "Full transcript should not..."

    def fake_get_job_summary(recent_limit: int):
        calls.append(recent_limit)
        return {
            "stats": {
                "total": 2,
                "queued": 1,
                "processing": 0,
                "done": 1,
                "failed": 0,
            },
            "recent_jobs": {
                "items": [job],
                "total": 0,
                "count": 1,
                "limit": recent_limit,
                "offset": 0,
                "has_next": False,
                "has_previous": False,
                "next_offset": None,
                "previous_offset": None,
            },
        }

    monkeypatch.setattr(jobs_api, "get_job_summary", fake_get_job_summary)

    response = client.get("/api/jobs/summary?recent_limit=3")

    assert response.status_code == 200
    assert response.json()["stats"]["total"] == 2
    assert response.json()["recent_jobs"]["limit"] == 3
    recent_job = response.json()["recent_jobs"]["items"][0]
    assert "transcript_text" not in recent_job
    assert recent_job["transcript_preview"] == "Full transcript should not..."
    assert calls == [3]


def test_job_summary_endpoint_rejects_invalid_recent_limit():
    response = client.get("/api/jobs/summary?recent_limit=0")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_job_actions_endpoint(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_actions",
        lambda job_id: {
            "job_id": job_id,
            "process": {"enabled": True, "reason": None},
            "retry": {"enabled": False, "reason": "Can only retry failed jobs"},
            "download_transcript": {
                "enabled": False,
                "reason": "Transcript is only available after the job is done",
            },
            "download_audio": {"enabled": True, "reason": None},
            "processing_attempts": 0,
            "max_processing_attempts": 3,
            "retry_attempts_remaining": 3,
        },
    )

    response = client.get("/api/jobs/1/actions")

    assert response.status_code == 200
    assert response.json()["job_id"] == 1
    assert response.json()["process"] == {"enabled": True, "reason": None}
    assert response.json()["retry"]["enabled"] is False
    assert response.json()["retry_attempts_remaining"] == 3


def test_job_actions_endpoint_returns_404_when_job_is_missing(monkeypatch):
    monkeypatch.setattr(jobs_api, "get_job_actions", lambda job_id: None)

    response = client.get("/api/jobs/999/actions")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not found"


def test_job_status_endpoint(monkeypatch):
    job = make_job(JobStatus.processing)

    monkeypatch.setattr(
        jobs_api,
        "get_job_status_detail",
        lambda job_id: {
            "job_id": job_id,
            "status": job["status"],
            "is_terminal": job["is_terminal"],
            "processing_attempts": job["processing_attempts"],
            "max_processing_attempts": 3,
            "retry_attempts_remaining": 3,
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "processing_duration_seconds": job["processing_duration_seconds"],
            "total_duration_seconds": job["total_duration_seconds"],
            "failure_summary": job["failure_summary"],
        },
    )

    response = client.get("/api/jobs/1/status")

    assert response.status_code == 200
    assert response.json()["job_id"] == 1
    assert response.json()["status"] == "processing"
    assert "transcript_text" not in response.json()


def test_job_status_endpoint_returns_404_when_job_is_missing(monkeypatch):
    monkeypatch.setattr(jobs_api, "get_job_status_detail", lambda job_id: None)

    response = client.get("/api/jobs/999/status")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not found"


def test_job_events_endpoint(monkeypatch):
    calls = []

    def fake_get_events_for_job(job_id, **kwargs):
        call = {"job_id": job_id, **kwargs}
        calls.append(call)
        return {
            "items": [
                {
                    "id": 1,
                    "job_id": job_id,
                    "event_type": "job_created",
                    "message": "Job was created and queued for transcription",
                    "created_at": "2026-06-24T12:00:00Z",
                }
            ],
            "total": 1,
            "count": 1,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
            "has_next": False,
            "has_previous": True,
            "next_offset": None,
            "previous_offset": 0,
        }

    monkeypatch.setattr(
        jobs_api,
        "get_events_for_job",
        fake_get_events_for_job,
    )

    response = client.get(
        "/api/jobs/1/events?event_type=job_created&limit=10"
        "&offset=5&sort_direction=desc"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["count"] == 1
    assert response.json()["limit"] == 10
    assert response.json()["offset"] == 5
    assert response.json()["has_next"] is False
    assert response.json()["has_previous"] is True
    assert response.json()["items"][0]["event_type"] == "job_created"
    assert calls == [
        {
            "job_id": 1,
            "event_type": "job_created",
            "limit": 10,
            "offset": 5,
            "sort_direction": "desc",
        }
    ]


def test_job_events_endpoint_returns_404_when_job_is_missing(monkeypatch):
    monkeypatch.setattr(jobs_api, "get_events_for_job", lambda job_id, **kwargs: None)

    response = client.get("/api/jobs/999/events")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not found"


def test_jobs_list_accepts_search_query(monkeypatch):
    calls = []

    def fake_get_all_jobs(**kwargs):
        calls.append(kwargs)
        return {
            "items": [],
            "total": 0,
            "count": 0,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
            "has_next": False,
            "has_previous": False,
            "next_offset": None,
            "previous_offset": None,
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
        "count": 0,
        "limit": 10,
        "offset": 0,
        "has_next": False,
        "has_previous": False,
        "next_offset": None,
        "previous_offset": None,
    }
    assert calls[0]["search"] == "interview"
    assert calls[0]["language"] == "en"
    assert calls[0]["created_from"].year == 2026
    assert calls[0]["created_to"].year == 2026


def test_jobs_list_omits_full_transcript_text(monkeypatch):
    job = make_job(JobStatus.done)
    job["transcript_text"] = "Full transcript should not be in list response"
    job["transcript_preview"] = "Full transcript should not..."

    monkeypatch.setattr(
        jobs_api,
        "get_all_jobs",
        lambda **kwargs: {
            "items": [job],
            "total": 1,
            "count": 1,
            "limit": kwargs["limit"],
            "offset": kwargs["offset"],
            "has_next": False,
            "has_previous": False,
            "next_offset": None,
            "previous_offset": None,
        },
    )

    response = client.get("/api/jobs/")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert "transcript_text" not in item
    assert item["transcript_preview"] == "Full transcript should not..."


def test_jobs_list_rejects_invalid_created_range():
    response = client.get(
        "/api/jobs/?created_from=2026-06-30T00:00:00Z"
        "&created_to=2026-06-01T00:00:00Z"
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_get_transcript_returns_text_and_metadata(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_transcript",
        lambda job_id: {
            "job_id": job_id,
            "transcript_text": "Hello from transcript",
            "character_count": 21,
            "word_count": 3,
        },
    )

    response = client.get("/api/jobs/1/transcript")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": 1,
        "transcript_text": "Hello from transcript",
        "character_count": 21,
        "word_count": 3,
    }


def test_get_transcript_metadata_endpoint(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_transcript_metadata",
        lambda job_id: {
            "job_id": job_id,
            "character_count": 21,
            "word_count": 3,
        },
    )

    response = client.get("/api/jobs/1/transcript/metadata")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": 1,
        "character_count": 21,
        "word_count": 3,
    }


def test_get_transcript_metadata_returns_404_when_job_is_missing(monkeypatch):
    monkeypatch.setattr(jobs_api, "get_job_transcript_metadata", lambda job_id: None)

    response = client.get("/api/jobs/999/transcript/metadata")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Job not found"


def test_download_transcript_returns_text_file(monkeypatch):
    monkeypatch.setattr(
        jobs_api,
        "get_job_transcript",
        lambda job_id: {
            "job_id": job_id,
            "transcript_text": "Hello from transcript",
            "character_count": 21,
            "word_count": 3,
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


def test_download_audio_returns_original_file(monkeypatch, tmp_path):
    audio_path = tmp_path / "stored.mp3"
    audio_path.write_bytes(b"fake audio bytes")

    job = make_job(JobStatus.done)
    job["content_type"] = "audio/mpeg"
    job["original_filename"] = "interview.mp3"

    monkeypatch.setattr(jobs_api, "get_job_by_id", lambda job_id: job)
    monkeypatch.setattr(jobs_api, "stored_file_exists", lambda filename: True)
    monkeypatch.setattr(jobs_api, "get_stored_file_path", lambda filename: audio_path)

    response = client.get("/api/jobs/1/audio/download")

    assert response.status_code == 200
    assert response.content == b"fake audio bytes"
    assert response.headers["content-type"] == "audio/mpeg"
    assert 'filename="interview.mp3"' in response.headers["content-disposition"]


def test_download_audio_returns_404_when_file_is_missing(monkeypatch):
    job = make_job(JobStatus.done)

    monkeypatch.setattr(jobs_api, "get_job_by_id", lambda job_id: job)
    monkeypatch.setattr(jobs_api, "stored_file_exists", lambda filename: False)

    response = client.get("/api/jobs/1/audio/download")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Stored audio file not found"


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
