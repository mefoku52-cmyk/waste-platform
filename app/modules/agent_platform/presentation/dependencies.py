"""Dependency injection for agent_platform presentation layer."""

from __future__ import annotations

import contextlib

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.application.agent.agent_orchestrator import (
    AgentOrchestrator,
)
from app.modules.agent_platform.infrastructure.ai.fallback_gateway import FallbackModelGateway
from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.agent_platform.infrastructure.ai.mistral_gateway import MistralModelGateway
from app.modules.agent_platform.infrastructure.events.sqlalchemy_event_publisher import (
    SqlAlchemyEventPublisher,
)
from app.modules.agent_platform.infrastructure.permission.actor_tool_permission_engine import (
    ActorToolPermissionEngine,
)
from app.modules.agent_platform.infrastructure.persistence.ai_conversation_repository import (
    SqlAlchemyAiConversationRepository,
)
from app.modules.agent_platform.infrastructure.policy.allowlist_policy_engine import (
    AllowlistPolicyEngine,
)
from app.modules.agent_platform.infrastructure.tools.cmep_admin_tools import (
    CmepAdminToolsHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_company_search_handler import (
    CmepCompanySearchHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_listing_search_handler import (
    CmepListingSearchHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_listing_transport_handler import (
    CmepListingTransportHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_nearby_companies_handler import (
    CmepNearbyCompaniesHandler,
)
from app.modules.agent_platform.infrastructure.tools.cmep_user_tools import (
    CmepUserToolsHandler,
)
from app.modules.agent_platform.infrastructure.tools.project_read import (
    ProjectReadHandler,
)
from app.modules.agent_platform.infrastructure.tools.tool_schemas import (
    CLIENT_ACTION_NAMES,
    CLIENT_ACTION_SCHEMAS,
    build_admin_tools,
    build_default_tools,
    build_project_read_tools,
    build_transport_tools,
    build_user_read_tools,
)
from app.modules.companies.application.entitlements import (
    CompanyEntitlementService,
)
from app.modules.companies.application.services import (
    GetCompanyService,
    ListCompaniesService,
)
from app.modules.companies.infrastructure.repositories import (
    SqlAlchemyCompanyRepository,
)
from app.modules.listings.application.services import ListingsService
from app.modules.listings.infrastructure.repositories import (
    ListingsRepositoryImpl,
)
from app.shared.application.side_effects import write_audit
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

    tool_handlers: dict[str, object] = {
        "search_companies": company_handler,
        "search_listings": listing_handler,
    }
    tool_scopes: dict[str, tuple[str, str]] = {
        "search_companies": ("companies", "search"),
        "search_listings": ("listings", "search"),
    }
    tool_schemas: tuple[dict[str, object], ...] = build_default_tools() + CLIENT_ACTION_SCHEMAS

    # Transport + nearby READ tools – pre vsetkych prihlasenych.
    nearby_handler = CmepNearbyCompaniesHandler(session=session)
    transport_handler = CmepListingTransportHandler(session=session)
    tool_handlers["search_nearby_companies"] = nearby_handler
    tool_handlers["get_listing_transport"] = transport_handler
    tool_scopes["search_nearby_companies"] = ("recommendations", "read")
    tool_scopes["get_listing_transport"] = ("recommendations", "read")
    tool_schemas = tool_schemas + build_transport_tools()

    # User READ tools (identity-bound) – pre všetkých prihlásených.
    get_company_service = GetCompanyService(company_repo)
    user_tools_handler = CmepUserToolsHandler(
        session=session,
        listings_service=listings_service,
        get_company_service=get_company_service,
        company_ids=company_ids,
        is_platform_admin=is_admin,
    )
    for _tool_name in (
        "get_my_listings",
        "get_my_company",
        "get_listing_details",
        "get_listing_stats",
        "get_company_listings",
        "get_recommendations",
    ):
        tool_handlers[_tool_name] = user_tools_handler
        tool_scopes[_tool_name] = ("listings", "read")
    tool_schemas = tool_schemas + build_user_read_tools()

    # Project READ tools — IBA pre platform admina (nie pre bežných userov).
    if is_admin:
        project_handler = ProjectReadHandler()
        tool_handlers["project_read_file"] = project_handler
        tool_handlers["project_list_dir"] = project_handler
        tool_scopes["project_read_file"] = ("admin", "read")
        tool_scopes["project_list_dir"] = ("admin", "read")
        tool_schemas = tool_schemas + build_project_read_tools()

    # Admin tools are attached ONLY when the caller is a platform admin.
    if is_admin:
        admin_handler = CmepAdminToolsHandler(session=session)
        for tool_name in (
            "get_platform_stats",
            "get_recent_activity",
            "get_companies_with_tiers",
            "get_my_company_context",
        ):
            tool_handlers[tool_name] = admin_handler
            tool_scopes[tool_name] = ("admin", "read")
        tool_schemas = tool_schemas + build_admin_tools()

    policy = AllowlistPolicyEngine(
        allowed_tool_names=frozenset(tool_handlers.keys()),
    )
    permission = ActorToolPermissionEngine(
        allowed_actor_types=frozenset({"user", "admin"}),
        allowed_scopes=frozenset(tool_scopes.values()),
    )

    async def _audit_agent_tool(
        actor_id: str,
        tool_name: str,
        outcome: str,
        duration_s: float,
    ) -> None:
        # 1. Existujuce: zapis do admin_audit_entries (best-effort).
        with contextlib.suppress(Exception):
            await write_audit(
                session=session,
                actor_user_id=actor_id,
                action=f"agent.tool.{outcome}",
                target_type="agent_tool",
                details=f"tool={tool_name},duration_ms={int(duration_s * 1000)}",
            )

        # 2. Nove: zapis do agent_audit_records cez DefaultAuditService.
        try:
            from datetime import UTC, datetime
            from uuid import uuid4

            from app.modules.agent_platform.application.audit.audit_service import (
                DefaultAuditService,
            )
            from app.modules.agent_platform.domain.audit.audit_action import (
                AuditAction,
            )
            from app.modules.agent_platform.domain.audit.audit_record import (
                AuditRecord,
            )
            from app.modules.agent_platform.domain.audit.audit_subject import (
                AuditSubject,
            )
            from app.modules.agent_platform.infrastructure.audit.audit_store import (
                SqlAlchemyAuditStore,
            )

            action_map = {
                "executed": AuditAction.EXECUTE,
                "failed": AuditAction.EXECUTE,
                "exception": AuditAction.EXECUTE,
                "denied_by_policy": AuditAction.DENY,
                "denied_by_permission": AuditAction.DENY,
                "tool_scope_unmapped": AuditAction.DENY,
                "tool_not_available": AuditAction.DENY,
                "requires_approval_policy": AuditAction.REQUEST,
                "requires_approval_permission": AuditAction.REQUEST,
            }
            audit_action = action_map.get(outcome, AuditAction.EXECUTE)

            record = AuditRecord(
                audit_id=str(uuid4()),
                actor_id=actor_id,
                actor_type="user",
                action=audit_action,
                subject=AuditSubject(subject_type="agent_tool", subject_id=tool_name),
                occurred_at=datetime.now(UTC),
                success=(outcome == "executed"),
                reason=outcome,
                metadata={"duration_ms": int(duration_s * 1000)},
            )
            svc = DefaultAuditService(store=SqlAlchemyAuditStore(session))
            await svc.record(record)
        except Exception:
            pass  # best-effort: never break caller

    return AgentOrchestrator(
        gateway=FallbackModelGateway(
            primary=GroqModelGateway(),
            fallback=MistralModelGateway(),
        ),
        tool_schemas=tool_schemas,
        tool_handlers=tool_handlers,
        policy=policy,
        permission=permission,
        tool_scopes=tool_scopes,
        audit=_audit_agent_tool,
        event_publisher=_build_event_bus(session=session),
        model="openai/gpt-oss-120b",
        client_tool_names=CLIENT_ACTION_NAMES,
    )


async def get_company_entitlement_service(
    session: AsyncSession = Depends(get_db_session),
) -> CompanyEntitlementService:
    """Build a CompanyEntitlementService bound to the request DB session."""
    repo = SqlAlchemyCompanyRepository(session)
    return CompanyEntitlementService(repository=repo)


async def get_ai_conversation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SqlAlchemyAiConversationRepository:
    """Build AI conversation repository bound to request session."""
    return SqlAlchemyAiConversationRepository(session=session)


async def get_control_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.control.control_service import (
        DefaultControlService,
    )
    from app.modules.agent_platform.infrastructure.persistence.control_repository import (
        SqlAlchemyControlRepository,
    )

    return DefaultControlService(repository=SqlAlchemyControlRepository(session))


async def get_alert_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.alerts.alert_service import (
        DefaultAlertService,
    )
    from app.modules.agent_platform.infrastructure.persistence.alert_repository import (
        SqlAlchemyAlertRepository,
    )

    return DefaultAlertService(repository=SqlAlchemyAlertRepository(session))


async def get_approval_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.approval.approval_service import (
        DefaultApprovalService,
    )
    from app.modules.agent_platform.infrastructure.persistence.approval_repository import (
        SqlAlchemyApprovalRepository,
    )

    return DefaultApprovalService(repository=SqlAlchemyApprovalRepository(session))


async def get_approval_workflow(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.approval.approval_workflow import (
        DefaultApprovalWorkflow,
    )
    from app.modules.agent_platform.infrastructure.persistence.approval_repository import (
        SqlAlchemyApprovalRepository,
    )

    return DefaultApprovalWorkflow(repository=SqlAlchemyApprovalRepository(session))


async def get_audit_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.audit.audit_service import (
        DefaultAuditService,
    )
    from app.modules.agent_platform.infrastructure.audit.audit_store import (
        SqlAlchemyAuditStore,
    )

    return DefaultAuditService(store=SqlAlchemyAuditStore(session))


async def get_security_engine():
    from app.modules.agent_platform.application.security.security_engine import (
        DefaultSecurityEngine,
    )

    return DefaultSecurityEngine()


async def get_security_signal_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.security.security_signal_service import (
        DefaultSecuritySignalService,
    )
    from app.modules.agent_platform.infrastructure.security.security_event_store import (
        SqlAlchemySecurityEventStore,
    )

    return DefaultSecuritySignalService(store=SqlAlchemySecurityEventStore(session))


async def get_security_risk_engine():
    from app.modules.agent_platform.application.security.security_risk_engine import (
        DefaultSecurityRiskEngine,
    )

    return DefaultSecurityRiskEngine()


async def get_security_alert_service(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.security.security_alert_service import (
        DefaultSecurityAlertService,
    )

    alert_svc = await get_alert_service(session)
    return DefaultSecurityAlertService(alert_service=alert_svc)


async def get_event_bus(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.application.events.event_bus import (
        DefaultEventBus,
    )

    return DefaultEventBus(publisher=SqlAlchemyEventPublisher(session=session))


async def get_event_dispatcher():
    from app.modules.agent_platform.application.events.event_dispatcher import (
        DefaultEventDispatcher,
    )

    return DefaultEventDispatcher()


async def get_event_store(
    session: AsyncSession = Depends(get_db_session),
):
    from app.modules.agent_platform.infrastructure.events.event_store import (
        SqlAlchemyEventStore,
    )

    return SqlAlchemyEventStore(session)


def _build_event_bus(*, session):
    """Zabal SqlAlchemyEventPublisher do DefaultEventBus."""
    from app.modules.agent_platform.application.events.event_bus import (
        DefaultEventBus,
    )

    return DefaultEventBus(publisher=SqlAlchemyEventPublisher(session=session))
