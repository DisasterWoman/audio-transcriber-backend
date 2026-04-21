from app.schemas.job import JobCreate


jobs = []


def get_all_jobs():
    return jobs


def get_job_by_id(job_id: int):
    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def create_job(job_data: JobCreate):
    new_job = {
        "id": len(jobs) + 1,
        "filename": job_data.filename,
        "language": job_data.language,
        "status": "queued",
    }
    jobs.append(new_job)
    return new_job