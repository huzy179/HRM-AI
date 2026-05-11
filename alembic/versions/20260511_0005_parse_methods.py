"""add parse/ingest method columns

Revision ID: 20260511_0005
Revises: 20260511_0004
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260511_0005"
down_revision = "20260511_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_descriptions",
        sa.Column("parse_method", sa.String(length=50), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "candidates",
        sa.Column("parse_method", sa.String(length=50), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "policy_documents",
        sa.Column("ingest_method", sa.String(length=50), nullable=False, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("policy_documents", "ingest_method")
    op.drop_column("candidates", "parse_method")
    op.drop_column("job_descriptions", "parse_method")

