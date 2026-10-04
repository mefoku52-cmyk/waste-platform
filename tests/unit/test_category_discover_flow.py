"""Tests for run_category_discover — ZS category discovery pipeline.

discover_from_category aj SqlAlchemyOutreachCandidateRepository sa importuju
lokalne vo vnutri run_category_discover, takze ich patchujeme v ich
zdrojovych moduloch.
"""

import pytest

from app.modules.lead_finder.application.services import daily_discover
from app.modules.lead_finder.application.services.zs_category_discovery import (
    DiscoveredCompany,
)
from app.modules.lead_finder.infrastructure.persistence import repositories as repo_mod


class FakeRepo:
    """In-memory nahrada SqlAlchemyOutreachCandidateRepository."""

    stored: list[dict] = []
    preload: list[dict] = []

    def __init__(self, _session):
        # preload simuluje riadky, ktore uz su v DB pred behom
        self.stored = list(type(self).preload)
        type(self).stored = self.stored

    async def find_by_email(self, email: str):
        cleaned = (email or "").strip().lower()
        for row in self.stored:
            if (row["email"] or "").strip().lower() == cleaned:
                return row
        return None

    async def create_from_discovery(self, **kwargs):
        self.stored.append(kwargs)
        return kwargs


@pytest.fixture(autouse=True)
def reset_fake_repo():
    FakeRepo.stored = []
    FakeRepo.preload = []
    yield
    FakeRepo.stored = []
    FakeRepo.preload = []


def _company(name: str, email: str, city: str | None = None) -> DiscoveredCompany:
    return DiscoveredCompany(
        company_name=name,
        email=email,
        city=city,
        source_url="https://www.zlatestranky.sk/firmy/x/H123/slug/",
    )


def _patch(monkeypatch, per_slug: dict[str, list[DiscoveredCompany]]):
    """Nahrad discover_from_category + repository; vrat zoznam volani."""
    calls: list[tuple[str, int]] = []

    def fake_discover(category_slug: str, page: int = 1, max_pages: int = 20):
        calls.append((category_slug, max_pages))
        return per_slug.get(category_slug, [])

    monkeypatch.setattr(
        "app.modules.lead_finder.application.services.zs_category_discovery.discover_from_category",
        fake_discover,
    )
    monkeypatch.setattr(repo_mod, "SqlAlchemyOutreachCandidateRepository", FakeRepo)
    return calls


async def test_run_category_discover_saves_new_candidates(monkeypatch):
    calls = _patch(
        monkeypatch,
        {
            "odpady": [_company("Alfa s.r.o.", "alfa@alfa.sk", "Trnava")],
            "Recyklácia": [_company("Beta s.r.o.", "beta@beta.sk")],
        },
    )

    result = await daily_discover.run_category_discover(
        session=object(),
        categories=["odpady", "Recyklácia"],
        max_pages_per_category=5,
    )

    assert result["saved"] == 2
    assert result["duplicates"] == 0
    assert result["discovered"] == 2
    assert result["per_category"] == {"odpady": 1, "Recyklácia": 1}
    assert calls == [("odpady", 5), ("Recyklácia", 5)]
    assert [r["email"] for r in FakeRepo.stored] == ["alfa@alfa.sk", "beta@beta.sk"]


async def test_run_category_discover_dedupes_within_run(monkeypatch):
    # Ten isty email v dvoch firmach / kategoriach + prazdny email.
    _patch(
        monkeypatch,
        {
            "odpady": [
                _company("Alfa s.r.o.", "Alfa@Alfa.sk"),
                _company("Alfa pobočka", "alfa@alfa.sk"),  # case dup v ramci behu
                _company("Bez emailu", ""),  # prazdny email sa preskoci
            ],
            "kovový odpad": [_company("Alfa znova", "ALFA@ALFA.SK")],  # dup medzi kat.
        },
    )

    result = await daily_discover.run_category_discover(
        session=object(),
        categories=["odpady", "kovový odpad"],
    )

    assert result["saved"] == 1
    assert result["discovered"] == 1
    assert len(FakeRepo.stored) == 1
    assert FakeRepo.stored[0]["email"] == "Alfa@Alfa.sk"


async def test_run_category_discover_handles_empty_categories(monkeypatch):
    calls = _patch(monkeypatch, {})

    result = await daily_discover.run_category_discover(
        session=object(),
        categories=[],
    )

    assert result == {
        "discovered": 0,
        "saved": 0,
        "duplicates": 0,
        "per_category": {},
    }
    assert calls == []
    assert FakeRepo.stored == []


async def test_run_category_discover_reports_db_duplicates(monkeypatch):
    """Kandidat, ktory uz je v DB, sa nerata ako saved."""
    _patch(
        monkeypatch,
        {"odpady": [_company("Gama s.r.o.", "gama@gama.sk")]},
    )

    # Predbezne napln repo, aby find_by_email nasiel zhodu.
    FakeRepo.preload = [{"email": "gama@gama.sk", "company_name": "Gama s.r.o."}]

    result = await daily_discover.run_category_discover(
        session=object(),
        categories=["odpady"],
    )

    assert result["saved"] == 0
    assert result["duplicates"] == 1
    assert result["discovered"] == 1
    assert len(FakeRepo.stored) == 1  # ziaden novy zapis


async def test_run_category_discover_survives_category_failure(monkeypatch):
    """Zlyhanie jednej kategorie nesmie zhodiť cely beh."""

    def boom(category_slug: str, page: int = 1, max_pages: int = 20):
        if category_slug == "odpady":
            raise RuntimeError("ZS timeout")
        return [_company("Delta s.r.o.", "delta@delta.sk")]

    monkeypatch.setattr(
        "app.modules.lead_finder.application.services.zs_category_discovery.discover_from_category",
        boom,
    )
    monkeypatch.setattr(repo_mod, "SqlAlchemyOutreachCandidateRepository", FakeRepo)

    result = await daily_discover.run_category_discover(
        session=object(),
        categories=["odpady", "Recyklácia"],
    )

    assert result["saved"] == 1
    assert result["per_category"] == {"odpady": 0, "Recyklácia": 1}
