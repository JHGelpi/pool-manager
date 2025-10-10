"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-01-09 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Chemical Inventory table
    op.create_table(
        'chemical_inventory',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('quantity_on_hand', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(), nullable=False),
        sa.Column('reorder_threshold', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_chemical_inventory_name'), 'chemical_inventory', ['name'])
    
    # Maintenance Tasks table
    op.create_table(
        'maintenance_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency_days', sa.Integer(), nullable=False),
        sa.Column('last_completed_date', sa.Date(), nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=False),
        sa.Column('last_completion_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_maintenance_tasks_next_due_date'), 'maintenance_tasks', ['next_due_date'])
    
    # Alerts table
    op.create_table(
        'alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('cadence', sa.String(), nullable=False),
        sa.Column('days_of_week', sa.String(), nullable=True),
        sa.Column('alert_time', sa.Time(), nullable=False),
        sa.Column('alert_on_low_inventory', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('alert_on_due_tasks', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_sent', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Reading Types table
    op.create_table(
        'reading_types',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('slug', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('low', sa.Float(), nullable=True),
        sa.Column('high', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    )
    op.create_index(op.f('ix_reading_types_slug'), 'reading_types', ['slug'], unique=True)
    
    # Readings table
    op.create_table(
        'readings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reading_type_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reading_value', sa.Float(), nullable=False),
        sa.Column('reading_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reading_type_id'], ['reading_types.id'], ondelete='CASCADE'),
    )
    op.create_index(op.f('ix_readings_reading_date'), 'readings', ['reading_date'])
    
    # Seed default reading types
    op.execute(f"""
        INSERT INTO reading_types (id, slug, name, unit, low, high, is_active) VALUES
        ('{uuid.uuid4()}', 'ph', 'pH', '', 6.8, 8.2, true),
        ('{uuid.uuid4()}', 'fc', 'Free Chlorine', 'ppm', 0, 10, true),
        ('{uuid.uuid4()}', 'cc', 'Combined Chlorine', 'ppm', 0, 1, true),
        ('{uuid.uuid4()}', 'ta', 'Total Alkalinity', 'ppm', 50, 180, true),
        ('{uuid.uuid4()}', 'ch', 'Calcium Hardness', 'ppm', 100, 1000, true),
        ('{uuid.uuid4()}', 'cya', 'Stabilizer (CYA)', 'ppm', 0, 200, true),
        ('{uuid.uuid4()}', 'salt', 'Salt', 'ppm', 0, 6000, true),
        ('{uuid.uuid4()}', 'temp', 'Water Temperature', '°F', 30, 120, true)
    """)
    
    # Create default admin user (admin@example.com / admin123)
    admin_id = uuid.uuid4()
    hashed_password = pwd_context.hash("admin123")
    op.execute(f"""
        INSERT INTO users (id, email, hashed_password, is_active) 
        VALUES ('{admin_id}', 'admin@example.com', '{hashed_password}', true)
    """)


def downgrade() -> None:
    op.drop_index(op.f('ix_readings_reading_date'), table_name='readings')
    op.drop_table('readings')
    op.drop_index(op.f('ix_reading_types_slug'), table_name='reading_types')
    op.drop_table('reading_types')
    op.drop_table('alerts')
    op.drop_index(op.f('ix_maintenance_tasks_next_due_date'), table_name='maintenance_tasks')
    op.drop_table('maintenance_tasks')
    op.drop_index(op.f('ix_chemical_inventory_name'), table_name='chemical_inventory')
    op.drop_table('chemical_inventory')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')