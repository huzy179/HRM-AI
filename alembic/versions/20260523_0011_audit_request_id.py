"""audit request id

Revision ID: 20260523_0011
Revises: 20260523_0010
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_0011"
down_revision = "20260523_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("request_id", sa.String(length=36), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("audit_events", "request_id")

