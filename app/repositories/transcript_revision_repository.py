from datetime import UTC, datetime

from sqlalchemy import desc, func, select

from app.db.session import SessionLocal
from app.models.job import TranscriptRevisionModel
from app.repositories.job_repository import build_transcript_preview
from app.repositories.pagination import build_paginated_response
from app.schemas.sorting import SortDirection
from app.services.transcript_service import get_transcript_metadata


def save_transcript_revision(job_id: int, transcript_text: str) -> dict:
    with SessionLocal() as session:
        version = get_next_revision_version(session, job_id)
        revision_model = TranscriptRevisionModel(
            job_id=job_id,
            version=version,
            transcript_text=transcript_text,
            created_at=datetime.now(UTC),
        )
        session.add(revision_model)
        session.commit()
        session.refresh(revision_model)
        return model_to_transcript_revision(revision_model)


def list_transcript_revisions(
    job_id: int,
    limit: int = 50,
    offset: int = 0,
    sort_direction: SortDirection = SortDirection.desc,
) -> dict:
    filters = [TranscriptRevisionModel.job_id == job_id]
    sort_column = TranscriptRevisionModel.version

    if sort_direction == SortDirection.desc:
        sort_column = desc(sort_column)

    total_statement = (
        select(func.count())
        .select_from(TranscriptRevisionModel)
        .where(*filters)
    )
    revisions_statement = (
        select(TranscriptRevisionModel)
        .where(*filters)
        .order_by(sort_column)
        .limit(limit)
        .offset(offset)
    )

    with SessionLocal() as session:
        total = session.scalar(total_statement) or 0
        revisions = session.scalars(revisions_statement).all()

    return build_paginated_response(
        items=[
            model_to_transcript_revision_summary(revision)
            for revision in revisions
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_transcript_revision(job_id: int, version: int) -> dict | None:
    statement = select(TranscriptRevisionModel).where(
        TranscriptRevisionModel.job_id == job_id,
        TranscriptRevisionModel.version == version,
    )

    with SessionLocal() as session:
        revision = session.scalar(statement)

    if revision is None:
        return None

    return model_to_transcript_revision(revision)


def get_next_revision_version(session, job_id: int) -> int:
    statement = select(func.max(TranscriptRevisionModel.version)).where(
        TranscriptRevisionModel.job_id == job_id
    )
    latest_version = session.scalar(statement)
    return (latest_version or 0) + 1


def model_to_transcript_revision_summary(
    revision: TranscriptRevisionModel,
) -> dict:
    metadata = get_transcript_metadata(revision.transcript_text)

    return {
        "id": revision.id,
        "job_id": revision.job_id,
        "version": revision.version,
        "created_at": revision.created_at,
        "character_count": metadata["character_count"],
        "word_count": metadata["word_count"],
        "transcript_preview": build_transcript_preview(revision.transcript_text),
    }


def model_to_transcript_revision(revision: TranscriptRevisionModel) -> dict:
    return {
        **model_to_transcript_revision_summary(revision),
        "transcript_text": revision.transcript_text,
    }
