"""Testy pre upload pravidlá a UUID konzistenciu."""

from uuid import UUID, uuid4

from app.modules.listings.domain.photos import ListingPhoto, PhotoACL
from app.modules.listings.presentation.photos_router import ALLOWED_MIME, MAX_SIZE_BYTES


def test_uuid_consistency():
    company = uuid4()
    photo = ListingPhoto(
        id=uuid4(),
        listing_id=uuid4(),
        company_id=company,
        storage_key="test",
        mime_type="image/jpeg",
        size_bytes=1024,
        created_at=None,
        created_by=uuid4(),
    )
    assert isinstance(photo.company_id, UUID)
    assert PhotoACL.can_read({company}, photo)


def test_mime_and_size_constants():
    assert "image/jpeg" in ALLOWED_MIME
    assert MAX_SIZE_BYTES == 10 * 1024 * 1024