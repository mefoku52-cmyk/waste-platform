"""Role-aware system prompt tests."""

from __future__ import annotations

from app.modules.agent_platform.presentation import chat_router


class _Admin:
    isPlatformAdmin = True
    email = "radoslav@cmep.sk"


class _Customer:
    isPlatformAdmin = False
    email = "zakaznik@firma.sk"


class _Broken:
    pass


def test_admin_gets_architect_addendum(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: True)
    prompt = chat_router._build_system_prompt(_Admin())
    assert "ARCHITEKT" in prompt or "architekt" in prompt
    assert "Radoslav" in prompt


def test_customer_gets_customer_addendum(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    prompt = chat_router._build_system_prompt(_Customer())
    assert "firemnému používateľovi" in prompt
    assert "ARCHITEKT" not in prompt


def test_base_rules_always_present(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: False)
    p1 = chat_router._build_system_prompt(_Customer())
    monkeypatch.setattr(chat_router, "is_platform_admin", lambda u: True)
    p2 = chat_router._build_system_prompt(_Admin())
    # Spolocne pravidla
    assert "search_companies" in p1 and "search_companies" in p2
    assert "NIKDY NEROBIŤ" in p1 and "NIKDY NEROBIŤ" in p2


def test_broken_user_falls_back_to_customer(monkeypatch) -> None:
    def boom(u):
        raise RuntimeError("broken")

    monkeypatch.setattr(chat_router, "is_platform_admin", boom)
    prompt = chat_router._build_system_prompt(_Broken())
    assert "firemnému používateľovi" in prompt


def test_base_rules_forbid_admin_words() -> None:
    """Base rules contain the anti-leak clause."""
    assert "admin" in chat_router.BASE_RULES
    assert "architekt" in chat_router.BASE_RULES.lower()
    assert "debug" in chat_router.BASE_RULES.lower()
