"""initial milestone2 schema

Revision ID: 001_initial_milestone2
Revises: 
Create Date: 2026-10-29 02:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_milestone2'
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. Profiles Table
    op.create_table(
        'profiles',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_profiles_email'), 'profiles', ['email'], unique=True)

    # 2. Trips Table
    op.create_table(
        'trips',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('owner_id', sa.CHAR(36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('destination', sa.String(length=255), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('total_budget', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('traveler_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PLANNING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_trips_owner_id'), 'trips', ['owner_id'], unique=False)

    # 3. Trip Members Table
    op.create_table(
        'trip_members',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('trip_id', sa.CHAR(36), nullable=False),
        sa.Column('profile_id', sa.CHAR(36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='VIEWER'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'profile_id', name='uq_trip_member')
    )
    op.create_index(op.f('ix_trip_members_profile_id'), 'trip_members', ['profile_id'], unique=False)
    op.create_index(op.f('ix_trip_members_trip_id'), 'trip_members', ['trip_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_trip_members_trip_id'), table_name='trip_members')
    op.drop_index(op.f('ix_trip_members_profile_id'), table_name='trip_members')
    op.drop_table('trip_members')

    op.drop_index(op.f('ix_trips_owner_id'), table_name='trips')
    op.drop_table('trips')

    op.drop_index(op.f('ix_profiles_email'), table_name='profiles')
    op.drop_table('profiles')
