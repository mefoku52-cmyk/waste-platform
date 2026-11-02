# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Module 8: Multi-photo + Document Versioning + ACL

### Status: PARTIAL

#### Done
- Domain models with company_id and PhotoACL
- SQLAlchemy model (ListingPhotoModel)
- Repository (ListingPhotoRepository)
- Proposed migration (docs/platform-extensions/migrations/proposed_listing_photos.py)
- Router with MIME type and size checks (max 10 MB, jpeg/png/webp)

#### Remaining
- Full persistence wiring in router
- Document versioning implementation
- Integration with existing listings service
- Tests

#### Files
- domain/photos.py
- infrastructure/models/listing_photo.py
- infrastructure/repositories/listing_photo_repository.py
- presentation/photos_router.py
- docs/platform-extensions/migrations/proposed_listing_photos.py