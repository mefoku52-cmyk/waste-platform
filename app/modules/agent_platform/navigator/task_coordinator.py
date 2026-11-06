"""Koordinátor úloh s limitmi pokusov, časovým limitom a bezpečným spracovaním chýb.

Spouští úlohy s ohľadom na:
- ExecutionPolicy (predvolene DISABLED - žiadne vykonanie)
- AgentRoleManager (oprávnenia agenta)
- Maximálny počet pokusov (retry pri zlyhaní)
- Časový limit (timeout)
- Bezpečné spracovanie chýb (žiadne neodchýtené výnimky)
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from typing import Any

from .agent_roles import AgentRoleManager
from .execution_policy import ExecutionMode, ExecutionPolicy
from .logging_safe import redact_any
from .permissions import PermissionMode, PermissionPolicy


@dataclass(frozen=True)
class TaskResult:
    """Výsledok vykonania jednej úlohy koordinátorom."""

    task_id: str
    status: str  # "completed", "failed", "timeout", "blocked", "disabled", "max_attempts_exceeded", "permission_denied"
    attempt: int
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    agent: str | None = None


class TaskCoordinator:
    """Koordinuje vykonanie úloh s limitmi a bezpečnou obsluhou chýb."""

    def __init__(
        self,
        policy: ExecutionPolicy | None = None,
        role_manager: AgentRoleManager | None = None,
        max_attempts: int = 3,
        default_timeout: float = 30.0,
    ):
        self.policy = policy or ExecutionPolicy()  # DISABLED je predvoleny
        self.permission_policy = PermissionPolicy(mode=PermissionMode.DIAGNOSTIC)
        if role_manager is not None:
            role_manager.policy = self.permission_policy
            self.role_manager = role_manager
        else:
            self.role_manager = AgentRoleManager(policy=self.permission_policy)
        self.max_attempts = max_attempts
        self.default_timeout = default_timeout
        self._history: list[TaskResult] = []

    def run(
        self,
        task_id: str,
        func: Callable[[], Any],
        agent_name: str | None = None,
        max_attempts: int | None = None,
        timeout: float | None = None,
        operation: str = "diagnose",
    ) -> TaskResult:
        """Vykoná úlohu s limitmi pokusov, timeoutom a bezpečnou obsluhou chýb.

        - Kontrola oprávnení agenta (double-check role + policy)
        - Kontrola ExecutionMode (DISABLED zablokuje vykonanie)
        - Opakovanie pri zlyhaní (max_attempts)
        - Časový limit na jeden pokus

        POZOR: Časový limit iba prestane čakať na výsledok vlákna,
        nezastaví samotné vykonávanie funkcie ``func``. Vlákno beží
        ďalej na pozadí až do dokončenia. Toto je obmedzenie platformy
        Android/Termux, kde bezpečné ukončenie vlákna z vonku nie je
        spoľahlivo dostupné. Timeout sa zaznamenáva ako chyba pokusu,
        ale funkcia sa môže pokračovať mimo kontroly koordinátora.
        """
        attempts = max_attempts if max_attempts is not None else self.max_attempts
        timeout_val = timeout if timeout is not None else self.default_timeout

        # 1. Kontrola oprávnení agenta
        if agent_name is not None:
            perm = self.role_manager.check_agent(agent_name, operation)
            if not perm.allowed:
                result = TaskResult(
                    task_id=task_id,
                    status="permission_denied",
                    attempt=0,
                    error=redact_any(perm.reason),
                    agent=agent_name,
                )
                self._history.append(result)
                return result

        # 2. Kontrola ExecutionMode
        if self.policy.mode == ExecutionMode.DISABLED:
            result = TaskResult(
                task_id=task_id,
                status="disabled",
                attempt=0,
                error="Vykonanie je vypnute (DISABLED)",
                agent=agent_name,
            )
            self._history.append(result)
            return result

        if not self.policy.is_allowed(operation):
            result = TaskResult(
                task_id=task_id,
                status="blocked",
                attempt=0,
                error=f"Operacia '{operation}' nie je povolena politikou",
                agent=agent_name,
            )
            self._history.append(result)
            return result

        # 3. Vykonanie s pokusami a timeoutom
        last_error: str | None = None
        last_result: Any = None
        start_total = time.monotonic()

        for attempt in range(1, attempts + 1):
            try:
                # POZOR: nepouzivame `with ThreadPoolExecutor(...)` — jeho
                # __exit__ robi shutdown(wait=True), takze pri timeoute by sa
                # cakalo na dobehnutie zaveseneho vlakna a timeout by nemal
                # ziadny efekt. shutdown(wait=False) necha vlakno dobehnut
                # na pozadi (zamerne — vid docstring vyssie).
                executor = ThreadPoolExecutor(max_workers=1)
                future = executor.submit(func)
                try:
                    last_result = future.result(timeout=timeout_val)
                except FuturesTimeoutError:
                    last_error = f"Casovy limit vyprsel ({timeout_val}s)"
                    executor.shutdown(wait=False)
                    continue
                except Exception as exc:
                    last_error = type(exc).__name__
                    executor.shutdown(wait=False)
                    continue
                executor.shutdown(wait=False)

                # Úspešné vykonanie
                duration_ms = round((time.monotonic() - start_total) * 1000, 2)
                result = TaskResult(
                    task_id=task_id,
                    status="completed",
                    attempt=attempt,
                    result=redact_any(last_result),
                    agent=agent_name,
                    duration_ms=duration_ms,
                )
                self._history.append(result)
                return result

            except Exception as exc:
                # Neodchýtená výnimka - bezpečné zachytenie
                last_error = f"Neočakávaná chyba: {type(exc).__name__}"

        # Vyčerpané všetky pokusy
        duration_ms = round((time.monotonic() - start_total) * 1000, 2)
        result = TaskResult(
            task_id=task_id,
            status="max_attempts_exceeded",
            attempt=attempts,
            error=redact_any(last_error or "Neznáma chyba"),
            result=redact_any(last_result),
            agent=agent_name,
            duration_ms=duration_ms,
        )
        self._history.append(result)
        return result

    def history(self) -> list[TaskResult]:
        """Vráti históriu vykonaných úloh (nemenný zoznam kopií)."""
        return list(self._history)

    def last_result(self, task_id: str) -> TaskResult | None:
        """Vráti posledný výsledok pre dané task_id."""
        for r in reversed(self._history):
            if r.task_id == task_id:
                return r
        return None
