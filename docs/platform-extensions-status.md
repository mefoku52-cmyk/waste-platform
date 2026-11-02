# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Module 8: Multi-photo + Document Versioning + ACL

### Status: PARTIAL

#### Done
- Domain + PhotoACL
- SQLAlchemy model + repository
- Proposed migration
- Router wired to repository
- Owning company resolved from listings table
- Membership ACL via require_company_member
- MIME + size validation
- Magic-byte validation wired into POST (is_valid_image_content)
- Document version model
- Unit tests (ACL, MIME, magic-bytes)
- Slovak documentation

#### Remaining
- Full stream-based size enforcement during upload
- Document versioning endpoints
- Integration tests with real DB (cross-tenant + invalid upload leaves no record)

#### Files updated this step
- presentation/photos_router.py (magic-byte check)
- tests/unit/test_magic_bytes.py