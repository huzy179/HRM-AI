"""candidate profiles + text quality metrics

Revision ID: 20260519_0006
Revises: 20260511_0005
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260519_0006"
down_revision = "20260511_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("parse_chars", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("candidates", sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("candidates", sa.Column("quality_reason", sa.String(length=100), nullable=False, server_default=""))

    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("candidates.id"), nullable=False, unique=True),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("email", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("years_experience", sa.Float(), nullable=False, server_default="0"),
        sa.Column("education", sa.Text(), nullable=False, server_default=""),
        sa.Column("skills_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("candidate_profiles")
    op.drop_column("candidates", "quality_reason")
    op.drop_column("candidates", "quality_score")
    op.drop_column("candidates", "parse_chars")

