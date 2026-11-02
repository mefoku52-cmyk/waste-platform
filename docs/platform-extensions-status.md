# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions
HEAD: cc067f65 (will update after this commit)

## Module 8: Multi-photo + Document Versioning + ACL

### Status: PARTIAL

#### Done
- Domain + PhotoACL
- SQLAlchemy model + repository
- Proposed migration
- Router wired to ListingPhotoRepository
- Owning company resolved from `listings` table (trusted)
- Membership ACL via `require_company_member`
- MIME + size validation
- Unit tests
- Slovak documentation

#### Remaining
- Magic-byte content verification
- Document versioning
- Integration tests with real DB (cross-tenant)

#### Files
- `app/modules/listings/presentation/photos_router.py` (updated)
- `docs/platform-extensions/module-8-photos.md` (updated)