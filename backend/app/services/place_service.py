import uuid
from typing import Optional, List, Union
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.place import Place
from app.schemas.place import (
    PlaceCreate,
    PlaceSearchResult,
    DestinationSearchResult,
)
from app.providers.places.geoapify_adapter import (
    GeoapifyAdapter,
    GeoapifyAuthenticationError,
    GeoapifyRateLimitError,
    GeoapifyServiceUnavailableError,
    GeoapifyValidationError,
)
from app.core.logging import logger


class PlaceService:
    def __init__(self, adapter: Optional[GeoapifyAdapter] = None):
        self.adapter = adapter or GeoapifyAdapter()

    @staticmethod
    async def create_place(
        db: AsyncSession,
        data: PlaceCreate,
    ) -> Place:
        """Manually creates a place record in the database."""
        # Check if already exists by provider_id
        if data.provider_id:
            stmt = select(Place).where(Place.provider_id == data.provider_id)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                return existing

        place = Place(
            name=data.name,
            provider_id=data.provider_id,
            address=data.address,
            latitude=data.latitude,
            longitude=data.longitude,
            category=data.category,
            rating=data.rating,
            opening_hours=data.opening_hours,
        )
        db.add(place)
        await db.commit()
        await db.refresh(place)
        return place

    @staticmethod
    async def get_place(
        db: AsyncSession,
        place_id: uuid.UUID,
    ) -> Place:
        """Retrieves a cached Place by its internal UUID."""
        stmt = select(Place).where(Place.id == place_id)
        place = (await db.execute(stmt)).scalar_one_or_none()
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Place with id '{place_id}' not found.",
            )
        return place

    async def search_places(
        self,
        db: AsyncSession,
        text: Optional[str] = None,
        categories: str = "tourism.attraction,catering.restaurant,entertainment,leisure",
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_meters: int = 5000,
        limit: int = 20,
    ) -> List[PlaceSearchResult]:
        """Searches places via Geoapify, geocoding `text` if coordinates are not provided directly."""
        try:
            # If coordinates are missing but search text is supplied, geocode text first
            search_lat = lat
            search_lon = lon
            place_name_filter = None

            if search_lat is None or search_lon is None:
                if not text or not text.strip():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Either (lat, lon) coordinates or a 'text' destination must be provided for place search.",
                    )
                destinations = await self.adapter.search_destination(query=text.strip(), limit=1)
                if not destinations:
                    return []
                search_lat = destinations[0].latitude
                search_lon = destinations[0].longitude
            else:
                place_name_filter = text.strip() if text else None

            # Fetch POIs from Geoapify
            raw_places = await self.adapter.search_places(
                lat=search_lat,
                lon=search_lon,
                categories=categories,
                radius_meters=radius_meters,
                limit=limit,
                name=place_name_filter,
            )

            if not raw_places:
                return []

            # Check database for existing cached places by provider_id
            provider_ids = [p.provider_id for p in raw_places if p.provider_id]
            cached_map = {}
            if provider_ids:
                stmt = select(Place).where(Place.provider_id.in_(provider_ids))
                cached_records = (await db.execute(stmt)).scalars().all()
                for rec in cached_records:
                    if rec.provider_id:
                        cached_map[rec.provider_id] = rec.id

            for p in raw_places:
                if p.provider_id in cached_map:
                    p.is_cached = True
                    p.cached_place_id = cached_map[p.provider_id]

            return raw_places

        except GeoapifyAuthenticationError as e:
            logger.error(f"Geoapify authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Places provider configuration error: {e}",
            )
        except GeoapifyRateLimitError as e:
            logger.warning(f"Geoapify rate limit error: {e}")
            headers = {"Retry-After": str(e.retry_after)} if e.retry_after else {}
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
                headers=headers,
            )
        except GeoapifyValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
        except GeoapifyServiceUnavailableError as e:
            logger.error(f"Geoapify service unavailable: {e}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    async def get_or_cache_place(
        self,
        db: AsyncSession,
        identifier: str,
    ) -> Place:
        """Retrieves a place either by UUID from the database or fetches and caches it via provider_id."""
        # Check if identifier is a UUID
        try:
            place_uuid = uuid.UUID(identifier)
            stmt = select(Place).where(Place.id == place_uuid)
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                return existing
        except ValueError:
            pass

        # Check by provider_id in DB
        stmt = select(Place).where(Place.provider_id == identifier)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # Fetch from Geoapify
        try:
            place_data = await self.adapter.get_place_details(identifier)
            if not place_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Place '{identifier}' not found in database or external provider.",
                )

            new_place = Place(
                provider_id=place_data.provider_id,
                name=place_data.name,
                address=place_data.address,
                latitude=place_data.latitude,
                longitude=place_data.longitude,
                category=place_data.category,
                rating=place_data.rating,
                opening_hours=place_data.opening_hours,
            )
            db.add(new_place)
            await db.commit()
            await db.refresh(new_place)
            return new_place

        except GeoapifyError as e:
            logger.error(f"Failed to fetch place details from Geoapify: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not retrieve place from external provider: {e}",
            )
