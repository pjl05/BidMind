"""add analysis tasks and file dedup tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analysis_tasks table
    op.create_table(
        'analysis_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('file_url', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('page_count', sa.Integer, nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('current_agent', sa.String(50), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('token_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('llm_cost', sa.String(20), nullable=False, server_default='0'),
        sa.Column('celery_task_id', sa.String(36), nullable=True),
        sa.Column('revision_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_analysis_tasks_user_id', 'analysis_tasks', ['user_id'])
    op.create_index('ix_analysis_tasks_file_hash', 'analysis_tasks', ['file_hash'])
    op.create_index('ix_analysis_tasks_status', 'analysis_tasks', ['status'])

    # Create file_dedup table
    op.create_table(
        'file_dedup',
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('file_url', sa.String(1000), nullable=False),
        sa.Column('first_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('file_hash')
    )


def downgrade() -> None:
    op.drop_table('file_dedup')
    op.drop_index('ix_analysis_tasks_status', table_name='analysis_tasks')
    op.drop_index('ix_analysis_tasks_file_hash', table_name='analysis_tasks')
    op.drop_index('ix_analysis_tasks_user_id', table_name='analysis_tasks')
    op.drop_table('analysis_tasks')