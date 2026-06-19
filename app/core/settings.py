from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str
    app_env: str

    api_prefix: str
    debug: bool

    upload_dir: str
    max_upload_size_mb: int = 25

    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    allowed_audio_extensions: str

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


settings = Settings()
