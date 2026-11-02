# Module 8 – Multi-photo + Document Versioning + ACL

## Overview
Company-scoped photo management for listings.

## ACL
- `PhotoACL.can_read` / `can_write` check that the user's company memberships include the photo's `company_id`.
- Tenant isolation is enforced at the domain level.

## Upload rules
- Allowed MIME: `image/jpeg`, `image/png`, `image/webp`
- Max size: 10 MB

## Files
- `app/modules/listings/domain/photos.py` – domain + ACL
- `app/modules/listings/infrastructure/models/listing_photo.py` – SQLAlchemy model
- `app/modules/listings/infrastructure/repositories/listing_photo_repository.py` – repository
- `app/modules/listings/presentation/photos_router.py` – router with validation
- `docs/platform-extensions/migrations/proposed_listing_photos.py` – migration proposal
- `tests/unit/test_listing_photos.py` – ACL tests
- `tests/unit/test_photo_upload_rules.py` – MIME/size tests

## Integration
Router is not yet registered in `api_router.py` (protected). Proposed:
```python
from app.modules.listings.presentation.photos_router import router as photos_router
api_router.include_router(photos_router)
```