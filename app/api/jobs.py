from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from app.schemas.job import (
    JobCreate,
    Job,
    JobList,
    JobStatusUpdate,
    JobTranscriptUpdate,
)
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.services.job_service import (
    InvalidJobStatusTransition,
    InvalidJobTranscriptUpdate,
    MissingJobTranscript,
    get_all_jobs,
    get_job_by_id,
    create_job,
    update_job_status,
    update_job_transcript,
)
from app.services.file_validation import validate_audio_file
from app.services.file_storage import save_uploaded_file

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobList)
def get_jobs(
    status: JobStatus | None = None,
    language: LanguageCode | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return get_all_jobs(
        status=status,
        language=language,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/", response_model=Job)
def create_new_job(job: JobCreate):
    return create_job(job)


@router.patch("/{job_id}/status", response_model=Job)
def update_status(job_id: int, status_update: JobStatusUpdate):
    try:
        job = update_job_status(
            job_id,
            status_update.status,
            status_update.error_message,
        )
    except (InvalidJobStatusTransition, MissingJobTranscript) as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.patch("/{job_id}/transcript", response_model=Job)
def update_transcript(job_id: int, transcript_update: JobTranscriptUpdate):
    try:
        job = update_job_transcript(job_id, transcript_update.transcript_text)
    except InvalidJobTranscriptUpdate as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/upload", response_model=Job)
async def upload_audio(
    file: UploadFile = File(...),
    language: LanguageCode = Form(LanguageCode.ru),
):
    validate_audio_file(file.filename)

    stored_file = await save_uploaded_file(file)

    job_data = JobCreate(
        filename=stored_file.filename,
        original_filename=stored_file.original_filename,
        file_size_bytes=stored_file.size_bytes,
        language=language,
    )

    return create_job(job_data)
