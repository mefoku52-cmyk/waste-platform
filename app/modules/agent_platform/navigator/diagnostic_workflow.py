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
from datetime import UTC, datetime
from typing import Any

from .agent_roles import Agent, AgentRole, AgentRoleManager
from .decision_log import DecisionLog
from .execution_policy import ExecutionMode, ExecutionPolicy
from .git_diag import GitDiagnostic
from .logging_safe import redact_any
from .mock_adapter import MockAdapter
from .model_comparator import compare, compare_adapter_outputs
from .monitor import DEFAULT_URL, check_site
from .permissions import PermissionMode, PermissionPolicy


@dataclass(frozen=True)
class VerifiedFact:
    """Overený fakt - potvrdený nezávislým zdrojom alebo deterministickým výpočtom."""

    source: str
    fact: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TestResult:
    """Výsledok testového overenia."""

    test_name: str
    passed: bool
    detail: str = ""
    adapter: str | None = None


@dataclass(frozen=True)
class ModelOutput:
    """Výstup z modelu (mock alebo skutočný)."""

    adapter: str
    result: str
    deterministic: bool
    available: bool
    error: str | None = None


@dataclass(frozen=True)
class UnverifiedClaim:
    """Neoverené zistenie - vyžaduje ďalšie overenie."""

    claim: str
    source: str
    reason: str


@dataclass(frozen=True)
class DiagnosticReport:
    """Komplexná správa z diagnostického pracovného toku.

    Rozlišuje medzi:
    - overenými faktami (VerifiedFact)
    - testovými výsledkami (TestResult)
    - modelovými výstupmi (ModelOutput)
    - neoverenými zisteniami (UnverifiedClaim)
    - bezpečnostnými blokátormi
    """

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
    """Diagnostický pracovný tok CMEP - iba čítanie, žiadne mutácie."""

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
        self.policy = policy or ExecutionPolicy()  # DISABLED je predvoleny
        self.permission_policy = PermissionPolicy(mode=PermissionMode.DIAGNOSTIC)
        if role_manager is not None:
            role_manager.policy = self.permission_policy
            self.role_manager = role_manager
        else:
            self.role_manager = AgentRoleManager(policy=self.permission_policy)
            # Auto-registruj predvolene agentov pre internalne kroky workflow
            self.role_manager.register_agent(Agent(name="observer", role=AgentRole.OBSERVER))
            self.role_manager.register_agent(Agent(name="analyst", role=AgentRole.ANALYST))
            self.role_manager.register_agent(Agent(name="coordinator", role=AgentRole.COORDINATOR))
        self.decision_log = decision_log
        self.workflow_id = f"diag-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S-%f')}"

    def _check_agent(self, agent_name: str, operation: str) -> bool:
        """Skontroluje oprávnenie agenta pre operáciu."""
        perm = self.role_manager.check_agent(agent_name, operation)
        return perm.allowed

    def step_1_gather_readonly(self, agent_name: str = "observer") -> dict[str, Any]:
        """Krok 1: Zber údajov iba na čítanie."""
        if not self._check_agent(agent_name, "inspect"):
            return {
                "step": "gather",
                "status": "permission_denied",
                "agent": agent_name,
                "error": f"Agent {agent_name} nemá oprávnenie 'inspect'",
            }

        data: dict[str, Any] = {"step": "gather", "status": "completed"}

        # Git diagnostika (read-only)
        try:
            git = GitDiagnostic(self.repo_path).full_diagnostic()
            data["git"] = git
        except Exception as exc:
            data["git"] = None
            data["git_error"] = type(exc).__name__
            data["status"] = "completed_with_errors"

        # Monitor - web dostupnosť
        try:
            site = check_site(self.site_url)
            data["site"] = site
        except Exception as exc:
            data["site"] = None
            data["site_error"] = type(exc).__name__
            data["status"] = "completed_with_errors"

        return data

    def step_2_analyze(
        self,
        gather_data: dict[str, Any],
        agent_name: str = "analyst",
    ) -> dict[str, Any]:
        """Krok 2: Analýza鐵ziskanych údajov pomocou modelov."""
        if not self._check_agent(agent_name, "analyze"):
            return {
                "step": "analyze",
                "status": "permission_denied",
                "agent": agent_name,
                "error": f"Agent {agent_name} nemá oprávnenie 'analyze'",
            }

        # Použijeme MockAdapter - nevyžaduje API kľúč, deterministický
        adapter = MockAdapter(policy=self.policy)

        analysis_input = {
            "git_branch": (gather_data.get("git") or {}).get("branch"),
            "git_clean": (gather_data.get("git") or {}).get("clean"),
            "site_ok": (gather_data.get("site") or {}).get("ok"),
            "site_status": (gather_data.get("site") or {}).get("status"),
            "git_error": gather_data.get("git_error"),
            "site_error": gather_data.get("site_error"),
        }

        prompt = (
            f"Analyzuj stav CMEP: git_branch={analysis_input['git_branch']}, "
            f"git_clean={analysis_input['git_clean']}, site_ok={analysis_input['site_ok']}, "
            f"site_status={analysis_input['site_status']}"
        )

        model_response = adapter.infer(prompt, context=analysis_input)

        model_output = ModelOutput(
            adapter=model_response.adapter,
            result=redact_any(model_response.result),
            deterministic=model_response.deterministic,
            available=model_response.available,
            error=redact_any(model_response.error),
        )

        result: dict[str, Any] = {
            "step": "analyze",
            "status": "completed",
            "agent": agent_name,
            "model_output": {
                "adapter": model_output.adapter,
                "result": model_output.result,
                "deterministic": model_output.deterministic,
                "available": model_output.available,
                "error": model_output.error,
            },
            "analysis_input": analysis_input,
        }

        # Zapíšeme rozhodnutie o analýze do decision_log (ak je k dispozícii)
        if self.decision_log is not None:
            try:
                self.decision_log.add_decision(
                    decision_id=f"{self.workflow_id}-analyze",
                    decision_type="model_analysis",
                    summary=f"Analýza CMEP stavu pomocou {model_output.adapter}",
                    actor=agent_name,
                    provenance={
                        "adapter": model_output.adapter,
                        "deterministic": model_output.deterministic,
                    },
                    evidence_refs=[model_output.result] if model_output.result else [],
                    verified_facts=[f"git_branch={analysis_input['git_branch']}"],
                    unverified_claims=[model_output.result] if model_output.result else [],
                )
            except Exception:
                pass  # Decision log chyba nesmie zablokovať workflow

        return result

    def step_3_proposals(
        self,
        analysis_data: dict[str, Any],
        agent_name: str = "coordinator",
    ) -> dict[str, Any]:
        """Krok 3: Návrhy opráv - iba zaznamenávanie, never aplikácia."""
        if not self._check_agent(agent_name, "coordinate"):
            return {
                "step": "propose",
                "status": "permission_denied",
                "agent": agent_name,
                "error": f"Agent {agent_name} nemá oprávnenie 'coordinate'",
            }

        proposals: list[dict[str, Any]] = []

        # Generujeme návrhy na základe analýzy (iba návrhy, žiadna aplikácia)
        git_data = (
            analysis_data.get("git", {}) if isinstance(analysis_data.get("git"), dict) else {}
        )
        site_data = (
            analysis_data.get("site", {}) if isinstance(analysis_data.get("site"), dict) else {}
        )

        if not git_data.get("clean", True):
            proposals.append(
                {
                    "id": f"{self.workflow_id}-prop-1",
                    "type": "repo_cleanup",
                    "description": "Repositár má nečistý pracovný strom",
                    "proposed_action": "Preverit zmeny v pracovnom strome",
                    "applied": False,
                    "reason": "Read-only režim - návrh sa nepoužije",
                }
            )

        if not site_data.get("ok", True):
            proposals.append(
                {
                    "id": f"{self.workflow_id}-prop-2",
                    "type": "site_remediation",
                    "description": f"Web stránka je nedostupná (status={site_data.get('status')})",
                    "proposed_action": "Skontrolovať dostupnosť webu",
                    "applied": False,
                    "reason": "Read-only režim - návrh sa nepoužije",
                }
            )

        # Zapíšeme návrhy do decision_log
        if self.decision_log is not None:
            for prop in proposals:
                try:
                    self.decision_log.add_decision(
                        decision_id=prop["id"],
                        decision_type="proposal",
                        summary=prop["description"],
                        actor=agent_name,
                        provenance={"workflow_id": self.workflow_id, "step": "propose"},
                        verified_facts=[prop["description"]],
                        unverified_claims=[prop["proposed_action"]],
                        blocker="Read-only režim - návrh nie je aplikovaný",
                    )
                except Exception:
                    pass

        return {
            "step": "propose",
            "status": "completed",
            "agent": agent_name,
            "proposals": proposals,
            "proposals_applied": False,
            "note": "Všetky návrhy sú iba zaznamenané, žiadna nie je aplikovaná do repozitára",
        }

    def step_4_test_verification(
        self,
        agent_name: str = "analyst",
    ) -> dict[str, Any]:
        """Krok 4: Testové overenie pomocou mock adaptérov (bez API kľúča)."""
        if not self._check_agent(agent_name, "compare"):
            return {
                "step": "verify",
                "status": "permission_denied",
                "agent": agent_name,
                "error": f"Agent {agent_name} nemá oprávnenie 'compare'",
            }

        # Spustíme testy cez mock adaptéry (deterministické, bez API kľúča)
        adapter_a = MockAdapter(policy=self.policy, seed="test-a")
        adapter_b = MockAdapter(policy=self.policy, seed="test-b")

        test_prompts = ["test-verify-1", "test-verify-2", "test-verify-3"]
        test_results: list[TestResult] = []

        for prompt in test_prompts:
            r_a = adapter_a.infer(prompt)
            r_b = adapter_b.infer(prompt)
            comp = compare(r_a, r_b)
            test_results.append(
                TestResult(
                    test_name=f"mock_compare_{prompt}",
                    passed=comp.match,
                    detail=f"Adapter A: {r_a.result}, Adapter B: {r_b.result}",
                    adapter="mock",
                )
            )

        # Porovnanie viacerých adapterov
        responses = {
            "adapter-a": adapter_a.infer("consistency-check"),
            "adapter-b": adapter_b.infer("consistency-check"),
        }
        comparison = compare_adapter_outputs(responses)

        return {
            "step": "verify",
            "status": "completed",
            "agent": agent_name,
            "test_results": [
                {
                    "test_name": t.test_name,
                    "passed": t.passed,
                    "detail": t.detail,
                    "adapter": t.adapter,
                }
                for t in test_results
            ],
            "comparison": comparison,
            "all_tests_passed": all(t.passed for t in test_results),
        }

    def step_5_security_check(
        self,
        agent_name: str = "observer",
    ) -> dict[str, Any]:
        """Krok 5: Bezpečnostná kontrola."""
        if not self._check_agent(agent_name, "check"):
            return {
                "step": "security",
                "status": "permission_denied",
                "agent": agent_name,
                "error": f"Agent {agent_name} nemá oprávnenie 'check'",
            }

        blockers: list[str] = []
        checks: dict[str, Any] = {}

        # Kontrola ExecutionMode
        checks["execution_mode"] = self.policy.mode.value
        if self.policy.mode == ExecutionMode.DISABLED:
            blockers.append("ExecutionMode je DISABLED - žiadne vykonanie nie je povolené")

        # Kontrola registrovaných agentov
        checks["registered_agents"] = self.role_manager.list_agents()

        # Kontrola zakázaných operácií
        forbidden_tested = ["write", "commit", "deploy", "git_push", "db_write"]
        checks["forbidden_operations_denied"] = {}
        for op in forbidden_tested:
            checks["forbidden_operations_denied"][op] = not self._check_agent(agent_name, op)

        return {
            "step": "security",
            "status": "completed",
            "agent": agent_name,
            "checks": checks,
            "blockers": blockers,
        }

    def step_6_report(
        self,
        gather_data: dict[str, Any],
        analysis_data: dict[str, Any],
        verify_data: dict[str, Any],
        security_data: dict[str, Any],
        proposals_data: dict[str, Any],
    ) -> DiagnosticReport:
        """Krok 6: Vygenerovanie komplexnej správy."""
        verified_facts: list[VerifiedFact] = []
        test_results: list[TestResult] = []
        model_outputs: list[ModelOutput] = []
        unverified_claims: list[UnverifiedClaim] = []
        blockers: list[str] = [redact_any(b) for b in security_data.get("blockers", [])]

        # Overené fakty z gather dát
        git = gather_data.get("git")
        git_error = gather_data.get("git_error")
        if git_error:
            blockers.append(redact_any(f"Git diagnostika zlyhala: {git_error}"))
            unverified_claims.append(
                UnverifiedClaim(
                    claim=f"Git diagnostika zlyhala: {git_error}",
                    source="git_diagnostic",
                    reason="GitDiagnostic vyhodil výnimku pri čítaní repozitára",
                )
            )
        elif isinstance(git, dict) and git:
            verified_facts.append(
                VerifiedFact(
                    source="git_diagnostic",
                    fact=f"Vetva: {git.get('branch', 'unknown')}",
                    evidence={"clean": git.get("clean")},
                )
            )
            verified_facts.append(
                VerifiedFact(
                    source="git_diagnostic",
                    fact=f"Pracovny strom cisty: {git.get('clean', False)}",
                    evidence={"changes": git.get("status", {}).get("changes", [])},
                )
            )

        site = gather_data.get("site")
        site_error = gather_data.get("site_error")
        if site_error:
            blockers.append(redact_any(f"Webova kontrola zlyhala: {site_error}"))
            unverified_claims.append(
                UnverifiedClaim(
                    claim=f"Webova kontrola zlyhala: {site_error}",
                    source="site_check",
                    reason="check_site() vyhodil výnimku pri kontrole webu",
                )
            )
        elif isinstance(site, dict) and site:
            verified_facts.append(
                VerifiedFact(
                    source="site_check",
                    fact=f"Web dostupny: {site.get('ok', False)}",
                    evidence={"status": site.get("status"), "elapsed_ms": site.get("elapsed_ms")},
                )
            )

        # Modelové výstupy z analýzy
        model_out = analysis_data.get("model_output", {})
        if model_out:
            model_outputs.append(
                ModelOutput(
                    adapter=model_out.get("adapter", "unknown"),
                    result=model_out.get("result", ""),
                    deterministic=model_out.get("deterministic", False),
                    available=model_out.get("available", False),
                    error=model_out.get("error"),
                )
            )
            # Modelový výstup je neoverené tvrdenie (nie overený fakt)
            if model_out.get("result"):
                unverified_claims.append(
                    UnverifiedClaim(
                        claim=model_out["result"],
                        source=f"model:{model_out.get('adapter', 'unknown')}",
                        reason="Modelový výstup nie je overený nezávislým zdrojom",
                    )
                )

        # Testové výsledky
        for tr in verify_data.get("test_results", []):
            test_results.append(
                TestResult(
                    test_name=tr["test_name"],
                    passed=tr["passed"],
                    detail=redact_any(tr.get("detail", "")),
                    adapter=tr.get("adapter"),
                )
            )
            if not tr["passed"]:
                blockers.append(redact_any(f"Test zlyhal: {tr['test_name']}"))

        # Návrhy (nie sú aplikované)
        proposals = proposals_data.get("proposals", [])

        overall_status = "completed"
        if blockers:
            overall_status = "completed_with_blockers"

        return DiagnosticReport(
            workflow_id=self.workflow_id,
            timestamp=datetime.now(UTC).isoformat(),
            repo_path=self.repo_path,
            site_url=self.site_url,
            execution_mode=self.policy.mode.value,
            verified_facts=verified_facts,
            test_results=test_results,
            model_outputs=model_outputs,
            unverified_claims=unverified_claims,
            blockers=blockers,
            proposals=proposals,
            comparison=verify_data.get("comparison", {}),
            overall_status=overall_status,
        )

    def run(
        self,
        agent_name: str = "observer",
    ) -> dict[str, Any]:
        """Spustí celý diagnostický pracovný tok."""
        results: dict[str, Any] = {
            "workflow_id": self.workflow_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "steps": {},
        }

        # Krok 1: Zber
        results["steps"]["gather"] = self.step_1_gather_readonly(agent_name)

        # Krok 2: Analýza
        results["steps"]["analyze"] = self.step_2_analyze(
            results["steps"]["gather"], agent_name="analyst"
        )

        # Krok 3: Návrhy
        results["steps"]["propose"] = self.step_3_proposals(
            results["steps"]["gather"], agent_name="coordinator"
        )

        # Krok 4: Overenie
        results["steps"]["verify"] = self.step_4_test_verification(agent_name="analyst")

        # Krok 5: Bezpečnosť
        results["steps"]["security"] = self.step_5_security_check(agent_name=agent_name)

        # Krok 6: Report
        report = self.step_6_report(
            results["steps"]["gather"],
            results["steps"]["analyze"],
            results["steps"]["verify"],
            results["steps"]["security"],
            results["steps"]["propose"],
        )
        results["report"] = {
            "workflow_id": report.workflow_id,
            "timestamp": report.timestamp,
            "repo_path": report.repo_path,
            "site_url": report.site_url,
            "execution_mode": report.execution_mode,
            "verified_facts": [
                {"source": f.source, "fact": f.fact, "evidence": f.evidence}
                for f in report.verified_facts
            ],
            "test_results": [
                {
                    "test_name": t.test_name,
                    "passed": t.passed,
                    "detail": t.detail,
                    "adapter": t.adapter,
                }
                for t in report.test_results
            ],
            "model_outputs": [
                {
                    "adapter": m.adapter,
                    "result": m.result,
                    "deterministic": m.deterministic,
                    "available": m.available,
                    "error": m.error,
                }
                for m in report.model_outputs
            ],
            "unverified_claims": [
                {"claim": c.claim, "source": c.source, "reason": c.reason}
                for c in report.unverified_claims
            ],
            "blockers": report.blockers,
            "proposals": report.proposals,
            "comparison": report.comparison,
            "overall_status": report.overall_status,
        }

        return results
