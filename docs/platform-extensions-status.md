# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Module 7: AI Approval Workflow
Status: PARTIAL (real context wired, create path done)

## Module 8: Multi-photo + Document Versioning + ACL
Status: PARTIAL

### Done
- Domain models with company_id
- Simple company-scoped ACL (PhotoACL.can_read / can_write)
- Basic router skeleton

### Remaining
- Full repository and DB model
- Upload endpoint with MIME/size checks
- Document versioning
- Proposed migration
- Integration with existing listings

### Files
- app/modules/listings/domain/photos.py
- app/modules/listings/presentation/photos_router.py