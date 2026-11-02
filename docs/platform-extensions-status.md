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
- Stream-based size limit helper (_read_and_validate_stream)
- Document version model
- Unit tests (ACL, MIME, magic-bytes, stream rules)
- Slovak documentation

#### Remaining
- Full integration of _read_and_validate_stream into the public POST (requires UploadFile)
- Document versioning endpoints
- Integration tests with real DB (cross-tenant + invalid upload leaves no record)

#### Files updated this step
- presentation/photos_router.py (stream helper)
- tests/unit/test_stream_validation.py