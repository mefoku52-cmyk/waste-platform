"""EmailDrafter fallback bez AI + /admin/lead-outreach/status.

Pravidla, ktore tieto testy chrania:
- fallback NIKDY nevymysla fakty (len company_name, city, industry)
- fallback VZDY obsahuje GDPR blok + STOP (rovnako ako AI verzia)
- status endpoint NIKDY neodhali hodnotu API kluca
"""

from __future__ import annotations

import pytest

from app.modules.lead_finder.application.services.email_drafter import (
    EmailDrafter,
    _fallback_draft,
    _parse_draft,
)

# ---------------------------------------------------------------------------
# Deterministicky fallback
# ---------------------------------------------------------------------------


def test_fallback_has_gdpr_block_and_stop():
    d = _fallback_draft(company_name="Barents Corporation, s.r.o.")

    assert "STOP" in d.body
    assert "GDPR" in d.body
    assert "RPO" in d.body
    assert "čl. 6 ods. 1 písm. f)" in d.body
    assert "trc-cmep@gmail.com" in d.body
    assert "trc-cmep.sk" in d.body


def test_fallback_subject_contains_company_name():
    d = _fallback_draft(company_name="Barents Corporation, s.r.o.")
    assert "Barents Corporation" in d.subject


def test_fallback_uses_city_and_industry_when_given():
    d = _fallback_draft(
        company_name="Drevo Svar s.r.o.",
        city="Snina",
        industry="spracovanie dreva",
    )
    assert "Snina" in d.body
    assert "spracovanie dreva" in d.body


def test_fallback_without_city_and_industry_still_valid():
    d = _fallback_draft(company_name="Firma s.r.o.")

    assert "Firma s.r.o." in d.subject
    assert "STOP" in d.body
    assert "GDPR" in d.body
    # Nesmie zostat prazdne miesto po sablone.
    assert " v lokalite" not in d.body
    assert " v oblasti" not in d.body


@pytest.mark.parametrize(
    "marker",
    [
        # zakazane marketingove frazy a vymyslene sluby
        "revolučn",
        "revolucn",
        "unikátn",
        "unikatn",
        "najlepš",
        "najleps",
        "game-changer",
        "zľava",
        "zlava",
        "%",
        "eur",
        "€",
    ],
)
def test_fallback_never_invents_facts_or_promises(marker):
    d = _fallback_draft(
        company_name="Firma s.r.o.",
        city="Bratislava",
        industry="odpady",
    )
    assert marker.lower() not in d.body.lower()


def test_fallback_early_bird_line_only_when_active():
    with_bird = _fallback_draft(company_name="Firma s.r.o.", early_bird=True)
    without_bird = _fallback_draft(company_name="Firma s.r.o.", early_bird=False)

    assert "ZADARMO navždy" in with_bird.body
    assert "ZADARMO navždy" not in without_bird.body
    assert "PRO alebo AI" not in without_bird.body


def test_fallback_is_deterministic():
    a = _fallback_draft(company_name="Firma s.r.o.", city="Snina")
    b = _fallback_draft(company_name="Firma s.r.o.", city="Snina")
    assert a == b


def test_fallback_has_no_html():
    d = _fallback_draft(company_name="Firma s.r.o.")
    assert "<" not in d.body
    assert "<br" not in d.body.lower()


# ---------------------------------------------------------------------------
# _parse_draft prazdne telo -> fallback (nie stara rucna sablona)
# ---------------------------------------------------------------------------


def test_parse_empty_body_returns_fallback_with_stop_and_gdpr():
    d = _parse_draft("", fallback_company="Firma X")

    assert "Firma X" in d.subject
    assert "STOP" in d.body
    assert "GDPR" in d.body
    assert "RPO" in d.body


# ---------------------------------------------------------------------------
# draft() prezije zlyhanie AI providera
# ---------------------------------------------------------------------------


class _FailingGateway:
    async def generate(self, _request):
        raise RuntimeError("GROQ_API_KEY missing")


class _EmptyGateway:
    async def generate(self, _request):
        from app.modules.agent_platform.infrastructure.ai.model_response import (
            ModelResponse,
        )

        return ModelResponse(request_id="x", text="", finish_reason="stop")


class _OkGateway:
    async def generate(self, _request):
        from app.modules.agent_platform.infrastructure.ai.model_response import (
            ModelResponse,
        )

        return ModelResponse(
            request_id="x",
            text="SUBJECT: Pozvanka\n---\nTelo od AI.",
            finish_reason="stop",
        )


async def test_draft_falls_back_when_gateway_raises():
    drafter = EmailDrafter(gateway=_FailingGateway())

    d = await drafter.draft(company_name="Barents Corporation, s.r.o.")

    assert "Barents Corporation" in d.subject
    assert "STOP" in d.body
    assert "GDPR" in d.body


async def test_draft_falls_back_when_gateway_returns_empty():
    drafter = EmailDrafter(gateway=_EmptyGateway())

    d = await drafter.draft(company_name="Firma s.r.o.")

    assert "STOP" in d.body
    assert "GDPR" in d.body


async def test_draft_uses_ai_output_when_gateway_works():
    drafter = EmailDrafter(gateway=_OkGateway())

    d = await drafter.draft(company_name="Firma s.r.o.")

    assert d.subject == "Pozvanka"
    assert "Telo od AI" in d.body


# ---------------------------------------------------------------------------
# is_provider_configured — nikdy nevrati hodnotu kluca
# ---------------------------------------------------------------------------


def test_provider_configured_true_when_key_set(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_super_secret_value")
    assert EmailDrafter.is_provider_configured() is True


def test_provider_configured_false_when_key_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert EmailDrafter.is_provider_configured() is False


def test_provider_configured_false_when_key_blank(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "   ")
    assert EmailDrafter.is_provider_configured() is False
