from fastapi import APIRouter, HTTPException
from app.schemas.job import JobCreate, Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

jobs = []


@router.get("/", response_model=list[Job])
def get_jobs():
    return jobs


@router.get("/{job_id}", response_model=Job)
def get_job(job_id: int):
    for job in jobs:
        if job["id"] == job_id:
            return job

    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/", response_model=Job)
def create_job(job: JobCreate):
    new_job = {
        "id": len(jobs) + 1,
        "filename": job.filename,
        "language": job.language,
        "status": "queued",
    }
    jobs.append(new_job)
    return new_job