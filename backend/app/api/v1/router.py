from fastapi import APIRouter
from app.api.v1 import health, profiles, trips, days, items, places, routes, weather, offers

api_v1_router = APIRouter()

# Health router
api_v1_router.include_router(health.router, tags=["Health"])

# Milestone 2 routers
api_v1_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_v1_router.include_router(trips.router, prefix="/trips", tags=["Trips"])

# Milestone 3 routers: Itinerary Days, Activities & Places
api_v1_router.include_router(days.router, tags=["Itinerary Days"])
api_v1_router.include_router(items.router, tags=["Itinerary Activities"])
api_v1_router.include_router(places.router, prefix="/places", tags=["Places"])

# Milestone 4 routers: Real Places, Routing, Weather & Travel Offers
api_v1_router.include_router(routes.router, prefix="/routes", tags=["Routing"])
api_v1_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_v1_router.include_router(offers.router, prefix="/offers", tags=["Travel Offers"])
