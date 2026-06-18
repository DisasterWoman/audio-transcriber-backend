from fastapi import APIRouter, HTTPException, UploadFile, File
from app.schemas.job import JobCreate, Job
from app.services.job_service import get_all_jobs, get_job_by_id, create_job
from app.services.file_validation import validate_audio_file
from app.services.file_storage import save_uploaded_file

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=list[Job])
def get_jobs():
    return get_all_jobs()


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    job = get_job_by_id(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/", response_model=Job)
def create_new_job(job: JobCreate):
    return create_job(job)


@router.post("/upload", response_model=Job)
async def upload_audio(
    file: UploadFile = File(...),
    language: str = "ru",
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
