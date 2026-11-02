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
- Magic-byte validation
- Stream-based size limit helper
- Document version model
- Unit tests
- Slovak documentation
- SQLite-based integration test file: tests/integration/test_module8_photos.py

#### Remaining
- Full UploadFile + _read_and_validate_stream wiring in public POST
- Document versioning endpoints
- Real PostgreSQL integration tests (environment not available here)
- Cross-tenant integration scenarios against live DB

#### Test notes
- tests/integration/test_module8_photos.py uses existing SQLite fixtures from tests/conftest.py
- Covers: missing listing, magic-bytes, MIME whitelist, size constant, model persistence