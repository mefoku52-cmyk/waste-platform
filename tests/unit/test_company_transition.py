from unittest.mock import patch
from uuid import uuid4

import pytest

from app.modules.companies.application.services import (
    CreateCompanyService,
    TransitionCompanyStatusService,
)
from app.modules.companies.domain.enums import CompanyStatus
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError
from tests.unit.test_company_services import FakeCompanyRepo, FakeMembershipRepo, _create_kwargs


@pytest.fixture(autouse=True)
def mock_lookup_ico():
    """RPO lookup volá reálnu api.statistics.sk — v unit teste to musí byť mock.

    Bez tohto mocku test padá, keď RPO API spomalí / spadne / vráti not_found.
    """
    with patch(
        "app.modules.companies.application.services.lookup_ico",
        return_value={
            "ok": True,
            "exists": True,
            "ico": "12345678",
            "legalName": "Test Company s.r.o.",
            "city": "Bratislava",
            "reason": "found",
        },
    ):
        yield


def _other_status(current: CompanyStatus) -> str:
    for item in CompanyStatus:
        if item != current:
            return item.value if hasattr(item, "value") else str(item)
    return current.value


@pytest.mark.asyncio
async def test_transition_company_status():
    companies = FakeCompanyRepo()
    created = await CreateCompanyService(
        repo=companies,
        membership_repo=FakeMembershipRepo(),
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    ).execute(**_create_kwargs(actor_user_id=None))
    current = companies.items[0].status
    target = _other_status(current)
    dto = await TransitionCompanyStatusService(companies, Clock()).execute(
        company_id=created.id,
        to_status=target,
        actor_user_id=uuid4(),
    )
    assert dto is not None


@pytest.mark.asyncio
async def test_transition_missing_company():
    with pytest.raises(NotFoundDomainError):
        await TransitionCompanyStatusService(FakeCompanyRepo(), Clock()).execute(
            company_id=uuid4(),
            to_status=_other_status(next(iter(CompanyStatus))),
            actor_user_id=None,
        )
