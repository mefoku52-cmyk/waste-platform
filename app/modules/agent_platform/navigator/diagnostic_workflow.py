from __future__ import annotations
from pathlib import Path

"""Diagnostický pracovný tok CMEP.

Prechádza postupom:
1. Zber údajov iba na čítanie (git_diag, monitor)
2. Analýza (model_adapter, model_comparator)
3. Návrhy (decision_log - iba zaznamenávanie,never aplikácia)
4. Testovacie overenie (mock adaptéry)
5. Bezpečnostná kontrola (agent_roles, execution_policy)
6. Report (rozlišuje overené fakty, testové výsledky, modelové výstupy, neoverené zistenia)

Nikdy neaplikuje návrhy do $HOME/waste-platform. Nevyžaduje API kľúče.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.modules.agent_platform.navigator.git_diag import GitDiagnostic
from app.modules.agent_platform.navigator.monitor import collect_snapshot, check_site, validate_url, DEFAULT_URL
from app.modules.agent_platform.navigator.model_adapter import ModelAdapter, ModelResponse
from app.modules.agent_platform.navigator.mock_adapter import MockAdapter
from app.modules.agent_platform.navigator.model_comparator import compare, compare_adapter_outputs
from app.modules.agent_platform.navigator.decision_log import DecisionLog
from app.modules.agent_platform.navigator.agent_roles import AgentRoleManager, Agent, AgentRole
from app.modules.agent_platform.navigator.execution_policy import ExecutionPolicy, ExecutionMode
from app.modules.agent_platform.navigator.logging_safe import redact_any
from app.modules.agent_platform.navigator.permissions import PermissionPolicy, PermissionMode

@dataclass(frozen=True)
class VerifiedFact:
    source: str
    fact: str
    evidence: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class TestResult:
    test_name: str
    passed: bool
    detail: str = ""
    adapter: str | None = None

@dataclass(frozen=True)
class ModelOutput:
    adapter: str
    result: str
    deterministic: bool
    available: bool
    error: str | None = None

@dataclass(frozen=True)
class UnverifiedClaim:
    claim: str
    source: str
    reason: str

@dataclass(frozen=True)
class DiagnosticReport:
    workflow_id: str
    timestamp: str
    repo_path: str
    site_url: str
    execution_mode: str
    verified_facts: list[VerifiedFact] = field(default_factory=list)
    test_results: list[TestResult] = field(default_factory=list)
    model_outputs: list[ModelOutput] = field(default_factory=list)
    unverified_claims: list[UnverifiedClaim] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    comparison: dict[str, Any] = field(default_factory=dict)
    overall_status: str = "completed"

class DiagnosticWorkflow:
    def __init__(
        self,
        repo_path: str,
        site_url: str = DEFAULT_URL,
        policy: ExecutionPolicy | None = None,
        role_manager: AgentRoleManager | None = None,
        decision_log: DecisionLog | None = None,
        log_dir: str | Path | None = None,
    ):
        self.repo_path = repo_path
        self.site_url = site_url
        self.policy = policy or ExecutionPolicy()
        self.permission_policy = PermissionPolicy(mode=PermissionMode.DIAGNOSTIC)
        if role_manager is not None:
            role_manager.policy = self.permission_policy
            self.role_manager = role_manager
        else:
            self.role_manager = AgentRoleManager(policy=self.permission_policy)
            self.role_manager.register_agent(Agent(name="observer", role=AgentRole.OBSERVER))
            self.role_manager.register_agent(Agent(name="analyst", role=AgentRole.ANALYST))
            self.role_manager.register_agent(Agent(name="coordinator", role=AgentRole.COORDINATOR))
        self.decision_log = decision_log
        self.workflow_id = f"diag-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')}"
