"""API v1 router."""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    companies,
    listings,
    users,
    health,
    websocket,
)

api_router = APIRouter()

# Inklúzia routerov
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(listings.router, prefix="/listings", tags=["listings"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
