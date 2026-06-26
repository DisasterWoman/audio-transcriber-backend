"""add audio source metadata

Revision ID: 20260626_0006
Revises: 20260626_0005
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260626_0006"
down_revision: str | None = "20260626_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "audio_source",
            sa.String(length=50),
            server_default="uploaded_file",
            nullable=False,
        ),
    )
    op.add_column(
        "jobs",
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_jobs_audio_source",
        "jobs",
        ["audio_source"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_audio_source", table_name="jobs")
    op.drop_column("jobs", "duration_seconds")
    op.drop_column("jobs", "audio_source")
