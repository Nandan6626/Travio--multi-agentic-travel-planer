import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.models.offer import SearchRecord, TravelOffer
from app.models.trip import Trip, TripRole
from app.providers.travel.duffel_adapter import (
    DuffelAdapter,
    DuffelError,
    DuffelConfigurationError,
    DuffelAuthenticationError,
    DuffelRateLimitError,
    DuffelServiceUnavailableError,
    DuffelValidationError,
)
from app.schemas.offer import (
    FlightSearchRequest,
    FlightSearchResponse,
    HotelSearchRequest,
    HotelSearchResponse,
)
from app.services.trip_service import TripService


class TravelService:
    def __init__(self, adapter: Optional[DuffelAdapter] = None):
        self.adapter = adapter or DuffelAdapter()

    def _translate_provider_error(self, e: DuffelError) -> HTTPException:
        """Translates Duffel adapter exceptions into appropriate FastAPI HTTP status codes."""
        if isinstance(e, DuffelConfigurationError):
            return HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Travel provider configuration error: {e.message}",
            )
        elif isinstance(e, DuffelAuthenticationError):
            return HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Travel provider authentication failed. Please verify provider credentials.",
            )
        elif isinstance(e, DuffelRateLimitError):
            headers = {"Retry-After": str(e.retry_after)} if e.retry_after else None
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=e.message,
                headers=headers,
            )
        elif isinstance(e, DuffelValidationError):
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid search request: {e.message}",
            )
        elif isinstance(e, DuffelServiceUnavailableError):
            return HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Travel provider currently unavailable: {e.message}",
            )
        else:
            return HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Travel provider communication error: {str(e)}",
            )

    async def search_flights(
        self,
        request: FlightSearchRequest,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> FlightSearchResponse:
        """Searches flights via Duffel and optionally logs SearchRecord & TravelOffers to DB."""
        if request.trip_id and user_id and db:
            await TripService.get_permitted_trip(
                db=db, trip_id=request.trip_id, user_id=user_id, min_role=TripRole.VIEWER
            )

        try:
            response = await self.adapter.search_flights(request)
        except DuffelError as e:
            raise self._translate_provider_error(e)

        # Persist search record & offers to database if db session is present
        if db:
            try:
                search_rec = SearchRecord(
                    trip_id=request.trip_id,
                    search_type="FLIGHT",
                    search_parameters=request.model_dump(mode="json"),
                )
                db.add(search_rec)
                await db.flush()

                for offer in response.offers:
                    travel_off = TravelOffer(
                        search_record_id=search_rec.id,
                        provider_name="DUFFEL",
                        offer_type="FLIGHT",
                        provider_offer_id=offer.provider_offer_id,
                        verified_price=offer.price,
                        currency=offer.currency,
                        valid_until=offer.expires_at,
                        offer_details=offer.model_dump(mode="json"),
                    )
                    db.add(travel_off)

                await db.commit()
            except Exception as e:
                logger.warning(f"Could not persist flight search records to database: {e}")
                await db.rollback()

        return response

    async def search_hotels(
        self,
        request: HotelSearchRequest,
        user_id: Optional[uuid.UUID] = None,
        db: Optional[AsyncSession] = None,
    ) -> HotelSearchResponse:
        """Searches hotels via Duffel and optionally logs SearchRecord & TravelOffers to DB."""
        if request.trip_id and user_id and db:
            await TripService.get_permitted_trip(
                db=db, trip_id=request.trip_id, user_id=user_id, min_role=TripRole.VIEWER
            )

        try:
            response = await self.adapter.search_hotels(request)
        except DuffelError as e:
            raise self._translate_provider_error(e)

        if db:
            try:
                search_rec = SearchRecord(
                    trip_id=request.trip_id,
                    search_type="HOTEL",
                    search_parameters=request.model_dump(mode="json"),
                )
                db.add(search_rec)
                await db.flush()

                for offer in response.offers:
                    travel_off = TravelOffer(
                        search_record_id=search_rec.id,
                        provider_name="DUFFEL",
                        offer_type="HOTEL",
                        provider_offer_id=offer.provider_offer_id,
                        verified_price=offer.price,
                        currency=offer.currency,
                        valid_until=offer.expires_at,
                        offer_details=offer.model_dump(mode="json"),
                    )
                    db.add(travel_off)

                await db.commit()
            except Exception as e:
                logger.warning(f"Could not persist hotel search records to database: {e}")
                await db.rollback()

        return response

    async def get_stored_offer(
        self,
        offer_id: uuid.UUID,
        db: AsyncSession,
    ) -> TravelOffer:
        """Retrieves stored travel offer and checks price validity timestamp."""
        stmt = select(TravelOffer).where(TravelOffer.id == offer_id)
        res = await db.execute(stmt)
        offer = res.scalar_one_or_none()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Travel offer {offer_id} not found.",
            )
        return offer

