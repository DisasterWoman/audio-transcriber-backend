from typing import Annotated

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from app.schemas.job import (
    JobCreate,
    JobCreateRequest,
    Job,
    JobList,
    JobListQuery,
    JobTranscript,
    JobStatusUpdate,
    JobTranscriptUpdate,
)
from app.schemas.job_status import JobStatus
from app.schemas.language import LanguageCode
from app.services.job_service import (
    InvalidJobStatusTransition,
    InvalidJobTranscriptUpdate,
    JobTranscriptNotReady,
    MissingJobTranscript,
    get_all_jobs,
    get_job_by_id,
    get_job_transcript,
    create_job,
    update_job_status,
    update_job_transcript,
)
from app.services.file_validation import (
    validate_audio_content_type,
    validate_audio_file,
    validate_audio_file_size,
)
from app.services.file_storage import generate_stored_filename, save_uploaded_file

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobList)
def get_jobs(query: Annotated[JobListQuery, Query()]):
    return get_all_jobs(
        status=query.status,
        language=query.language,
        limit=query.limit,
        offset=query.offset,
        sort_by=query.sort_by,
        sort_direction=query.sort_direction,
    )


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.get("/{job_id}/transcript", response_model=JobTranscript)
def get_transcript(job_id: int):
    try:
        transcript = get_job_transcript(job_id)
    except JobTranscriptNotReady as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    if transcript is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return transcript


@router.post("/", response_model=Job)
def create_new_job(job: JobCreateRequest):
    validate_audio_file(job.original_filename)
    validate_audio_content_type(job.content_type)
    validate_audio_file_size(job.file_size_bytes)

    job_data = JobCreate(
        filename=generate_stored_filename(job.original_filename),
        original_filename=job.original_filename,
        file_size_bytes=job.file_size_bytes,
        content_type=job.content_type,
        language=job.language,
    )

    return create_job(job_data)


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
    validate_audio_content_type(file.content_type)

    stored_file = await save_uploaded_file(file)

    job_data = JobCreate(
        filename=stored_file.filename,
        original_filename=stored_file.original_filename,
        file_size_bytes=stored_file.size_bytes,
        content_type=stored_file.content_type,
        language=language,
    )

    return create_job(job_data)
