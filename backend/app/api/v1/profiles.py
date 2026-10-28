from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_profile, get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileRead, ProfileSync
from app.services.trip_service import TripService

router = APIRouter()


@router.get(
    "/me",
    response_model=ProfileRead,
    summary="Get current user profile",
    description="Returns the profile matching the verified Supabase JWT subject.",
)
async def get_my_profile(
    current_profile: Profile = Depends(get_current_profile),
) -> ProfileRead:
    return ProfileRead.model_validate(current_profile)


@router.post(
    "/me",
    response_model=ProfileRead,
    summary="Create or synchronize user profile",
    description="Safely synchronizes full name and avatar URL for the authenticated user.",
)
async def sync_my_profile(
    data: ProfileSync,
    current_profile: Profile = Depends(get_current_profile),
    db: AsyncSession = Depends(get_db),
) -> ProfileRead:
    updated = await TripService.get_or_create_profile(
        db=db,
        user_id=current_profile.id,
        email=current_profile.email,
        full_name=data.full_name,
        avatar_url=data.avatar_url,
    )
    return ProfileRead.model_validate(updated)
