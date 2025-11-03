"""reorder readings and update target ranges

Revision ID: 005_reorder_readings_add_ranges
Revises: 004_migrate_existing_completions
Create Date: 2025-11-01 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_reorder_readings_add_ranges'
down_revision: Union[str, None] = '004_migrate_existing_completions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add display_order column
    op.add_column('reading_types', sa.Column('display_order', sa.Integer(), nullable=True))

    # Add new reading types
    op.execute("""
        INSERT INTO reading_types (id, slug, name, unit, low, high, is_active, display_order)
        VALUES
            (gen_random_uuid(), 'th', 'Total Hardness', 'ppm', 250, 500, true, 1),
            (gen_random_uuid(), 'bromine', 'Bromine', 'ppm', 2, 6, true, 3),
            (gen_random_uuid(), 'tc', 'Total Chlorine', 'ppm', 1, 3, true, 4)
        ON CONFLICT (slug) DO NOTHING;
    """)

    # Update existing reading types with new order and ranges
    op.execute("UPDATE reading_types SET display_order = 1, low = 250, high = 500 WHERE slug = 'th'")
    op.execute("UPDATE reading_types SET display_order = 2, low = 1, high = 3 WHERE slug = 'fc'")
    op.execute("UPDATE reading_types SET display_order = 3, low = 2, high = 6 WHERE slug = 'bromine'")
    op.execute("UPDATE reading_types SET display_order = 4, low = 1, high = 3 WHERE slug = 'tc'")
    op.execute("UPDATE reading_types SET display_order = 5, low = 30, high = 100 WHERE slug = 'cya'")
    op.execute("UPDATE reading_types SET display_order = 6, low = 80, high = 120 WHERE slug = 'ta'")
    op.execute("UPDATE reading_types SET display_order = 7, low = 7.2, high = 7.8 WHERE slug = 'ph'")
    op.execute("UPDATE reading_types SET display_order = 8, low = NULL, high = NULL WHERE slug = 'salt'")

    # Mark unused readings as inactive
    op.execute("UPDATE reading_types SET is_active = false, display_order = 99 WHERE slug IN ('cc', 'ch', 'temp')")

    # Create index on display_order
    op.create_index('ix_reading_types_display_order', 'reading_types', ['display_order'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_reading_types_display_order', 'reading_types')

    # Restore old ranges
    op.execute("""
        UPDATE reading_types SET low = 0, high = 10 WHERE slug = 'fc';
        UPDATE reading_types SET low = 0, high = 200 WHERE slug = 'cya';
        UPDATE reading_types SET low = 50, high = 180 WHERE slug = 'ta';
        UPDATE reading_types SET low = 6.8, high = 8.2 WHERE slug = 'ph';
        UPDATE reading_types SET is_active = true WHERE slug IN ('cc', 'ch', 'temp');
    """)

    # Remove new reading types
    op.execute("""
        DELETE FROM reading_types WHERE slug IN ('th', 'bromine', 'tc');
    """)

    # Drop display_order column
    op.drop_column('reading_types', 'display_order')
