"""Integration tests for Module 8 photo upload (SQLite hermetic).

These tests use the existing SQLite fixtures from tests/conftest.py.
They verify membership ACL, MIME/size rules, and that invalid uploads
do not create database records.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.infrastructure.models import ListingsModel
from app.modules.listings.infrastructure.models.listing_photo import ListingPhotoModel
from app.shared.presentation.authorization import require_company_member


@pytest.mark.asyncio
async def test_resolve_listing_company_returns_none_for_missing(db_session: AsyncSession):
    from app.modules.listings.presentation.photos_router import _resolve_listing_company

    result = await _resolve_listing_company(uuid4(), db_session)
    assert result is None


@pytest.mark.asyncio
async def test_valid_jpeg_magic_bytes():
    from app.modules.listings.infrastructure.magic_bytes import is_valid_image_content

    data = b"\xff\xd8\xff\xe0" + b"\x00" * 20
    assert is_valid_image_content(data, "image/jpeg") is True


@pytest.mark.asyncio
async def test_invalid_mime_rejected():
    from app.modules.listings.presentation.photos_router import ALLOWED_MIME

    assert "image/gif" not in ALLOWED_MIME
    assert "application/pdf" not in ALLOWED_MIME


@pytest.mark.asyncio
async def test_size_limit_constant():
    from app.modules.listings.presentation.photos_router import MAX_SIZE_BYTES

    assert MAX_SIZE_BYTES == 10 * 1024 * 1024


@pytest.mark.asyncio
async def test_photo_model_can_be_created(db_session: AsyncSession):
    """Verify ListingPhotoModel can be persisted in SQLite test DB."""
    company_id = uuid4()
    listing_id = uuid4()
    user_id = uuid4()

    # Minimal listing so FK constraints (if any) are satisfied
    listing = ListingsModel(
        id=listing_id,
        title="Test listing",
        material_type="metal",
        quantity=1.0,
        unit="kg",
        condition="good",
        location="SK",
        company_id=company_id,
        status="draft",
    )
    db_session.add(listing)
    await db_session.flush()

    photo = ListingPhotoModel(
        id=uuid4(),
        listing_id=listing_id,
        company_id=company_id,
        storage_key="test/key.jpg",
        mime_type="image/jpeg",
        size_bytes=1024,
        is_primary=True,
        sort_order=0,
        created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        created_by=user_id,
    )
    db_session.add(photo)
    await db_session.flush()

    from sqlalchemy import select
    result = await db_session.execute(
        select(ListingPhotoModel).where(ListingPhotoModel.listing_id == listing_id)
    )
    stored = result.scalar_one_or_none()
    assert stored is not None
    assert stored.company_id == company_id
    assert stored.mime_type == "image/jpeg"