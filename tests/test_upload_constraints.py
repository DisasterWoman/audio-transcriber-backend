from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_upload_constraints_endpoint_returns_frontend_rules():
    response = client.get("/api/upload-constraints")

    assert response.status_code == 200
    assert response.json() == {
        "max_upload_size_mb": 25,
        "max_upload_size_bytes": 25 * 1024 * 1024,
        "allowed_audio_extensions": ["m4a", "mp3", "wav", "webm"],
        "allowed_audio_mime_types": [
            "audio/mp4",
            "audio/mpeg",
            "audio/wav",
            "audio/webm",
            "audio/x-wav",
        ],
    }
