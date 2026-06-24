"""add job processing attempts

Revision ID: 20260624_0003
Revises: 20260623_0002
Create Date: 2026-06-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260624_0003"
down_revision = "20260623_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jobs",
        sa.Column(
            "processing_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("jobs", "processing_attempts")
