# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Module 8: Multi-photo + Document Versioning + ACL

### Status: PARTIAL

#### Done
- Domain models + PhotoACL
- SQLAlchemy model + repository
- Proposed migration
- Router wired to ListingPhotoRepository
- Membership ACL via require_company_member (after resolving company from listing)
- MIME/size validation
- Unit tests
- Slovak documentation

#### Remaining
- Real listing → company resolution (currently placeholder returns None)
- Content-level file validation
- Document versioning
- Integration tests with real DB

#### Files
- presentation/photos_router.py (repository + ACL wiring)
- infrastructure/repositories/listing_photo_repository.py
- docs/platform-extensions/module-8-photos.md