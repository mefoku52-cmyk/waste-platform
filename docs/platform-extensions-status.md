# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Module 8: Multi-photo + Document Versioning + ACL

### Status: PARTIAL

#### Done
- Domain models with company_id
- PhotoACL (company-scoped can_read / can_write)
- SQLAlchemy model
- Repository
- Proposed migration
- Router with MIME type and size checks (max 10 MB)
- Unit tests for ACL and upload constraints

#### Remaining
- Full persistence wiring in router (repo.add + ACL check against membership)
- Document versioning
- Integration tests

#### Files
- domain/photos.py
- infrastructure/models/listing_photo.py
- infrastructure/repositories/listing_photo_repository.py
- presentation/photos_router.py
- tests/unit/test_listing_photos.py
- docs/platform-extensions/migrations/proposed_listing_photos.py

#### ACL
Only members of the owning company can read or write photos.