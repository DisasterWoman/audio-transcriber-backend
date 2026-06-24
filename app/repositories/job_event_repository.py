from datetime import UTC, datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.job import JobEventModel
from app.schemas.job_event import JobEventCreate, JobEventType


def save_job_event(event: JobEventCreate) -> dict:
    with SessionLocal() as session:
        event_model = JobEventModel(
            job_id=event.job_id,
            event_type=event.event_type.value,
            message=event.message,
            created_at=datetime.now(UTC),
        )
        session.add(event_model)
        session.commit()
        session.refresh(event_model)
        return model_to_job_event(event_model)


def list_job_events(job_id: int) -> dict:
    statement = (
        select(JobEventModel)
        .where(JobEventModel.job_id == job_id)
        .order_by(JobEventModel.created_at.asc(), JobEventModel.id.asc())
    )

    with SessionLocal() as session:
        events = session.scalars(statement).all()

    return {
        "items": [model_to_job_event(event) for event in events],
        "total": len(events),
    }


def model_to_job_event(event: JobEventModel) -> dict:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "event_type": JobEventType(event.event_type),
        "message": event.message,
        "created_at": event.created_at,
    }
