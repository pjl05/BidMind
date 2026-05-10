"""add analysis result columns

Revision ID: 003
Revises: 002
Create Date: 2026-05-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('analysis_tasks', sa.Column('final_report', sa.Text(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('requirements', sa.JSON(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('scoring_criteria', sa.JSON(), nullable=True))
    op.add_column('analysis_tasks', sa.Column('bid_strategy', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('analysis_tasks', 'bid_strategy')
    op.drop_column('analysis_tasks', 'scoring_criteria')
    op.drop_column('analysis_tasks', 'requirements')
    op.drop_column('analysis_tasks', 'final_report')