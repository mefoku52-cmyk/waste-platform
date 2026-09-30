"""Abstraktné kontrakty agent_platform.

Pre kazdu ABC overime:
  - neda sa instancovat
  - abstraktne metody raise-uju NotImplementedError
  - Default* implementacia existuje a je instancovatelna
"""

import inspect

# ─── Control ───────────────────────────────────────────────────


def test_control_service_is_abc():
    from app.modules.agent_platform.application.control.control_service import (
        ControlService,
    )

    assert inspect.isabstract(ControlService)


def test_default_control_service_exists():
    from app.modules.agent_platform.application.control.control_service import (
        DefaultControlService,
    )

    assert DefaultControlService is not None
    assert not inspect.isabstract(DefaultControlService)


def test_emergency_service_is_abc():
    from app.modules.agent_platform.application.control.emergency_service import (
        EmergencyService,
    )

    assert inspect.isabstract(EmergencyService)


def test_default_emergency_service_exists():
    from app.modules.agent_platform.application.control.emergency_service import (
        DefaultEmergencyService,
    )

    assert not inspect.isabstract(DefaultEmergencyService)


def test_break_glass_service_is_abc():
    from app.modules.agent_platform.application.control.break_glass_service import (
        BreakGlassService,
    )

    assert inspect.isabstract(BreakGlassService)


def test_default_break_glass_service_exists():
    from app.modules.agent_platform.application.control.break_glass_service import (
        DefaultBreakGlassService,
    )

    assert not inspect.isabstract(DefaultBreakGlassService)


# ─── Security ──────────────────────────────────────────────────


def test_security_engine_is_abc():
    from app.modules.agent_platform.application.security.security_engine import (
        SecurityEngine,
    )

    assert inspect.isabstract(SecurityEngine)


def test_default_security_engine_instantiates():
    from app.modules.agent_platform.application.security.security_engine import (
        DefaultSecurityEngine,
    )

    engine = DefaultSecurityEngine()
    assert engine is not None


def test_security_risk_engine_is_abc():
    from app.modules.agent_platform.application.security.security_risk_engine import (
        SecurityRiskEngine,
    )

    assert inspect.isabstract(SecurityRiskEngine)


def test_default_security_risk_engine_exists():
    from app.modules.agent_platform.application.security.security_risk_engine import (
        DefaultSecurityRiskEngine,
    )

    assert not inspect.isabstract(DefaultSecurityRiskEngine)


def test_security_signal_service_is_abc():
    from app.modules.agent_platform.application.security.security_signal_service import (
        SecuritySignalService,
    )

    assert inspect.isabstract(SecuritySignalService)


def test_default_security_signal_service_exists():
    from app.modules.agent_platform.application.security.security_signal_service import (
        DefaultSecuritySignalService,
    )

    assert not inspect.isabstract(DefaultSecuritySignalService)


def test_security_alert_service_is_abc():
    from app.modules.agent_platform.application.security.security_alert_service import (
        SecurityAlertService,
    )

    assert inspect.isabstract(SecurityAlertService)


def test_default_security_alert_service_exists():
    from app.modules.agent_platform.application.security.security_alert_service import (
        DefaultSecurityAlertService,
    )

    assert not inspect.isabstract(DefaultSecurityAlertService)


# ─── Policy ────────────────────────────────────────────────────


def test_policy_engine_is_abc():
    from app.modules.agent_platform.application.policy.policy_engine import (
        PolicyEngine,
    )

    assert inspect.isabstract(PolicyEngine)


def test_policy_evaluator_is_abc():
    from app.modules.agent_platform.application.policy.policy_evaluator import (
        PolicyEvaluator,
    )

    assert inspect.isabstract(PolicyEvaluator)


# ─── Permission ────────────────────────────────────────────────


def test_permission_engine_is_abc():
    from app.modules.agent_platform.application.permission.permission_engine import (
        PermissionEngine,
    )

    assert inspect.isabstract(PermissionEngine)


def test_permission_resolver_is_abc():
    from app.modules.agent_platform.application.permission.permission_resolver import (
        PermissionResolver,
    )

    assert inspect.isabstract(PermissionResolver)


# ─── Approval ──────────────────────────────────────────────────


def test_approval_service_is_abc():
    from app.modules.agent_platform.application.approval.approval_service import (
        ApprovalService,
    )

    assert inspect.isabstract(ApprovalService)


def test_default_approval_service_exists():
    from app.modules.agent_platform.application.approval.approval_service import (
        DefaultApprovalService,
    )

    assert not inspect.isabstract(DefaultApprovalService)


def test_approval_workflow_is_abc():
    from app.modules.agent_platform.application.approval.approval_workflow import (
        ApprovalWorkflow,
    )

    assert inspect.isabstract(ApprovalWorkflow)


def test_default_approval_workflow_exists():
    from app.modules.agent_platform.application.approval.approval_workflow import (
        DefaultApprovalWorkflow,
    )

    assert not inspect.isabstract(DefaultApprovalWorkflow)


# ─── Tools ─────────────────────────────────────────────────────


def test_tool_registry_is_abc():
    from app.modules.agent_platform.application.tools.tool_registry import (
        ToolRegistry,
    )

    assert inspect.isabstract(ToolRegistry)


def test_tool_dispatcher_is_abc():
    from app.modules.agent_platform.application.tools.tool_dispatcher import (
        ToolDispatcher,
    )

    assert inspect.isabstract(ToolDispatcher)


def test_tool_guard_is_abc():
    from app.modules.agent_platform.application.tools.tool_guard import (
        ToolGuard,
    )

    assert inspect.isabstract(ToolGuard)


def test_tool_executor_is_abc():
    from app.modules.agent_platform.application.tools.tool_executor import (
        ToolExecutor,
    )

    assert inspect.isabstract(ToolExecutor)


def test_tool_handler_is_abc():
    from app.modules.agent_platform.application.tools.tool_handler import (
        ToolHandler,
    )

    assert inspect.isabstract(ToolHandler)


def test_tool_handler_registry_is_abc():
    from app.modules.agent_platform.application.tools.tool_handler_registry import (
        ToolHandlerRegistry,
    )

    assert inspect.isabstract(ToolHandlerRegistry)


# ─── Events ────────────────────────────────────────────────────


def test_event_bus_is_abc():
    from app.modules.agent_platform.application.events.event_bus import (
        EventBus,
    )

    assert inspect.isabstract(EventBus)


def test_default_event_bus_exists():
    from app.modules.agent_platform.application.events.event_bus import (
        DefaultEventBus,
    )

    assert not inspect.isabstract(DefaultEventBus)


def test_event_dispatcher_is_abc():
    from app.modules.agent_platform.application.events.event_dispatcher import (
        EventDispatcher,
    )

    assert inspect.isabstract(EventDispatcher)


def test_default_event_dispatcher_exists():
    from app.modules.agent_platform.application.events.event_dispatcher import (
        DefaultEventDispatcher,
    )

    assert not inspect.isabstract(DefaultEventDispatcher)


def test_event_processor_is_abc():
    from app.modules.agent_platform.application.events.event_processor import (
        EventProcessor,
    )

    assert inspect.isabstract(EventProcessor)


def test_default_event_processor_exists():
    from app.modules.agent_platform.application.events.event_processor import (
        DefaultEventProcessor,
    )

    assert not inspect.isabstract(DefaultEventProcessor)


# ─── Alerts ────────────────────────────────────────────────────


def test_alert_service_is_abc():
    from app.modules.agent_platform.application.alerts.alert_service import (
        AlertService,
    )

    assert inspect.isabstract(AlertService)


def test_default_alert_service_exists():
    from app.modules.agent_platform.application.alerts.alert_service import (
        DefaultAlertService,
    )

    assert not inspect.isabstract(DefaultAlertService)


# ─── Audit ─────────────────────────────────────────────────────


def test_audit_service_is_abc():
    from app.modules.agent_platform.application.audit.audit_service import (
        AuditService,
    )

    assert inspect.isabstract(AuditService)


def test_default_audit_service_exists():
    from app.modules.agent_platform.application.audit.audit_service import (
        DefaultAuditService,
    )

    assert not inspect.isabstract(DefaultAuditService)


# ─── Infrastructure ABCs ───────────────────────────────────────


def test_model_gateway_is_abc():
    from app.modules.agent_platform.infrastructure.ai.model_gateway import (
        ModelGateway,
    )

    assert inspect.isabstract(ModelGateway)


def test_event_store_is_abc():
    from app.modules.agent_platform.infrastructure.events.event_store import (
        EventStore,
    )

    assert inspect.isabstract(EventStore)


def test_security_event_store_is_abc():
    from app.modules.agent_platform.infrastructure.security.security_event_store import (
        SecurityEventStore,
    )

    assert inspect.isabstract(SecurityEventStore)


def test_audit_store_is_abc():
    from app.modules.agent_platform.infrastructure.audit.audit_store import (
        AuditStore,
    )

    assert inspect.isabstract(AuditStore)


def test_agent_repository_is_abc():
    from app.modules.agent_platform.infrastructure.persistence.agent_repository import (
        AgentRepository,
    )

    assert inspect.isabstract(AgentRepository)


def test_alert_repository_is_abc():
    from app.modules.agent_platform.infrastructure.persistence.alert_repository import (
        AlertRepository,
    )

    assert inspect.isabstract(AlertRepository)


def test_approval_repository_is_abc():
    from app.modules.agent_platform.infrastructure.persistence.approval_repository import (
        ApprovalRepository,
    )

    assert inspect.isabstract(ApprovalRepository)


def test_control_repository_is_abc():
    from app.modules.agent_platform.infrastructure.persistence.control_repository import (
        ControlRepository,
    )

    assert inspect.isabstract(ControlRepository)


def test_ai_conversation_repository_is_abc():
    from app.modules.agent_platform.infrastructure.persistence.ai_conversation_repository import (
        AiConversationRepository,
    )

    assert inspect.isabstract(AiConversationRepository)


# ─── Pipelines / Memory ────────────────────────────────────────


def test_agent_pipeline_exists():
    from app.modules.agent_platform.application.pipeline.agent_pipeline import (
        AgentPipeline,
    )

    assert AgentPipeline is not None


def test_pipeline_ports_are_protocols():
    from typing import Protocol

    from app.modules.agent_platform.application.pipeline.pipeline_ports import (
        ApprovalPort,
        AuditPort,
        EventPort,
        ModelProposalPort,
        PermissionPort,
        PolicyPort,
        ToolPort,
    )

    for cls in [
        ModelProposalPort,
        PolicyPort,
        PermissionPort,
        ApprovalPort,
        ToolPort,
        AuditPort,
        EventPort,
    ]:
        assert issubclass(cls, Protocol), f"{cls.__name__} is not Protocol"


def test_build_history_function_exists():
    from app.modules.agent_platform.application.memory.context_builder import (
        build_history,
    )

    assert callable(build_history)


def test_build_history_empty():
    from app.modules.agent_platform.application.memory.context_builder import (
        build_history,
    )

    result = build_history([])
    assert isinstance(result, tuple)
    assert len(result) == 0


def test_agent_context_exists():
    from app.modules.agent_platform.application.agent.agent_context import (
        AgentContext,
    )

    assert AgentContext is not None


def test_agent_response_exists():
    from app.modules.agent_platform.application.agent.agent_response import (
        AgentResponse,
    )

    assert AgentResponse is not None


# ─── Prediction (domain contracts) ─────────────────────────────


def test_prediction_provider_is_abc():
    from app.modules.prediction.domain.provider import PredictionProvider

    assert inspect.isabstract(PredictionProvider)


def test_prediction_entitlement_provider_is_abc():
    from app.modules.prediction.domain.entitlement import (
        PredictionEntitlementProvider,
    )

    assert inspect.isabstract(PredictionEntitlementProvider)


def test_prediction_feature_extractor_is_abc():
    from app.modules.prediction.domain.extractor import FeatureExtractor

    assert inspect.isabstract(FeatureExtractor)
