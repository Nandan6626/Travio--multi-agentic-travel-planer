import uuid
from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user_id
from app.schemas.offer import (
    FlightSearchRequest,
    FlightSearchResponse,
    HotelSearchRequest,
    HotelSearchResponse,
)
from app.services.travel_service import TravelService

router = APIRouter()
travel_service = TravelService()


@router.post(
    "/flights/search",
    response_model=FlightSearchResponse,
    summary="Search flights via Duffel API",
    description="Fetches live flight offers from Duffel Flights API. Never generates simulated or fake prices.",
)
async def search_flights(
    request: FlightSearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> FlightSearchResponse:
    return await travel_service.search_flights(request=request, user_id=user_id, db=db)


@router.post(
    "/hotels/search",
    response_model=HotelSearchResponse,
    summary="Search hotels and stays via Duffel API",
    description="Fetches live accommodation and room rates from Duffel Stays API with exact provider pricing.",
)
async def search_hotels(
    request: HotelSearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HotelSearchResponse:
    return await travel_service.search_hotels(request=request, user_id=user_id, db=db)


@router.get(
    "/{offer_id}",
    summary="Retrieve verified travel offer details",
    description="Retrieves a stored travel offer by UUID and reports validity status.",
)
async def get_offer(
    offer_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    offer = await travel_service.get_stored_offer(offer_id=offer_id, db=db)
    is_expired = False
    if offer.valid_until:
        from datetime import datetime, timezone
        valid_until = offer.valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)
        is_expired = datetime.now(timezone.utc) > valid_until

    return {
        "id": str(offer.id),
        "provider_name": offer.provider_name,
        "offer_type": offer.offer_type,
        "provider_offer_id": offer.provider_offer_id,
        "verified_price": str(offer.verified_price),
        "currency": offer.currency,
        "valid_until": offer.valid_until.isoformat() if offer.valid_until else None,
        "is_expired": is_expired,
        "is_provider_verified": True,
        "offer_details": offer.offer_details,
        "created_at": offer.created_at.isoformat() if offer.created_at else None,
    }
