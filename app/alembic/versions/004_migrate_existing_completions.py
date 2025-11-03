"""migrate existing completion data to history

Revision ID: 004_migrate_existing_completions
Revises: 003_task_completion_history
Create Date: 2025-11-01 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '004_migrate_existing_completions'
down_revision: Union[str, None] = '003_task_completion_history'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate existing completion data from maintenance_tasks to task_completion_history.

    For each task that has a last_completed_date, create a corresponding history entry.
    This preserves the existing completion information while maintaining the new structure.

    This migration is idempotent - it only inserts records that don't already exist.
    """
    # Use raw SQL to insert existing completion data into history table
    # Only insert if a matching record doesn't already exist (idempotent)
    op.execute("""
        INSERT INTO task_completion_history (id, task_id, completed_date, notes, created_at)
        SELECT
            gen_random_uuid() as id,
            mt.id as task_id,
            mt.last_completed_date as completed_date,
            mt.last_completion_notes as notes,
            (mt.last_completed_date || ' 12:00:00')::timestamp with time zone as created_at
        FROM maintenance_tasks mt
        WHERE mt.last_completed_date IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM task_completion_history tch
            WHERE tch.task_id = mt.id
            AND tch.completed_date = mt.last_completed_date
            AND tch.created_at::date = tch.completed_date
            AND (tch.notes = mt.last_completion_notes
                 OR (tch.notes IS NULL AND mt.last_completion_notes IS NULL))
        )
    """)


def downgrade() -> None:
    """
    Remove the migrated history entries.

    This will delete history entries that were created from the initial migration.
    Since we can't reliably identify which records were migrated vs. manually created,
    this is a best-effort rollback that matches on date and notes.

    Note: If task completion data has changed since migration, some records may not
    be removed during downgrade. This is acceptable as it preserves user data.
    """
    op.execute("""
        DELETE FROM task_completion_history tch
        USING maintenance_tasks mt
        WHERE tch.task_id = mt.id
        AND tch.completed_date = mt.last_completed_date
        AND (tch.notes = mt.last_completion_notes
             OR (tch.notes IS NULL AND mt.last_completion_notes IS NULL))
        AND tch.created_at::date = tch.completed_date
    """)
