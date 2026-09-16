from fastapi import APIRouter

from app.modules.admin.presentation.router import router as admin_router
from app.modules.analytics.presentation.router import router as analytics_router
from app.modules.auth.presentation.router import router as auth_router
from app.modules.chat.presentation.router import router as chat_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import (
    router as memberships_router,
)
from app.modules.compliance.presentation.router import router as compliance_router
from app.modules.documents.presentation.router import router as documents_router
from app.modules.inquiries.presentation.router import router as inquiries_router
from app.modules.listings.presentation.router import router as listings_router
from app.modules.notifications.presentation.router import router as notifications_router
from app.modules.uploads.presentation.router import router as uploads_router
from app.modules.users.presentation.router import router as users_router

api_router = APIRouter()


api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(companies_router)
api_router.include_router(memberships_router)

api_router.include_router(admin_router)
api_router.include_router(analytics_router)
api_router.include_router(compliance_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(inquiries_router)
api_router.include_router(listings_router)
api_router.include_router(notifications_router)
api_router.include_router(uploads_router)
