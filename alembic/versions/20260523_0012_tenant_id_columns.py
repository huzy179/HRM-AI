"""tenant_id columns for multi-tenant scoping

Revision ID: 20260523_0012
Revises: 20260523_0011
Create Date: 2026-05-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260523_0012"
down_revision = "20260523_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # campaigns
    op.add_column("campaigns", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # campaign_settings
    op.add_column("campaign_settings", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # job_descriptions
    op.add_column("job_descriptions", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # candidates
    op.add_column("candidates", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # candidate_profiles
    op.add_column("candidate_profiles", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # screening_results
    op.add_column("screening_results", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # review_results
    op.add_column("review_results", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # policy_documents
    op.add_column("policy_documents", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # jobs
    op.add_column("jobs", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))

    # audit_events
    op.add_column("audit_events", sa.Column("tenant_id", sa.String(length=50), nullable=False, server_default="default"))


def downgrade() -> None:
    op.drop_column("audit_events", "tenant_id")
    op.drop_column("jobs", "tenant_id")
    op.drop_column("policy_documents", "tenant_id")
    op.drop_column("review_results", "tenant_id")
    op.drop_column("screening_results", "tenant_id")
    op.drop_column("candidate_profiles", "tenant_id")
    op.drop_column("candidates", "tenant_id")
    op.drop_column("job_descriptions", "tenant_id")
    op.drop_column("campaign_settings", "tenant_id")
    op.drop_column("campaigns", "tenant_id")

