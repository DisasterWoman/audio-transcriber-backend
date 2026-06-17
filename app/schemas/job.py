from pydantic import BaseModel
from app.schemas.job_status import JobStatus


class JobCreate(BaseModel):
    filename: str
    original_filename: str
    language: str


class Job(BaseModel):
    id: int
    filename: str
    original_filename: str
    language: str
    status: JobStatus