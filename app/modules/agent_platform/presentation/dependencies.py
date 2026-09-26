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


async def get_agent_orchestrator(
    session: AsyncSession = Depends(get_db_session),
) -> AgentOrchestrator:
    """Build orchestrator with real tool handlers bound to DB services."""

    company_repo = SqlAlchemyCompanyRepository(session)
    list_companies_service = ListCompaniesService(company_repo)

    listings_service = ListingsService(ListingsRepositoryImpl(session))

    company_handler = CmepCompanySearchHandler(
        service=list_companies_service,
        is_platform_admin=False,
        company_ids=(),
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
