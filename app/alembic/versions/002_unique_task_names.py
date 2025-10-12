"""unique task names per user

Revision ID: 002_unique_task_names
Revises: 001_initial
Create Date: 2025-01-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_unique_task_names'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unique constraint on (user_id, name) combination
    # This ensures each user can't have duplicate task names
    op.create_unique_constraint(
        'uq_maintenance_tasks_user_name',
        'maintenance_tasks',
        ['user_id', 'name']
    )


def downgrade() -> None:
    # Remove the unique constraint
    op.drop_constraint(
        'uq_maintenance_tasks_user_name',
        'maintenance_tasks',
        type_='unique'
    )