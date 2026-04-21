from fastapi import APIRouter, HTTPException
from app.schemas.job import JobCreate, Job
from app.services.job_service import get_all_jobs, get_job_by_id, create_job
from fastapi import UploadFile, File
import os
from app.core.settings import settings
import uuid

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

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    filename = f"{file_id}.{file_extension}"

    file_path = os.path.join(settings.upload_dir, filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return {
        "file_id": file_id,
        "filename": filename
    }