"""add review_results

Revision ID: 20260511_0002
Revises: 20260510_0001
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260511_0002"
down_revision = "20260510_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_results",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("score_llm", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths_json", sa.Text(), nullable=False),
        sa.Column("gaps_json", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("review_results")

