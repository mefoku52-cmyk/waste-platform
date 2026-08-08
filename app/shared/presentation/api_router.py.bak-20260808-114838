from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.users.presentation.router import router as users_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import router as memberships_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(companies_router)
api_router.include_router(memberships_router)
