"""add company profiles table

Revision ID: 004
Revises: 003
Create Date: 2026-05-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'company_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=True),
        sa.Column('qualification_types', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('established_years', sa.Integer(), nullable=True),
        sa.Column('has_similar_projects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('similar_project_desc', sa.Text(), nullable=True),
        sa.Column('annual_revenue', sa.String(50), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('extra_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('company_profiles')