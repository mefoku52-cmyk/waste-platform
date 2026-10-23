"""Shared helpers for company_pages / company_reviews integration tests.

Seeds real rows into the SQLite test DB (session-scoped, file-based) and
provides a dependency-overridden async HTTP client. Auth is faked via
``dependency_overrides[require_current_user]`` so tests exercise the real
endpoint logic (authorization, validation, DB) without issuing tokens.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.shared.infrastructure.db.session import async_session_factory
from app.shared.presentation.auth_dependencies import require_current_user


class FakeUser:
    def __init__(self, user_id=None, *, memberships=(), email="user@example.com", roles=()):
        self.id = str(user_id or uuid.uuid4())
        self.email = email
        self.memberships = list(memberships)
        self.roleCodes = list(roles)


def member_user(user_id, company_id, role="owner", **kw):
    return FakeUser(
        user_id,
        memberships=[{"companyId": str(company_id), "membershipRole": role}],
        **kw,
    )


def platform_admin(user_id=None, **kw):
    return FakeUser(user_id, roles=["platform_admin"], **kw)


def client_for(user: FakeUser | None):
    """Async HTTP client with auth overridden to ``user`` (or none → 401 path)."""
    if user is None:
        app.dependency_overrides.pop(require_current_user, None)
    else:
        app.dependency_overrides[require_current_user] = lambda: user
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


def clear_overrides():
    app.dependency_overrides.pop(require_current_user, None)


# Registry of companies created by tests, cleaned up after each test so the
# shared session-scoped test DB stays consistent with tests that assert an
# empty ``companies`` table.
CREATED_COMPANY_IDS: list[str] = []


async def cleanup_created():
    """Odstráni riadky vytvorené testami (a nadväzné záznamy) z test DB."""
    ids = list(CREATED_COMPANY_IDS)
    CREATED_COMPANY_IDS.clear()
    if not ids:
        return
    from sqlalchemy import delete

    from app.modules.companies.infrastructure.models import CompanyModel
    from app.modules.company_memberships.infrastructure.models import (
        CompanyMembershipModel,
    )
    from app.modules.company_pages.infrastructure.models import (
        CompanyPageModel,
        CompanyPhotoModel,
    )
    from app.modules.company_reviews.infrastructure.models import CompanyReviewModel
    from app.modules.events.infrastructure.models import ActivityEventModel
    from app.modules.inquiries.infrastructure.models import InquiryModel
    from app.modules.listings.infrastructure.models import ListingsModel

    async with async_session_factory() as session:
        for model in (
            CompanyPhotoModel,
            CompanyPageModel,
            CompanyReviewModel,
            CompanyMembershipModel,
        ):
            await session.execute(delete(model).where(model.company_id.in_(ids)))
        await session.execute(
            delete(ActivityEventModel).where(ActivityEventModel.company_id.in_(ids))
        )
        # inquiries/listings.company_id je UUID typ → konvertuj
        inquiry_uuids = [uuid.UUID(i) for i in ids]
        await session.execute(
            delete(InquiryModel).where(InquiryModel.company_id.in_(inquiry_uuids))
        )
        await session.execute(
            delete(ListingsModel).where(ListingsModel.company_id.in_(inquiry_uuids))
        )
        await session.execute(delete(CompanyModel).where(CompanyModel.id.in_(ids)))
        await session.commit()


async def make_company(*, status="verified", **over):
    from app.modules.companies.infrastructure.models import CompanyModel

    cid = str(uuid.uuid4())
    CREATED_COMPANY_IDS.append(cid)
    now = datetime.now()
    fields = {
        "id": cid,
        "status": status,
        "legal_name": "Test s.r.o.",
        "trading_name": "Test Firma",
        "registration_number": "reg-" + uuid.uuid4().hex[:12],
        "tax_identifier": None,
        "vat_identifier": None,
        "subscription_tier": "free",
        "company_type": "seller",
        "email": None,
        "phone": None,
        "website_url": None,
        "logo_url": None,
        "country_code": "SK",
        "address_line_1": "Hlavna 1",
        "address_line_2": None,
        "city": "Bratislava",
        "postal_code": "81101",
        "latitude": None,
        "longitude": None,
        "seller_capability": True,
        "buyer_capability": False,
        "logistics_capability": False,
        "accepted_material_types": None,
        "created_at": now,
        "updated_at": now,
    }
    fields.update(over)
    async with async_session_factory() as session:
        session.add(CompanyModel(**fields))
        await session.commit()
    return cid


async def make_inquiry(company_id, user_id, *, status="answered"):
    from app.modules.inquiries.infrastructure.models import InquiryModel

    now = datetime.now()
    async with async_session_factory() as session:
        session.add(
            InquiryModel(
                id=uuid.uuid4(),
                listing_id=uuid.uuid4(),
                company_id=uuid.UUID(str(company_id)),
                message="Dobry den",
                contact_email="buyer@example.com",
                status=status,
                created_at=now,
                updated_at=now,
                created_by_user_id=uuid.UUID(str(user_id)),
            )
        )
        await session.commit()


def complete_page_payload(**over):
    payload = {
        "displayName": "Eko Odpad s.r.o.",
        "aboutShort": "Zber a spracovanie odpadu.",
        "publicEmail": "info@eko.example",
        "publicPhone": "+421900111222",
        "services": "Zber papiera, plastu a skla.",
    }
    payload.update(over)
    return payload
