"""create transcript revisions

Revision ID: 20260626_0005
Revises: 20260624_0004
Create Date: 2026-06-26

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260626_0005"
down_revision: str | None = "20260624_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transcript_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("transcript_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_transcript_revisions_id"),
        "transcript_revisions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_transcript_revisions_job_id"),
        "transcript_revisions",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_transcript_revisions_job_id_created_at",
        "transcript_revisions",
        ["job_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_transcript_revisions_job_id_version",
        "transcript_revisions",
        ["job_id", "version"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transcript_revisions_job_id_version",
        table_name="transcript_revisions",
    )
    op.drop_index(
        "ix_transcript_revisions_job_id_created_at",
        table_name="transcript_revisions",
    )
    op.drop_index(
        op.f("ix_transcript_revisions_job_id"),
        table_name="transcript_revisions",
    )
    op.drop_index(
        op.f("ix_transcript_revisions_id"),
        table_name="transcript_revisions",
    )
    op.drop_table("transcript_revisions")
