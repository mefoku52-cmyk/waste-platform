import pytest

from app.modules.lead_finder.application.services import daily_discover


class FakeResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class FakeSession:
    async def execute(self, _query):
        return FakeResult([])


class FakeCandidate:
    def __init__(self, candidate_id, company_name, ico, city, industry, email=None):
        self.id = candidate_id
        self.company_name = company_name
        self.ico = ico
        self.city = city
        self.industry = industry
        self.email = email


class FakeRepository:
    last_instance: "FakeRepository | None" = None

    def __init__(self, session):
        self.session = session
        self.created = []
        self.emails = []
        self.drafts = []
        FakeRepository.last_instance = self

    async def create(self, **kwargs):
        candidate = FakeCandidate(
            candidate_id=len(self.created) + 1,
            company_name=kwargs["company_name"],
            ico=kwargs["ico"],
            city=kwargs.get("city"),
            industry=kwargs.get("industry"),
            email=kwargs.get("email"),
        )
        self.created.append(candidate)
        return candidate

    async def update_email(self, *, candidate_id, email):
        self.emails.append((candidate_id, email))

    async def update_draft(self, *, candidate_id, subject, body):
        self.drafts.append((candidate_id, subject, body))


class FakeWebsiteFinder:
    result = "https://example.sk"

    def __init__(self):
        pass

    async def find_website(self, *, company_name, city):
        return self.result


class FakeEmailFinder:
    result = None
    closed = False

    def __init__(self):
        FakeEmailFinder.closed = False

    async def find_email_for_company(self, website, *, company_name):
        return self.result

    async def close(self):
        FakeEmailFinder.closed = True


class FakeMail:
    subject = "Ponuka spolupráce"
    body = "Dobrý deň, radi by sme vám predstavili CMEP."


class FakeDrafter:
    async def draft(self, **kwargs):
        return FakeMail()


@pytest.mark.asyncio
async def test_daily_discover_uses_directory_fallback_and_persists_email(monkeypatch):
    rows = [
        {
            "legalName": "Test Recycling s.r.o.",
            "ico": "12345678",
            "city": "Presov",
            "activity": "recyklacia plastov",
        }
    ]

    directory_calls = []

    def fake_search_rpo(*, limit, only_active, **query):
        assert limit == 10
        assert only_active is True
        return rows

    def fake_lookup_public_email(company_name, city, ico):
        directory_calls.append((company_name, city, ico))
        return "info@testrecycling.sk"

    monkeypatch.setattr(daily_discover, "search_rpo", fake_search_rpo)
    monkeypatch.setattr(
        daily_discover,
        "SqlAlchemyOutreachCandidateRepository",
        FakeRepository,
    )
    monkeypatch.setattr(daily_discover, "WebsiteFinder", FakeWebsiteFinder)
    monkeypatch.setattr(daily_discover, "AsyncLegalEmailFinder", FakeEmailFinder)
    monkeypatch.setattr(
        daily_discover,
        "lookup_public_email",
        fake_lookup_public_email,
    )

    FakeEmailFinder.result = None

    result = await daily_discover.run_daily_discover(
        FakeSession(),
        limit=1,
        draft=False,
    )
    assert result is not None

    repo = FakeRepository.last_instance
    assert repo is not None

    assert result["picked"] == 1
    assert result["created"] == 1
    assert result["emails_found"] == 1
    assert result["drafted"] == 0

    assert directory_calls == [("Test Recycling s.r.o.", "Presov", "12345678")]
    assert repo.emails == [(1, "info@testrecycling.sk")]
    assert repo.drafts == []
    assert result["items"][0]["email"] == "info@testrecycling.sk"
    assert FakeEmailFinder.closed is True


@pytest.mark.asyncio
async def test_daily_discover_never_invents_email(monkeypatch):
    rows = [
        {
            "legalName": "No Email s.r.o.",
            "ico": "22345678",
            "city": "Kosice",
            "activity": "spracovanie odpadu",
        }
    ]

    monkeypatch.setattr(
        daily_discover,
        "search_rpo",
        lambda **kwargs: rows,
    )
    monkeypatch.setattr(
        daily_discover,
        "SqlAlchemyOutreachCandidateRepository",
        FakeRepository,
    )
    monkeypatch.setattr(daily_discover, "WebsiteFinder", FakeWebsiteFinder)
    monkeypatch.setattr(daily_discover, "AsyncLegalEmailFinder", FakeEmailFinder)
    monkeypatch.setattr(
        daily_discover,
        "lookup_public_email",
        lambda company_name, city, ico: None,
    )

    FakeEmailFinder.result = None

    result = await daily_discover.run_daily_discover(
        FakeSession(),
        limit=1,
        draft=False,
    )
    assert result is not None

    repo = FakeRepository.last_instance
    assert repo is not None

    assert result["emails_found"] == 0
    assert repo.emails == []
    assert result["items"][0]["email"] is None


@pytest.mark.asyncio
async def test_daily_discover_saves_personalized_draft(monkeypatch):
    rows = [
        {
            "legalName": "Plastic Works s.r.o.",
            "ico": "32345678",
            "city": "Zilina",
            "activity": "spracovanie plastov",
        }
    ]

    draft_calls = []

    monkeypatch.setattr(
        daily_discover,
        "search_rpo",
        lambda **kwargs: rows,
    )
    monkeypatch.setattr(
        daily_discover,
        "SqlAlchemyOutreachCandidateRepository",
        FakeRepository,
    )
    monkeypatch.setattr(daily_discover, "WebsiteFinder", FakeWebsiteFinder)
    monkeypatch.setattr(daily_discover, "AsyncLegalEmailFinder", FakeEmailFinder)
    monkeypatch.setattr(
        daily_discover,
        "lookup_public_email",
        lambda company_name, city, ico: None,
    )

    class RecordingDrafter:
        async def draft(self, **kwargs):
            draft_calls.append(kwargs)
            return FakeMail()

    monkeypatch.setattr(daily_discover, "EmailDrafter", RecordingDrafter)

    FakeEmailFinder.result = None

    result = await daily_discover.run_daily_discover(
        FakeSession(),
        limit=1,
        draft=True,
    )
    assert result is not None

    repo = FakeRepository.last_instance
    assert repo is not None

    assert result["drafted"] == 1
    assert len(repo.drafts) == 1

    assert draft_calls[0]["company_name"] == "Plastic Works s.r.o."
    assert draft_calls[0]["city"] == "Zilina"
    assert draft_calls[0]["industry"] == "spracovanie plastov"
    assert "spracovanie plastov" in draft_calls[0]["reason"]
    assert "Zilina" in draft_calls[0]["reason"]


@pytest.mark.asyncio
async def test_daily_discover_caps_limit_at_50(monkeypatch):
    rows = [
        {
            "legalName": f"Company {i} s.r.o.",
            "ico": f"{10000000 + i:08d}",
            "city": "Bratislava",
            "activity": "odpad",
        }
        for i in range(60)
    ]

    calls = []

    def fake_search_rpo(*, limit, only_active, **query):
        calls.append(limit)
        return rows

    monkeypatch.setattr(daily_discover, "search_rpo", fake_search_rpo)
    monkeypatch.setattr(
        daily_discover,
        "SqlAlchemyOutreachCandidateRepository",
        FakeRepository,
    )
    monkeypatch.setattr(daily_discover, "WebsiteFinder", FakeWebsiteFinder)
    monkeypatch.setattr(daily_discover, "AsyncLegalEmailFinder", FakeEmailFinder)
    monkeypatch.setattr(
        daily_discover,
        "lookup_public_email",
        lambda company_name, city, ico: None,
    )

    FakeEmailFinder.result = None

    result = await daily_discover.run_daily_discover(
        FakeSession(),
        limit=999,
        draft=False,
    )
    assert result is not None

    assert result["picked"] == 50
    assert result["created"] == 50
    last_repository = FakeRepository.last_instance
    assert last_repository is not None
    assert len(last_repository.created) == 50
    assert calls
    assert all(value == 10 for value in calls)
