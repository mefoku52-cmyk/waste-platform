from fastapi import APIRouter

from app.modules.admin.presentation.router import router as admin_router
from app.modules.agent_platform.presentation.chat_router import router as agent_platform_chat_router
from app.modules.agent_platform.presentation.control_router import (
    router as agent_platform_control_router,
)
from app.modules.agent_platform.presentation.router import router as agent_platform_router
from app.modules.analytics.presentation.router import router as analytics_router
from app.modules.auth.presentation.router import router as auth_router
from app.modules.chat.presentation.router import router as chat_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import (
    router as memberships_router,
)
from app.modules.compliance.presentation.router import router as compliance_router
from app.modules.documents.presentation.router import router as documents_router
from app.modules.events.presentation.router import router as events_router
from app.modules.inquiries.presentation.router import router as inquiries_router
from app.modules.lead_finder.presentation.router import (
    router as lead_finder_router,
)
from app.modules.listings.presentation.router import router as listings_router
from app.modules.notifications.presentation.router import router as notifications_router
from app.modules.recommendations.presentation.router import router as recommendations_router
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
api_router.include_router(recommendations_router)
api_router.include_router(events_router)
api_router.include_router(agent_platform_router)
api_router.include_router(lead_finder_router)
api_router.include_router(agent_platform_control_router)
api_router.include_router(agent_platform_chat_router)

# Agent Platform governance routers (security / approvals / alerts / audit)
from app.modules.agent_platform.presentation.alerts_router import (
    router as agent_platform_alerts_router,
)
from app.modules.agent_platform.presentation.approvals_router import (
    router as agent_platform_approvals_router,
)
from app.modules.agent_platform.presentation.audit_router import (
    router as agent_platform_audit_router,
)
from app.modules.agent_platform.presentation.security_router import (
    router as agent_platform_security_router,
)

api_router.include_router(agent_platform_security_router)
api_router.include_router(agent_platform_approvals_router)
api_router.include_router(agent_platform_alerts_router)
api_router.include_router(agent_platform_audit_router)
