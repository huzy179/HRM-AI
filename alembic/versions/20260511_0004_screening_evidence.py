"""add screening_results.evidence_json

Revision ID: 20260511_0004
Revises: 20260511_0003
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260511_0004"
down_revision = "20260511_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("screening_results", sa.Column("evidence_json", sa.Text(), nullable=False, server_default="[]"))


def downgrade() -> None:
    op.drop_column("screening_results", "evidence_json")

