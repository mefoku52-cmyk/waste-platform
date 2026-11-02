# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions
Base: main @ 834f389

## Completed / In Progress

### 1. Outbound Webhooks (Etapa A) – PARTIAL
- app/modules/webhooks/__init__.py
- app/modules/webhooks/domain/models.py (event types, endpoint, delivery)
- app/modules/webhooks/infrastructure/signing.py (HMAC-SHA256 + replay protection)
- app/modules/webhooks/application/delivery_service.py (retry + DLQ skeleton)

Still needed: router, repository, SSRF guard, admin endpoints, tests, migration.

### 2. Idempotent Command Bus (Etapa B) – PARTIAL
- app/shared/infrastructure/commands/bus.py

Still needed: registration of business commands, DB-backed idempotency, integration with inquiry/listing/promote.

### 3. Partner OAuth 2.0 (Etapa C) – PARTIAL
- app/modules/partner_oauth/domain/models.py (scopes + application/token)

Still needed: token issuance, middleware, client registry, rate limits.

### 4–8. Remaining
- CQRS Light (read_models)
- Saga / Process Manager (workflows)
- Business Observability (OpenTelemetry)
- AI Approval Workflow
- Multi-photo + Document Versioning

## Notes
- No changes to main, config.py, JWT, or protected files.
- No production deploy or migration execution.
- Token used for creation should be revoked immediately.

Next batches will complete the remaining layers and tests.