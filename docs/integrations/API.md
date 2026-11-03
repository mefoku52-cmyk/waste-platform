# CMEP Integrations — API rozhranie (Etapa 2)

Prefix: `/api/v1/integrations`
Auth: všetky endpointy vyžadujú `Authorization: Bearer <token>`

## Dostupné integrácie

GET /integrations/available
- Zoznam typov integrácií (ERP, WAREHOUSE, ACCOUNTING, TRANSPORT, CUSTOM)
- Auth: require_current_user
- Odpoveď: [{ type, name, description, required_fields[] }]

## Pripojenia

GET /integrations/connections?company_id={id}
- Zoznam pripojení firmy
- Auth: require_current_user + require_company_member
- Odpoveď: [{ id, company_id, type, name, status, base_url, last_sync_at, last_sync_status }]
- Tajné údaje: NIKDY

POST /integrations/connections
- Vytvorenie pripojenia
- Auth: require_current_user + require_company_admin
- Tier check: CompanyEntitlementService.has_tier()
- Body: { company_id, type, name, base_url, credentials{}, config{} }
- credentials sa šifrujú (Fernet) pred zápisom
- Odpoveď: 201 { id, type, name, status: "active" } (bez credentials)

GET /integrations/connections/{id}
- Detail pripojenia
- Auth: require_current_user + ownership check
- Odpoveď: { id, company_id, type, name, status, base_url, config, last_sync_at, ... }
- credentials: NIKDY

PATCH /integrations/connections/{id}
- Aktualizácia (name, base_url, config, credentials)
- Auth: require_current_user + require_company_admin + ownership
- credentials (ak poslané): šifrovať

DELETE /integrations/connections/{id}
- Odpojenie (soft delete, status → disconnected)
- Auth: require_current_user + require_company_admin + ownership

POST /integrations/connections/{id}/test
- Test spojenia bez zmeny dát
- Auth: require_current_user + require_company_member + ownership
- Odpoveď: { ok: bool, latency_ms, error?: str }

POST /integrations/connections/{id}/sync
- Spustenie synchronizácie
- Auth: require_current_user + require_company_admin + ownership
- Body: { direction: "inbound"|"outbound", entity_types[]? }
- Odpoveď: 202 { sync_job_id, status: "pending" }

GET /integrations/connections/{id}/history
- História operácií (sync jobs + events)
- Auth: require_current_user + require_company_member + ownership
- Query: ?limit=50&offset=0
- Odpoveď: [{ sync_job_id, status, started_at, completed_at, records, error? }]

## Webhooky

POST /integrations/webhooks/{connection_id}
- Prijatie externého webhooku
- Auth: HMAC-SHA256 podpis v hlavičke X-Integration-Signature
- Overenie: timestamp (X-Integration-Timestamp) + replay okno 5 min
- Idempotencia: X-Integration-Event-Id deduplikácia
- Odpoveď: 200 { received: true, event_id: str }

## Zdravie

GET /integrations/health
- Stav všetkých integrácií (preložené)
- Auth: require_admin (platform admin)
- Odpoveď: [{ connection_id, company_id, status, last_sync, error_count }]
