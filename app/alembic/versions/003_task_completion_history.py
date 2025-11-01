"""add task completion history

Revision ID: 003_task_completion_history
Revises: 002_unique_task_names
Create Date: 2025-11-01 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '003_task_completion_history'
down_revision: Union[str, None] = '002_unique_task_names'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create task_completion_history table
    op.create_table(
        'task_completion_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('maintenance_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('completed_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create index on task_id for faster queries
    op.create_index('ix_task_completion_history_task_id', 'task_completion_history', ['task_id'])

    # Create index on completed_date for sorting
    op.create_index('ix_task_completion_history_completed_date', 'task_completion_history', ['completed_date'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('ix_task_completion_history_completed_date', 'task_completion_history')
    op.drop_index('ix_task_completion_history_task_id', 'task_completion_history')

    # Drop table
    op.drop_table('task_completion_history')
