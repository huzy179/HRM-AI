"""screening run hash for idempotency

Revision ID: 20260523_0010
Revises: 20260523_0009
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_0010"
down_revision = "20260523_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("screening_results", sa.Column("run_hash", sa.String(length=64), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("screening_results", "run_hash")

