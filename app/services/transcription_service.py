from pathlib import Path

from app.core.settings import settings
from app.schemas.language import LanguageCode


class UnsupportedTranscriptionProvider(Exception):
    def __init__(self, provider: str):
        super().__init__(f"Unsupported transcription provider: {provider}")


def transcribe_audio(file_path: Path, language: LanguageCode) -> str:
    if settings.transcription_provider == "stub":
        return create_stub_transcript(file_path, language)

    raise UnsupportedTranscriptionProvider(settings.transcription_provider)


def create_stub_transcript(file_path: Path, language: LanguageCode) -> str:
    return (
        f"{settings.stub_transcript_text} "
        f"File: {file_path.name}. Language: {language.value}."
    )
