from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Form, Query, UploadFile
from fastapi.responses import PlainTextResponse

from app.core.errors import NotFoundError
from app.core.settings import settings
from app.schemas.job import (
    Job,
    JobCreate,
    JobCreateRequest,
    JobList,
    JobListQuery,
    JobStats,
    JobStatusUpdate,
    JobTranscript,
    JobTranscriptUpdate,
)
from app.schemas.language import LanguageCode
from app.services.file_storage import generate_stored_filename, save_uploaded_file
from app.services.file_validation import (
    validate_audio_content_type,
    validate_audio_file,
    validate_audio_file_size,
)
from app.services.job_processing import (
    process_job,
    retry_job_processing,
    start_job_processing,
)
from app.services.job_service import (
    create_job,
    delete_job_by_id,
    get_all_jobs,
    get_job_by_id,
    get_job_stats,
    get_job_transcript,
    update_job_status,
    update_job_transcript,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobList)
def get_jobs(query: Annotated[JobListQuery, Query()]):
    return get_all_jobs(
        status=query.status,
        language=query.language,
        search=query.search,
        created_from=query.created_from,
        created_to=query.created_to,
        limit=query.limit,
        offset=query.offset,
        sort_by=query.sort_by,
        sort_direction=query.sort_direction,
    )


@router.get("/stats", response_model=JobStats)
def get_jobs_stats():
    return get_job_stats()


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        raise NotFoundError("Job not found")

    return job


@router.get("/{job_id}/transcript", response_model=JobTranscript)
def get_transcript(job_id: int):
    transcript = get_job_transcript(job_id)

    if transcript is None:
        raise NotFoundError("Job not found")

    return transcript


@router.get("/{job_id}/transcript/download", response_class=PlainTextResponse)
def download_transcript(job_id: int):
    transcript = get_job_transcript(job_id)

    if transcript is None:
        raise NotFoundError("Job not found")

    filename = f"job-{job_id}-transcript.txt"

    return PlainTextResponse(
        content=transcript["transcript_text"],
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.delete("/{job_id}", status_code=204)
def delete_existing_job(job_id: int):
    deleted = delete_job_by_id(job_id)

    if not deleted:
        raise NotFoundError("Job not found")

    return None


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
    job = update_job_status(
        job_id,
        status_update.status,
        status_update.error_message,
    )

    if job is None:
        raise NotFoundError("Job not found")

    return job


@router.patch("/{job_id}/transcript", response_model=Job)
def update_transcript(job_id: int, transcript_update: JobTranscriptUpdate):
    job = update_job_transcript(job_id, transcript_update.transcript_text)

    if job is None:
        raise NotFoundError("Job not found")

    return job


@router.post("/{job_id}/process", response_model=Job)
def process_existing_job(job_id: int, background_tasks: BackgroundTasks):
    job = start_job_processing(job_id)

    if job is None:
        raise NotFoundError("Job not found")

    background_tasks.add_task(process_job, job_id)

    return job


@router.post("/{job_id}/retry", response_model=Job)
def retry_job(job_id: int, background_tasks: BackgroundTasks):
    job = retry_job_processing(job_id)

    if job is None:
        raise NotFoundError("Job not found")

    background_tasks.add_task(process_job, job_id)

    return job


@router.post("/upload", response_model=Job)
async def upload_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: LanguageCode = Form(LanguageCode.ru),
    auto_process: bool | None = Form(None),
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

    job = create_job(job_data)

    should_process = settings.auto_process_uploads

    if auto_process is not None:
        should_process = auto_process

    if should_process:
        background_tasks.add_task(process_job, job["id"])

    return job
