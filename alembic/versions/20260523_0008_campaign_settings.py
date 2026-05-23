"""campaign settings for composite scoring

Revision ID: 20260523_0008
Revises: 20260520_0007
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_0008"
down_revision = "20260520_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaign_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), nullable=False, unique=True),
        sa.Column("w_embed", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("required_skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("min_years_override", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("campaign_settings")

