from fastapi import APIRouter
from app.api.v1 import health, profiles, trips

api_v1_router = APIRouter()

# Health router
api_v1_router.include_router(health.router, tags=["Health"])

# Milestone 2 routers
api_v1_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_v1_router.include_router(trips.router, prefix="/trips", tags=["Trips"])

# Future milestone routers will be mounted here:
# api_v1_router.include_router(itinerary.router, prefix="/trips/{trip_id}/itinerary", tags=["Itinerary"])
# api_v1_router.include_router(places.router, prefix="/places", tags=["Places"])
# api_v1_router.include_router(offers.router, prefix="/offers", tags=["Offers"])
# api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
