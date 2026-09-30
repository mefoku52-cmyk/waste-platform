"""backfill_emails - service s FakeRepo + mock website/email finder."""

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.lead_finder.application.services.backfill_emails import (
    DEFAULT_LIMIT,
    backfill_emails,
)


def test_default_limit_is_35():
    assert DEFAULT_LIMIT == 35


class FakeScalar:
    """Napodobňuje Result.scalars().all() z SQLAlchemy."""

    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class FakeModel:
    def __init__(self, cid, name, city, ico=None):
        self.id = cid
        self.company_name = name
        self.city = city
        self.ico = ico


class FakeSession:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return FakeScalar(self._rows)


@pytest.mark.asyncio
async def test_backfill_empty_session():
    """Prazdny vysledok -> vsetko 0."""
    session = FakeSession([])
    with (
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.WebsiteFinder"
        ) as MockWF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.AsyncLegalEmailFinder"
        ) as MockEF,
    ):
        MockWF.return_value.find_website = AsyncMock(return_value=None)
        MockEF.return_value.find_email_for_company = AsyncMock(return_value=None)
        MockEF.return_value.close = AsyncMock()
        result = await backfill_emails(session, limit=35)

    assert result["ok"] is True
    assert result["processed"] == 0
    assert result["found"] == 0
    assert result["failed"] == 0


@pytest.mark.asyncio
async def test_backfill_no_website():
    row = FakeModel("id-1", "Firma s.r.o.", "Bratislava", "12345678")
    session = FakeSession([row])

    with (
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.WebsiteFinder"
        ) as MockWF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.AsyncLegalEmailFinder"
        ) as MockEF,
    ):
        MockWF.return_value.find_website = AsyncMock(return_value=None)
        MockEF.return_value.find_email_for_company = AsyncMock(return_value=None)
        MockEF.return_value.close = AsyncMock()
        result = await backfill_emails(session, limit=35)

    assert result["processed"] == 1
    assert result["no_website"] == 1
    assert result["found"] == 0


@pytest.mark.asyncio
async def test_backfill_website_no_email():
    row = FakeModel("id-1", "Firma s.r.o.", "Bratislava")
    session = FakeSession([row])

    with (
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.WebsiteFinder"
        ) as MockWF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.AsyncLegalEmailFinder"
        ) as MockEF,
    ):
        MockWF.return_value.find_website = AsyncMock(return_value="https://firma.sk")
        MockEF.return_value.find_email_for_company = AsyncMock(return_value=None)
        MockEF.return_value.close = AsyncMock()
        result = await backfill_emails(session, limit=35)

    assert result["processed"] == 1
    assert result["no_email_on_website"] == 1
    assert result["found"] == 0


@pytest.mark.asyncio
async def test_backfill_found_email():
    row = FakeModel("id-1", "Firma s.r.o.", "Bratislava")

    class FakeRepo:
        def __init__(self, session):
            self.updated = []

        async def update_email(self, *, candidate_id, email):
            self.updated.append((candidate_id, email))

    session = FakeSession([row])

    with (
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.WebsiteFinder"
        ) as MockWF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.AsyncLegalEmailFinder"
        ) as MockEF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.SqlAlchemyOutreachCandidateRepository",
            FakeRepo,
        ),
    ):
        MockWF.return_value.find_website = AsyncMock(return_value="https://firma.sk")
        MockEF.return_value.find_email_for_company = AsyncMock(return_value="info@firma.sk")
        MockEF.return_value.close = AsyncMock()
        result = await backfill_emails(session, limit=35)

    assert result["processed"] == 1
    assert result["found"] == 1


@pytest.mark.asyncio
async def test_backfill_finder_exception():
    row = FakeModel("id-1", "Firma s.r.o.", "Bratislava")
    session = FakeSession([row])

    with (
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.WebsiteFinder"
        ) as MockWF,
        patch(
            "app.modules.lead_finder.application.services.backfill_emails.AsyncLegalEmailFinder"
        ) as MockEF,
    ):
        MockWF.return_value.find_website = AsyncMock(side_effect=Exception("boom"))
        MockEF.return_value.find_email_for_company = AsyncMock(return_value=None)
        MockEF.return_value.close = AsyncMock()
        result = await backfill_emails(session, limit=35)

    assert result["processed"] == 1
    assert result["failed"] == 1
