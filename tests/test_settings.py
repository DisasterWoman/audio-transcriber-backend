import pytest
from pydantic import ValidationError

from app.core.settings import Settings


def make_settings(**overrides) -> Settings:
    values = {
        "app_name": "Audio Transcriber Backend",
        "app_env": "test",
        "api_prefix": "/api",
        "debug": True,
        "upload_dir": "uploads",
        "allowed_audio_extensions": "mp3,wav",
    }
    values.update(overrides)

    return Settings(**values)


def test_settings_accept_valid_values():
    settings = make_settings()

    assert settings.app_env == "test"
    assert settings.max_upload_size_mb == 25
    assert settings.max_processing_attempts == 3
    assert settings.transcription_provider == "stub"


def test_settings_can_load_without_env_file():
    settings = Settings(_env_file=None)

    assert settings.app_name == "Audio Transcriber Backend"
    assert settings.api_prefix == "/api"
    assert settings.upload_dir == "uploads"
    assert settings.allowed_audio_extension_set == {"m4a", "mp3", "wav", "webm"}


def test_settings_reject_invalid_environment():
    with pytest.raises(ValidationError):
        make_settings(app_env="staging")


def test_settings_reject_invalid_log_level():
    with pytest.raises(ValidationError):
        make_settings(log_level="TRACE")


def test_settings_reject_empty_csv_values():
    with pytest.raises(ValidationError):
        make_settings(allowed_audio_extensions=",,")


def test_settings_reject_too_small_upload_limit():
    with pytest.raises(ValidationError):
        make_settings(max_upload_size_mb=0)


def test_settings_reject_too_small_processing_attempt_limit():
    with pytest.raises(ValidationError):
        make_settings(max_processing_attempts=0)
