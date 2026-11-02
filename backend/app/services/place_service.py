import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.models.place import Place
from app.schemas.place import PlaceCreate


class PlaceService:
    @staticmethod
    async def create_place(
        db: AsyncSession,
        data: PlaceCreate,
    ) -> Place:
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
        stmt = select(Place).where(Place.id == place_id)
        place = (await db.execute(stmt)).scalar_one_or_none()
        if not place:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found",
            )
        return place

