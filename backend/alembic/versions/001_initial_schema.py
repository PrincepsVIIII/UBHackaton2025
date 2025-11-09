"""Initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-09 03:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('elder', 'volunteer', name='user_role_enum'), nullable=True),
        sa.Column('is_suspended', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create email_otps table
    op.create_table(
        'email_otps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('code_hash', sa.String(length=128), nullable=False),
        sa.Column('role', sa.Enum('elder', 'volunteer', name='email_otp_role_enum'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_email_otps_id'), 'email_otps', ['id'], unique=False)

    # Create elder_profiles table
    op.create_table(
        'elder_profiles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=False),
        sa.Column('mobility_notes', sa.Text(), nullable=True),
        sa.Column('preferred_contact_method', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create volunteer_profiles table
    op.create_table(
        'volunteer_profiles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('radius_miles', sa.Integer(), nullable=False),
        sa.Column('has_vehicle', sa.Boolean(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('completed_events_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create help_requests table
    op.create_table(
        'help_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('elder_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('address_override', sa.String(length=500), nullable=True),
        sa.Column('lat', sa.Float(), nullable=False),
        sa.Column('lng', sa.Float(), nullable=False),
        sa.Column('urgency_level', sa.Enum('low', 'medium', 'high', 'critical', name='urgency_level_enum'), nullable=False),
        sa.Column('weather_factor', sa.Float(), nullable=False, server_default=sa.text('0.0')),
        sa.Column(
            'status',
            sa.Enum(
                'open',
                'assigned',
                'completed_pending_approval',
                'completed',
                'cancelled',
                name='request_status_enum',
            ),
            nullable=False,
            server_default='open',
        ),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('completion_approved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['elder_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_help_requests_elder_id'), 'help_requests', ['elder_id'], unique=False)
    op.create_index(op.f('ix_help_requests_id'), 'help_requests', ['id'], unique=False)
    op.create_index(op.f('ix_help_requests_status'), 'help_requests', ['status'], unique=False)

    # Create assignments table
    op.create_table(
        'assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('volunteer_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['help_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['volunteer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assignments_id'), 'assignments', ['id'], unique=False)
    op.create_index(op.f('ix_assignments_request_id'), 'assignments', ['request_id'], unique=False)
    op.create_index(op.f('ix_assignments_volunteer_id'), 'assignments', ['volunteer_id'], unique=False)

    # Create event_logs table
    op.create_table(
        'event_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['request_id'], ['help_requests.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_logs_id'), 'event_logs', ['id'], unique=False)
    op.create_index(op.f('ix_event_logs_request_id'), 'event_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_event_logs_user_id'), 'event_logs', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_event_logs_user_id'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_request_id'), table_name='event_logs')
    op.drop_index(op.f('ix_event_logs_id'), table_name='event_logs')
    op.drop_table('event_logs')
    op.drop_index(op.f('ix_assignments_volunteer_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_request_id'), table_name='assignments')
    op.drop_index(op.f('ix_assignments_id'), table_name='assignments')
    op.drop_table('assignments')
    op.drop_index(op.f('ix_help_requests_status'), table_name='help_requests')
    op.drop_index(op.f('ix_help_requests_id'), table_name='help_requests')
    op.drop_index(op.f('ix_help_requests_elder_id'), table_name='help_requests')
    op.drop_table('help_requests')
    op.drop_table('volunteer_profiles')
    op.drop_table('elder_profiles')
    op.drop_index(op.f('ix_email_otps_id'), table_name='email_otps')
    op.drop_table('email_otps')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

