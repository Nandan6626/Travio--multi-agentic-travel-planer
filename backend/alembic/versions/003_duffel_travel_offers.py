"""duffel search records and travel offers schema

Revision ID: 003_duffel_travel_offers
Revises: 002_milestone3_itinerary
Create Date: 2026-11-02 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_duffel_travel_offers'
down_revision: Union[str, None] = '002_milestone3_itinerary'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # 1. Search Records Table
    op.create_table(
        'search_records',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('trip_id', sa.CHAR(36), nullable=True),
        sa.Column('search_type', sa.String(length=50), nullable=False),
        sa.Column('search_parameters', sa.JSON(), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_search_records_trip_id'), 'search_records', ['trip_id'], unique=False)
    op.create_index(op.f('ix_search_records_search_type'), 'search_records', ['search_type'], unique=False)

    # 2. Travel Offers Table
    op.create_table(
        'travel_offers',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('search_record_id', sa.CHAR(36), nullable=True),
        sa.Column('provider_name', sa.String(length=50), nullable=False, server_default='DUFFEL'),
        sa.Column('offer_type', sa.String(length=50), nullable=False),
        sa.Column('provider_offer_id', sa.String(length=255), nullable=False),
        sa.Column('verified_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('offer_details', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['search_record_id'], ['search_records.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_travel_offers_search_record_id'), 'travel_offers', ['search_record_id'], unique=False)
    op.create_index(op.f('ix_travel_offers_provider_offer_id'), 'travel_offers', ['provider_offer_id'], unique=False)
    op.create_index(op.f('ix_travel_offers_offer_type'), 'travel_offers', ['offer_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_travel_offers_offer_type'), table_name='travel_offers')
    op.drop_index(op.f('ix_travel_offers_provider_offer_id'), table_name='travel_offers')
    op.drop_index(op.f('ix_travel_offers_search_record_id'), table_name='travel_offers')
    op.drop_table('travel_offers')

    op.drop_index(op.f('ix_search_records_search_type'), table_name='search_records')
    op.drop_index(op.f('ix_search_records_trip_id'), table_name='search_records')
    op.drop_table('search_records')

