from fastapi import APIRouter, HTTPException

from app.repositories.job_repository import is_database_ready
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
        raise HTTPException(
            status_code=503,
            detail="Upload directory is not ready",
        )

    if not is_database_ready():
        raise HTTPException(
            status_code=503,
            detail="Database is not ready",
        )

    return {"status": "ready"}
