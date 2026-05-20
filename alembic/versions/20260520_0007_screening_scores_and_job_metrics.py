"""screening composite scores + job metrics

Revision ID: 20260520_0007
Revises: 20260519_0006
Create Date: 2026-05-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260520_0007"
down_revision = "20260519_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("screening_results", sa.Column("score_rules", sa.Float(), nullable=False, server_default="0"))
    op.add_column("screening_results", sa.Column("score_total", sa.Float(), nullable=False, server_default="0"))
    op.add_column("screening_results", sa.Column("rules_json", sa.Text(), nullable=False, server_default="{}"))

    op.add_column("jobs", sa.Column("started_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("finished_at", sa.DateTime(), nullable=True))
    op.add_column("jobs", sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("jobs", "duration_ms")
    op.drop_column("jobs", "finished_at")
    op.drop_column("jobs", "started_at")

    op.drop_column("screening_results", "rules_json")
    op.drop_column("screening_results", "score_total")
    op.drop_column("screening_results", "score_rules")

