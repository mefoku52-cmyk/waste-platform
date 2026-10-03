"""Testy CmepCompanySearchHandler — bez realneho CMEP service a bez HTTP.

Handler je business boundary: validuje argumenty, rozhoduje o scope
(admin vs. clen firmy) a serializuje vysledok. CMEP service sa mockuje,
aby testy ostali hermetic.
"""

from dataclasses import dataclass

import pytest

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.tools.cmep_company_search_handler import (
    CmepCompanySearchHandler as Handler,
)

_TOOL = "cmep.company.search"


def make_request(arguments=None, **overrides) -> ToolRequest:
    kwargs = {
        "request_id": "req-1",
        "tool_name": _TOOL,
        "actor_id": "actor-1",
        "actor_type": "user",
        "arguments": arguments if arguments is not None else {},
        "reason": "test",
    }
    kwargs.update(overrides)
    return ToolRequest(**kwargs)


@dataclass
class FakeItem:
    id: str = "c1"
    legal_name: str = "EKOL s.r.o."
    trading_name: str | None = "EKOL"
    registration_number: str | None = "12345678"
    company_type: str | None = "sro"
    status: str | None = "active"
    city: str | None = "Presov"
    country_code: str | None = "SK"
    seller_capability: bool | None = True
    buyer_capability: bool | None = None
    logistics_capability: bool | None = None


class FakeService:
    """Minimalna nahrada CMEP company service."""

    def __init__(self, items=(), total=0, error: Exception | None = None) -> None:
        self.items = list(items)
        self.total = total
        self.error = error
        self.calls: list[dict] = []

    async def execute(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return list(self.items), self.total


def make_handler(service, *, admin=False, company_ids=()) -> Handler:
    return Handler(
        service=service,
        is_platform_admin=admin,
        company_ids=tuple(company_ids),
    )


# --- Validacia argumentov -----------------------------------------------


@pytest.mark.asyncio
async def test_invalid_arguments_error():
    service = FakeService()
    result = await make_handler(service).handle(make_request({"bogus": 1, "zzz": 2}))

    assert result.success is False
    assert result.error_code == "invalid_arguments"
    assert result.error_message is not None
    assert "bogus" in result.error_message
    assert "zzz" in result.error_message
    # Neznamy argument nesmie dojst az k service.
    assert service.calls == []


@pytest.mark.asyncio
async def test_non_numeric_page_rejected():
    service = FakeService()
    result = await make_handler(service).handle(make_request({"page": "abc"}))

    assert result.success is False
    assert result.error_code == "invalid_arguments"
    assert result.error_message is not None
    assert "musia byť čísla" in result.error_message
    assert service.calls == []


@pytest.mark.asyncio
async def test_page_size_over_limit_rejected():
    """Handler page_size NEclampuje — hodnota > 50 je invalid_arguments."""
    service = FakeService()
    result = await make_handler(service).handle(make_request({"page_size": 999}))

    assert result.success is False
    assert result.error_code == "invalid_arguments"
    assert result.error_message == "Neplatné page/page_size."
    assert service.calls == []


# --- Defaults -----------------------------------------------------------


@pytest.mark.asyncio
async def test_page_defaults():
    service = FakeService()
    result = await make_handler(service, admin=True).handle(make_request({"q": "ekol"}))

    assert result.success is True
    call = service.calls[0]
    assert call["page"] == 1
    assert call["page_size"] == 10
    assert call["q"] == "ekol"
    assert call["status"] is None


# --- Scope: admin vs. clen firmy vs. denial -----------------------------


@pytest.mark.asyncio
async def test_admin_sees_all_companies():
    service = FakeService()
    result = await make_handler(service, admin=True).handle(make_request())

    assert result.success is True
    # Admin -> ziadne obmedzenie scope.
    assert service.calls[0]["company_ids"] is None


@pytest.mark.asyncio
async def test_company_user_scoped_to_own_ids():
    service = FakeService()
    handler = make_handler(service, company_ids=("c1", "c2"))
    result = await handler.handle(make_request())

    assert result.success is True
    assert service.calls[0]["company_ids"] == ["c1", "c2"]


@pytest.mark.asyncio
async def test_company_access_denied():
    service = FakeService()
    result = await make_handler(service, company_ids=()).handle(make_request())

    assert result.success is False
    assert result.error_code == "company_access_denied"
    assert service.calls == []


# --- Service failure + serializacia -------------------------------------


@pytest.mark.asyncio
async def test_service_exception_wrapped():
    service = FakeService(error=RuntimeError("db down"))
    result = await make_handler(service, admin=True).handle(make_request())

    assert result.success is False
    assert result.error_code == "company_search_failed"
    assert result.error_message is not None
    assert "RuntimeError" in result.error_message
    # Vynimka nesmie uniknut von.
    assert result.data is None


@pytest.mark.asyncio
async def test_result_serialization():
    item = FakeItem()
    service = FakeService(items=[item], total=1)
    result = await make_handler(service, admin=True).handle(make_request())

    assert result.success is True
    assert result.request_id == "req-1"
    assert result.tool_name == _TOOL
    assert result.data["total"] == 1
    assert result.data["page"] == 1
    assert result.data["page_size"] == 10

    [serialized] = result.data["items"]
    assert serialized["id"] == "c1"
    assert serialized["legal_name"] == "EKOL s.r.o."
    assert serialized["city"] == "Presov"
    assert serialized["country_code"] == "SK"
    assert serialized["seller_capability"] is True


@pytest.mark.asyncio
async def test_empty_result_serialization():
    service = FakeService(items=[], total=0)
    result = await make_handler(service, admin=True).handle(make_request())

    assert result.success is True
    assert result.data["items"] == []
    assert result.data["total"] == 0
