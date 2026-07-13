from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260714_0016"
down_revision = "20260713_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policy_eval_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"),
        sa.Column("name", sa.String(length=200), nullable=False, server_default="Policy eval"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("passed_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "policy_eval_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("run_id", sa.Integer(), sa.ForeignKey("policy_eval_runs.id"), nullable=False),
        sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_source", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("expected_keywords_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("citations_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade() -> None:
    op.drop_table("policy_eval_items")
    op.drop_table("policy_eval_runs")
