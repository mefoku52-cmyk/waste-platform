"""Contact/inquiry notification email tests (best-effort, mocked transport)."""

from __future__ import annotations

import uuid

import pytest

from tests.integration._company_helpers import (
    clear_overrides,
    client_for,
    complete_page_payload,
    make_company,
    member_user,
)


@pytest.fixture(autouse=True)
def _clean_overrides():
    yield
    clear_overrides()


@pytest.fixture
def sent_emails(monkeypatch):
    calls: list[dict] = []

    async def fake_send(*, to, subject, body, reply_to=None):
        calls.append({"to": to, "subject": subject, "body": body, "reply_to": reply_to})
        return True

    monkeypatch.setattr(
        "app.shared.infrastructure.email.transactional.send_transactional_email",
        fake_send,
    )
    return calls


async def test_landing_contact_sends_email_to_admin(sent_emails):
    async with client_for(None) as client:
        r = await client.post(
            "/api/v1/events/contact",
            json={
                "name": "Ján Test",
                "email": "jan@example.com",
                "company": "Test s.r.o.",
                "message": "Mám záujem o služby.",
            },
            headers={"x-forwarded-for": "10.0.0.1"},
        )
    assert r.status_code == 200, r.text
    assert sent_emails, "admin notification was not sent"
    assert all(call["reply_to"] == "jan@example.com" for call in sent_emails)
    assert any("Mám záujem o služby." in call["body"] for call in sent_emails)


async def test_landing_contact_email_failure_does_not_break(sent_emails, monkeypatch):
    async def boom(*args, **kwargs):
        raise RuntimeError("smtp down")

    monkeypatch.setattr(
        "app.shared.infrastructure.email.transactional.send_transactional_email",
        boom,
    )
    async with client_for(None) as client:
        r = await client.post(
            "/api/v1/events/contact",
            json={
                "name": "Fail Test",
                "email": "fail@example.com",
                "message": "Test zlyhania.",
            },
            headers={"x-forwarded-for": "10.0.0.2"},
        )
    assert r.status_code == 200


async def test_public_company_contact_sends_to_public_email(sent_emails):
    company_id = await make_company()
    admin = member_user(uuid.uuid4(), company_id, role="owner")
    async with client_for(admin) as client:
        await client.put(
            f"/api/v1/companies/{company_id}/page",
            json=complete_page_payload(slug=f"kontakt-{uuid.uuid4().hex[:8]}"),
        )
        pub = await client.post(f"/api/v1/companies/{company_id}/page/publish")
        assert pub.status_code == 200, pub.text
        slug = pub.json()["data"]["slug"]

    async with client_for(None) as client:
        r = await client.post(
            f"/api/v1/public/company-pages/{slug}/contact",
            json={
                "name": "Zákazník",
                "email": "zakaznik@example.com",
                "phone": "+421900123456",
                "message": "Prosím o cenovú ponuku.",
            },
            headers={"x-forwarded-for": "10.0.0.3"},
        )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    assert any(call["to"] == "info@eko.example" for call in sent_emails)
    assert all(call["reply_to"] == "zakaznik@example.com" for call in sent_emails)


async def test_inquiry_notifies_seller_with_buyer_reply_to(sent_emails):
    from app.modules.listings.infrastructure.models import ListingsModel
    from app.shared.infrastructure.db.session import async_session_factory

    seller_id = await make_company(email="predajca@example.com")
    buyer_id = await make_company()
    listing_id = uuid.uuid4()
    async with async_session_factory() as session:
        session.add(
            ListingsModel(
                id=listing_id,
                title="Recyklovaný plast",
                material_type="plast",
                quantity=10,
                unit="t",
                currency="EUR",
                condition="novy",
                location="Bratislava",
                status="published",
                company_id=uuid.UUID(seller_id),
            )
        )
        await session.commit()

    buyer = member_user(uuid.uuid4(), buyer_id, role="owner")
    async with client_for(buyer) as client:
        r = await client.post(
            "/api/v1/inquiries",
            json={
                "listingId": str(listing_id),
                "companyId": buyer_id,
                "message": "Mám záujem.",
                "contactEmail": "kupujuci@example.com",
            },
        )
    assert r.status_code == 201, r.text
    assert any(call["to"] == "predajca@example.com" for call in sent_emails)
    assert all(call["reply_to"] == "kupujuci@example.com" for call in sent_emails)
