from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Audio Transcriber Backend"
    app_env: Literal["development", "test", "production"] = "development"

    api_prefix: str = "/api"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    upload_dir: str = "uploads"
    database_url: str = (
        "postgresql+psycopg://transcriber:transcriber@localhost:5432/audio_transcriber"
    )
    max_upload_size_mb: int = Field(default=25, ge=1)
    auto_process_uploads: bool = True
    transcription_provider: Literal["stub"] = "stub"
    stub_transcript_text: str = Field(
        default="This is a development transcript placeholder.",
        min_length=1,
    )

    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    allowed_audio_extensions: str = "mp3,wav,m4a,webm"
    allowed_audio_mime_types: str = (
        "audio/mpeg,audio/wav,audio/x-wav,audio/mp4,audio/webm"
    )

    @field_validator(
        "allowed_audio_extensions",
        "allowed_audio_mime_types",
        "cors_allowed_origins",
    )
    @classmethod
    def validate_csv_setting(cls, value: str) -> str:
        if not [item for item in value.split(",") if item.strip()]:
            raise ValueError("must contain at least one comma-separated value")

        return value

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_audio_extension_set(self) -> set[str]:
        return {
            extension.strip().lower().lstrip(".")
            for extension in self.allowed_audio_extensions.split(",")
            if extension.strip()
        }

    @property
    def allowed_audio_mime_type_set(self) -> set[str]:
        return {
            mime_type.strip().lower()
            for mime_type in self.allowed_audio_mime_types.split(",")
            if mime_type.strip()
        }


settings = Settings()
