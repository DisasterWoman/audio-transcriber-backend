from datetime import UTC, datetime

from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models.job import JobEventModel
from app.repositories.pagination import build_paginated_response
from app.schemas.job_event import JobEventCreate, JobEventType
from app.schemas.sorting import SortDirection


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


def list_job_events(
    job_id: int,
    event_type: JobEventType | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_direction: SortDirection = SortDirection.asc,
) -> dict:
    filters = [JobEventModel.job_id == job_id]

    if event_type is not None:
        filters.append(JobEventModel.event_type == event_type.value)

    sort_columns = [JobEventModel.created_at, JobEventModel.id]

    if sort_direction == SortDirection.desc:
        sort_columns = [column.desc() for column in sort_columns]

    total_statement = select(func.count()).select_from(JobEventModel).where(*filters)
    events_statement = (
        select(JobEventModel)
        .where(*filters)
        .order_by(*sort_columns)
        .limit(limit)
        .offset(offset)
    )

    with SessionLocal() as session:
        total = session.scalar(total_statement) or 0
        events = session.scalars(events_statement).all()

    return build_paginated_response(
        items=[model_to_job_event(event) for event in events],
        total=total,
        limit=limit,
        offset=offset,
    )


def model_to_job_event(event: JobEventModel) -> dict:
    return {
        "id": event.id,
        "job_id": event.job_id,
        "event_type": JobEventType(event.event_type),
        "message": event.message,
        "created_at": event.created_at,
    }
