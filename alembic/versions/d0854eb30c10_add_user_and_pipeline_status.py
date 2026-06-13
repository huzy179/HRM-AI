"""add_user_and_pipeline_status

Revision ID: d0854eb30c10
Revises: 20260524_0014
Create Date: 2026-06-13 16:27:43.997221

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = 'd0854eb30c10'
down_revision = '20260524_0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=200), nullable=False),
        sa.Column('tenant_id', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    # 2. Add pipeline_status column as nullable first
    op.add_column('candidates', sa.Column('pipeline_status', sa.String(length=50), nullable=True))
    # 3. Populate existing rows with default 'Applied'
    op.execute("UPDATE candidates SET pipeline_status = 'Applied' WHERE pipeline_status IS NULL")
    # 4. Alter column to not null
    op.alter_column('candidates', 'pipeline_status', nullable=False)


def downgrade() -> None:
    op.drop_column('candidates', 'pipeline_status')
    op.drop_table('users')
