"""milestone3 itinerary and places schema

Revision ID: 002_milestone3_itinerary
Revises: 001_initial_milestone2
Create Date: 2026-11-01 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_milestone3_itinerary'
down_revision: Union[str, None] = '001_initial_milestone2'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. Places Table
    op.create_table(
        'places',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('provider_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='attraction'),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('opening_hours', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_places_provider_id'), 'places', ['provider_id'], unique=False)

    # 2. Itinerary Days Table
    op.create_table(
        'itinerary_days',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('trip_id', sa.CHAR(36), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('trip_id', 'day_number', name='uq_trip_day_number'),
    )
    op.create_index(op.f('ix_itinerary_days_trip_id'), 'itinerary_days', ['trip_id'], unique=False)

    # 3. Itinerary Items Table
    op.create_table(
        'itinerary_items',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('day_id', sa.CHAR(36), nullable=False),
        sa.Column('place_id', sa.CHAR(36), nullable=True),
        sa.Column('activity_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False, server_default='sightseeing'),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('estimated_cost', sa.Numeric(precision=12, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['day_id'], ['itinerary_days.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['place_id'], ['places.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('day_id', 'order_index', name='uq_day_item_order'),
    )
    op.create_index(op.f('ix_itinerary_items_day_id'), 'itinerary_items', ['day_id'], unique=False)
    op.create_index(op.f('ix_itinerary_items_place_id'), 'itinerary_items', ['place_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_itinerary_items_place_id'), table_name='itinerary_items')
    op.drop_index(op.f('ix_itinerary_items_day_id'), table_name='itinerary_items')
    op.drop_table('itinerary_items')

    op.drop_index(op.f('ix_itinerary_days_trip_id'), table_name='itinerary_days')
    op.drop_table('itinerary_days')

    op.drop_index(op.f('ix_places_provider_id'), table_name='places')
    op.drop_table('places')

