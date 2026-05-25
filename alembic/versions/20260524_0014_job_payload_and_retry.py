"""job payload_json + retry fields

Revision ID: 20260524_0014
Revises: 20260524_0013
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_0014"
down_revision = "20260524_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("payload_json", sa.Text(), nullable=False, server_default="{}"))
    op.add_column("jobs", sa.Column("parent_job_id", sa.String(length=36), nullable=False, server_default=""))
    op.add_column("jobs", sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"))

    op.create_index("ix_jobs_tenant_type_created", "jobs", ["tenant_id", "job_type", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_jobs_tenant_type_created", table_name="jobs")
    op.drop_column("jobs", "attempt")
    op.drop_column("jobs", "parent_job_id")
    op.drop_column("jobs", "payload_json")

