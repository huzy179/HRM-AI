"""job result_json + indexes

Revision ID: 20260524_0013
Revises: 20260523_0012
Create Date: 2026-05-24
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260524_0013"
down_revision = "20260523_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("result_json", sa.Text(), nullable=False, server_default=""))

    # Indexes for tenant-scoped queries
    op.create_index("ix_campaigns_tenant_id", "campaigns", ["tenant_id"])
    op.create_index("ix_candidates_tenant_campaign", "candidates", ["tenant_id", "campaign_id"])
    op.create_index("ix_policy_documents_tenant_status", "policy_documents", ["tenant_id", "ingest_status"])
    op.create_index("ix_jobs_tenant_created_at", "jobs", ["tenant_id", "created_at"])
    op.create_index("ix_audit_events_tenant_ts", "audit_events", ["tenant_id", "ts"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_tenant_ts", table_name="audit_events")
    op.drop_index("ix_jobs_tenant_created_at", table_name="jobs")
    op.drop_index("ix_policy_documents_tenant_status", table_name="policy_documents")
    op.drop_index("ix_candidates_tenant_campaign", table_name="candidates")
    op.drop_index("ix_campaigns_tenant_id", table_name="campaigns")

    op.drop_column("jobs", "result_json")

