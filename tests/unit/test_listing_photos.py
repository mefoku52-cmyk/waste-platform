"""Unit tests for photo upload validation and ACL."""

from uuid import uuid4

import pytest

from app.modules.listings.domain.photos import ListingPhoto, PhotoACL
from app.modules.listings.presentation.photos_router import ALLOWED_MIME, MAX_SIZE_BYTES


def test_allowed_mime():
    assert "image/jpeg" in ALLOWED_MIME
    assert "image/png" in ALLOWED_MIME
    assert "application/pdf" not in ALLOWED_MIME


def test_max_size():
    assert MAX_SIZE_BYTES == 10 * 1024 * 1024


def test_acl_can_read():
    company = uuid4()
    photo = ListingPhoto(
        id=uuid4(),
        listing_id=uuid4(),
        company_id=company,
        storage_key="k",
        mime_type="image/jpeg",
        size_bytes=100,
        created_at=None,
        created_by=uuid4(),
    )
    assert PhotoACL.can_read({company}, photo) is True
    assert PhotoACL.can_read({uuid4()}, photo) is False


def test_acl_can_write():
    company = uuid4()
    photo = ListingPhoto(
        id=uuid4(),
        listing_id=uuid4(),
        company_id=company,
        storage_key="k",
        mime_type="image/jpeg",
        size_bytes=100,
        created_at=None,
        created_by=uuid4(),
    )
    assert PhotoACL.can_write({company}, photo) is True
    assert PhotoACL.can_write(set(), photo) is False