"""policy chat admin tables

Revision ID: 20260713_0015
Revises: d0854eb30c10
Create Date: 2026-07-13 00:00:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_0015"
down_revision = "d0854eb30c10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    policy_columns = {col["name"] for col in inspector.get_columns("policy_documents")} if "policy_documents" in tables else set()
    if "category" not in policy_columns:
        op.add_column("policy_documents", sa.Column("category", sa.String(length=100), nullable=True))
    if "visibility" not in policy_columns:
        op.add_column("policy_documents", sa.Column("visibility", sa.String(length=50), nullable=True))
    if "version" not in policy_columns:
        op.add_column("policy_documents", sa.Column("version", sa.String(length=50), nullable=True))
    if "status" not in policy_columns:
        op.add_column("policy_documents", sa.Column("status", sa.String(length=50), nullable=True))
    if "effective_date" not in policy_columns:
        op.add_column("policy_documents", sa.Column("effective_date", sa.DateTime(), nullable=True))

    op.execute("UPDATE policy_documents SET category = 'general' WHERE category IS NULL")
    op.execute("UPDATE policy_documents SET visibility = 'employee' WHERE visibility IS NULL")
    op.execute("UPDATE policy_documents SET version = '1.0' WHERE version IS NULL")
    op.execute("UPDATE policy_documents SET status = 'published' WHERE status IS NULL AND ingest_status = 'OK'")
    op.execute("UPDATE policy_documents SET status = 'draft' WHERE status IS NULL")

    op.alter_column("policy_documents", "category", nullable=False)
    op.alter_column("policy_documents", "visibility", nullable=False)
    op.alter_column("policy_documents", "version", nullable=False)
    op.alter_column("policy_documents", "status", nullable=False)

    if "chat_sessions" not in tables:
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(length=50), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("channel", sa.String(length=50), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_chat_sessions_tenant_channel", "chat_sessions", ["tenant_id", "channel"])

    if "chat_messages" not in tables:
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("session_id", sa.Integer(), nullable=False),
            sa.Column("tenant_id", sa.String(length=50), nullable=False),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("citations_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_chat_messages_session", "chat_messages", ["session_id", "created_at"])

    if "chat_feedback" not in tables:
        op.create_table(
            "chat_feedback",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("tenant_id", sa.String(length=50), nullable=False),
            sa.Column("message_id", sa.Integer(), nullable=True),
            sa.Column("query", sa.Text(), nullable=False),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("rating", sa.String(length=20), nullable=False),
            sa.Column("comment", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["message_id"], ["chat_messages.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_chat_feedback_tenant_rating", "chat_feedback", ["tenant_id", "rating"])


def downgrade() -> None:
    op.drop_index("ix_chat_feedback_tenant_rating", table_name="chat_feedback")
    op.drop_table("chat_feedback")
    op.drop_index("ix_chat_messages_session", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_tenant_channel", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_column("policy_documents", "effective_date")
    op.drop_column("policy_documents", "status")
    op.drop_column("policy_documents", "version")
    op.drop_column("policy_documents", "visibility")
    op.drop_column("policy_documents", "category")
