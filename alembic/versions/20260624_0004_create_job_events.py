"""create job events

Revision ID: 20260624_0004
Revises: 20260624_0003
Create Date: 2026-06-24

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260624_0004"
down_revision: str | None = "20260624_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "job_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_events_id"), "job_events", ["id"], unique=False)
    op.create_index(
        op.f("ix_job_events_job_id"),
        "job_events",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_job_events_job_id_created_at",
        "job_events",
        ["job_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_job_events_job_id_created_at", table_name="job_events")
    op.drop_index(op.f("ix_job_events_job_id"), table_name="job_events")
    op.drop_index(op.f("ix_job_events_id"), table_name="job_events")
    op.drop_table("job_events")
