from fastapi import APIRouter

from app.core.errors import ServiceUnavailableError
from app.core.settings import settings
from app.repositories.job_repository import is_database_ready
from app.schemas.upload import UploadConstraints
from app.services.file_storage import is_upload_dir_ready

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Backend is running"}


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.get("/ready")
def readiness_check():
    if not is_upload_dir_ready():
        raise ServiceUnavailableError("Upload directory is not ready")

    if not is_database_ready():
        raise ServiceUnavailableError("Database is not ready")

    return {"status": "ready"}


@router.get("/upload-constraints", response_model=UploadConstraints)
def get_upload_constraints():
    return {
        "max_upload_size_mb": settings.max_upload_size_mb,
        "max_upload_size_bytes": settings.max_upload_size_mb * 1024 * 1024,
        "allowed_audio_extensions": sorted(settings.allowed_audio_extension_set),
        "allowed_audio_mime_types": sorted(settings.allowed_audio_mime_type_set),
    }
