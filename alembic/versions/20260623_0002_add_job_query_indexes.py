"""add job query indexes

Revision ID: 20260623_0002
Revises: 20260623_0001
Create Date: 2026-06-23
"""

from alembic import op

revision = "20260623_0002"
down_revision = "20260623_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_jobs_language", "jobs", ["language"], unique=False)
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"], unique=False)
    op.create_index("ix_jobs_updated_at", "jobs", ["updated_at"], unique=False)
    op.create_index(
        "ix_jobs_file_size_bytes", "jobs", ["file_size_bytes"], unique=False
    )
    op.create_index(
        "ix_jobs_status_language_created_at",
        "jobs",
        ["status", "language", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_status_language_created_at", table_name="jobs")
    op.drop_index("ix_jobs_file_size_bytes", table_name="jobs")
    op.drop_index("ix_jobs_updated_at", table_name="jobs")
    op.drop_index("ix_jobs_created_at", table_name="jobs")
    op.drop_index("ix_jobs_language", table_name="jobs")
