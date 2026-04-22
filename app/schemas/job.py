from pydantic import BaseModel


class JobCreate(BaseModel):
    filename: str
    language: str


class Job(BaseModel):
    id: int
    filename: str
    original_filename: str
    language: str
    status: str