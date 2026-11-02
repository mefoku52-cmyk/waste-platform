# CMEP Platform Extensions – Implementation Status (updated)

Branch: feat/platform-extensions
Base: main @ 834f389

## Modules

### 1. Outbound Webhooks – PARTIAL
- Domain models, HMAC signing, SSRF guard, delivery service, basic router
- Missing: DB persistence, full admin CRUD, tests, migration, event emission from business flows

### 2. Idempotent Command Bus – PARTIAL
- In-memory bus with idempotency key
- Missing: DB-backed store, transaction boundaries, registration of real commands

### 3. Partner OAuth 2.0 – PARTIAL
- Domain models and scopes
- Missing: token issuance/refresh, middleware, client registry, rate limits

### 4. CQRS Light – PARTIAL
- Listings read model (in-memory)
- Missing: other projections, event-driven sync, Redis/materialized view

### 5. Saga / Process Manager – PARTIAL
- Inquiry process manager (in-memory)
- Missing: persistence, permission re-checks, recovery

### 6. Business Observability – PARTIAL
- OpenTelemetry span helpers (optional import)
- Missing: metrics, correlation ID middleware, full instrumentation

### 7. AI Approval Workflow – PARTIAL
- ApprovalRequest model and service
- Missing: integration into AgentOrchestrator, UI endpoints, audit

### 8. Multi-photo + Document Versioning – PARTIAL
- Domain models for photos and versions
- Missing: upload endpoints, ACL, MIME/size enforcement, storage adapter

## Safety
- No changes to main or protected files
- No production migrations or deploys
- All work remains on feat/platform-extensions

Revoke the temporary PAT immediately.