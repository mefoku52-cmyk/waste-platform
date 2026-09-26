"""BatchDrafter tests – never exceeds MAX_BATCH."""

from __future__ import annotations

import pytest

from app.modules.lead_finder.application.services.batch_drafter import (
    BatchDrafter,
    CompanyInput,
)
from app.modules.lead_finder.application.services.email_drafter import DraftedEmail


class _FakeDrafter:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def draft(self, *, company_name, city, industry, reason, early_bird):
        self.calls.append(company_name)
        return DraftedEmail(
            subject=f"Subject for {company_name}",
            body=f"Body for {company_name}",
        )


@pytest.mark.asyncio
async def test_batch_uses_fake_drafter(monkeypatch) -> None:
    fake = _FakeDrafter()
    bd = BatchDrafter()
    bd._drafter = fake  # type: ignore[assignment]

    items = await bd.draft_batch(
        companies=[
            CompanyInput(company_name="A s.r.o.", city="Ulic"),
            CompanyInput(company_name="B s.r.o.", city="Snina"),
        ],
        early_bird=True,
    )
    assert len(items) == 2
    assert items[0].subject == "Subject for A s.r.o."
    assert fake.calls == ["A s.r.o.", "B s.r.o."]


@pytest.mark.asyncio
async def test_batch_respects_max_30(monkeypatch) -> None:
    fake = _FakeDrafter()
    bd = BatchDrafter()
    bd._drafter = fake  # type: ignore[assignment]

    companies = [CompanyInput(company_name=f"F{i}") for i in range(50)]
    items = await bd.draft_batch(companies=companies, early_bird=False)
    assert len(items) == 30
    assert len(fake.calls) == 30


@pytest.mark.asyncio
async def test_batch_skips_failed_draft(monkeypatch) -> None:
    class _SometimesFail:
        def __init__(self) -> None:
            self.count = 0

        async def draft(self, *, company_name, city, industry, reason, early_bird):
            self.count += 1
            if self.count == 2:
                raise RuntimeError("boom")
            return DraftedEmail(subject="s", body="b")

    fake = _SometimesFail()
    bd = BatchDrafter()
    bd._drafter = fake  # type: ignore[assignment]

    items = await bd.draft_batch(
        companies=[
            CompanyInput(company_name="A"),
            CompanyInput(company_name="B"),
            CompanyInput(company_name="C"),
        ],
        early_bird=False,
    )
    assert len(items) == 2
    assert [i.company_name for i in items] == ["A", "C"]
