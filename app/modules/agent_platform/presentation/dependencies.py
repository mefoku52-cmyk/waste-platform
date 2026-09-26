"""Dependency injection for agent_platform presentation layer."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.tools.cmep_company_search_handler import (
    CmepCompanySearchHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_listing_search_handler import (
    CmepListingSearchHandler,
)
from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    build_default_tools,
)
from app.modules.companies.application.services import ListCompaniesService
from app.modules.companies.infrastructure.repositories import (
    SqlAlchemyCompanyRepository,
)
from app.modules.listings.application.services import ListingsService
from app.modules.listings.infrastructure.repositories import (
    ListingsRepositoryImpl,
)
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    is_platform_admin,
    membership_company_ids,
)


async def get_agent_orchestrator(
    session: AsyncSession = Depends(get_db_session),
    current_user=Depends(require_current_user),
) -> AgentOrchestrator:
    """Build orchestrator with tool handlers bound to current user's scope."""

    company_repo = SqlAlchemyCompanyRepository(session)
    list_companies_service = ListCompaniesService(company_repo)

    listings_service = ListingsService(ListingsRepositoryImpl(session))

    try:
        company_ids: tuple[str, ...] = tuple(
            str(x) for x in (membership_company_ids(current_user) or [])
        )
        is_admin: bool = bool(is_platform_admin(current_user))
    except Exception:
        company_ids = ()
        is_admin = False

    company_handler = CmepCompanySearchHandler(
        service=list_companies_service,
        is_platform_admin=is_admin,
        company_ids=company_ids,
    )
    listing_handler = CmepListingSearchHandler(service=listings_service)

    return AgentOrchestrator(
        gateway=GroqModelGateway(),
        tool_schemas=build_default_tools(),
        tool_handlers={
            "search_companies": company_handler,
            "search_listings": listing_handler,
        },
        model="openai/gpt-oss-120b",
    )
