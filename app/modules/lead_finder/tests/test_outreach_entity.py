"""OutreachCandidate entity tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.modules.lead_finder.domain.entities.outreach_candidate import (
    OutreachCandidate,
    OutreachStatus,
)


def _candidate(**overrides) -> OutreachCandidate:
    now = datetime.now(UTC)
    base = {
        "id": "c1",
        "company_name": "Test s.r.o.",
        "ico": "12345678",
        "city": "Ulic",
        "industry": "Drevospracovanie",
        "email": "a@b.sk",
        "status": OutreachStatus.NEW,
        "draft_subject": None,
        "draft_body": None,
        "created_at": now,
        "updated_at": now,
        "approved_at": None,
        "sent_at": None,
    }
    base.update(overrides)
    return OutreachCandidate(**base)


def test_entity_valid() -> None:
    c = _candidate()
    assert c.company_name == "Test s.r.o."
    assert c.status == OutreachStatus.NEW


def test_entity_requires_id() -> None:
    with pytest.raises(ValueError):
        _candidate(id="")


def test_entity_requires_company_name() -> None:
    with pytest.raises(ValueError):
        _candidate(company_name="")


def test_status_values() -> None:
    assert OutreachStatus.NEW.value == "new"
    assert OutreachStatus.DRAFTED.value == "drafted"
    assert OutreachStatus.APPROVED.value == "approved"
    assert OutreachStatus.SENT.value == "sent"
