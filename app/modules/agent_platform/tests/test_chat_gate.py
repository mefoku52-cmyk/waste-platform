"""Chat gate tests – 402/403 before any orchestrator call."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.modules.agent_platform.presentation import user_ai_chat_router as chat_router
from app.modules.companies.domain.enums import SubscriptionTier


class _User:
    def __init__(self, *, email: str = "user@test.sk", memberships=None) -> None:
        self.email = email
        self.memberships = memberships or []


class _Entitlements:
    def __init__(self, results: dict[str, bool]) -> None:
        self._results = results
        self.calls: list[tuple[str, SubscriptionTier]] = []

    async def has_tier(self, company_id: str, minimum: SubscriptionTier) -> bool:
        self.calls.append((str(company_id), minimum))
        return self._results.get(str(company_id), False)


@pytest.mark.asyncio
async def test_chat_gate_admin_passes(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: True)
    monkeypatch.setattr(chat_router, "membership_company_ids", lambda u: [])
    ent = _Entitlements({})

    # Admin passes even without company and without PRO.
    await chat_router._check_ai_entitlement(
        current_user=_User(),
        entitlements=ent,  # type: ignore[arg-type]
    )
    assert ent.calls == []


@pytest.mark.asyncio
async def test_chat_gate_pro_passes(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    monkeypatch.setattr(chat_router, "membership_company_ids", lambda u: ["c1"])
    ent = _Entitlements({"c1": True})

    await chat_router._check_ai_entitlement(
        current_user=_User(),
        entitlements=ent,  # type: ignore[arg-type]
    )
    assert ent.calls and ent.calls[0][0] == "c1"


@pytest.mark.asyncio
async def test_chat_gate_second_company_passes(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    monkeypatch.setattr(chat_router, "membership_company_ids", lambda u: ["c1", "c2"])
    ent = _Entitlements({"c1": False, "c2": True})

    await chat_router._check_ai_entitlement(
        current_user=_User(),
        entitlements=ent,  # type: ignore[arg-type]
    )
    assert [c[0] for c in ent.calls] == ["c1", "c2"]


@pytest.mark.asyncio
async def test_chat_gate_free_returns_402(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    monkeypatch.setattr(chat_router, "membership_company_ids", lambda u: ["c1"])
    ent = _Entitlements({"c1": False})

    with pytest.raises(HTTPException) as exc:
        await chat_router._check_ai_entitlement(
            current_user=_User(),
            entitlements=ent,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_chat_gate_no_company_returns_403(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    monkeypatch.setattr(chat_router, "membership_company_ids", lambda u: [])
    ent = _Entitlements({})

    with pytest.raises(HTTPException) as exc:
        await chat_router._check_ai_entitlement(
            current_user=_User(),
            entitlements=ent,  # type: ignore[arg-type]
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_control_mode_read_failure_fails_closed() -> None:
    class _BrokenControl:
        async def get_mode(self):
            raise RuntimeError("database unavailable")

    with pytest.raises(HTTPException) as exc:
        await chat_router._resolve_chat_gate(_BrokenControl())

    assert exc.value.status_code == 503
