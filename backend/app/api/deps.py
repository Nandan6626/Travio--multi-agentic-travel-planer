import uuid
from typing import Dict, Any, Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user_token_payload, get_current_user_id
from app.models.profile import Profile
from app.models.trip import Trip, TripRole
from app.services.trip_service import TripService


async def get_current_profile(
    payload: Dict[str, Any] = Depends(get_current_user_token_payload),
    db: AsyncSession = Depends(get_db),
) -> Profile:
    """
    Extracts user identity from verified Supabase token and ensures
    a corresponding Profile record exists in PostgreSQL.
    """
    user_id = uuid.UUID(str(payload["sub"]))
    email = payload.get("email") or f"{user_id}@auth.travio.local"
    user_metadata = payload.get("user_metadata") or {}
    full_name = user_metadata.get("full_name") or user_metadata.get("name")
    avatar_url = user_metadata.get("avatar_url") or user_metadata.get("picture")

    profile = await TripService.get_or_create_profile(
        db=db,
        user_id=user_id,
        email=email,
        full_name=full_name,
        avatar_url=avatar_url,
    )
    return profile


def require_trip_role(min_role: TripRole) -> Callable:
    """
    Returns a dependency that validates the requesting user has at least min_role
    on the specified trip_id path parameter.
    """
    async def dependency(
        trip_id: uuid.UUID,
        user_id: uuid.UUID = Depends(get_current_user_id),
        db: AsyncSession = Depends(get_db),
    ) -> Trip:
        trip, _ = await TripService.get_permitted_trip(
            db=db,
            trip_id=trip_id,
            user_id=user_id,
            min_role=min_role,
        )
        return trip

    return dependency
