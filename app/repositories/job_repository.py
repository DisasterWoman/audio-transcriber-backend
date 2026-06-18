jobs = []


def list_jobs():
    return jobs


def get_job(job_id: int):
    for job in jobs:
        if job["id"] == job_id:
            return job

    return None


def save_job(job: dict):
    jobs.append(job)
    return job


def get_next_job_id() -> int:
    return len(jobs) + 1
