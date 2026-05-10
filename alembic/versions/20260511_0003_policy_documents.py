"""add policy_documents

Revision ID: 20260511_0003
Revises: 20260511_0002
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260511_0003"
down_revision = "20260511_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_documents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("ingest_status", sa.String(length=50), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policy_documents")

