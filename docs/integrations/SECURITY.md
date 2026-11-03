# CMEP Integrations — Bezpečnosť (Etapa 2)

## 1. Šifrovanie credentials

Knica: `cryptography.fernet.Fernet`
Kľúč: `INTEGRATIONS_ENCRYPTION_KEY` (env), fallback na `JWT_SECRET_KEY`
Šifrujú sa: API kľúče, heslá, tokeny, OAuth secrets
Ukladanie: `integration_connections.encrypted_credentials` (TEXT/BLOB)
Nikdy sa nevracajú v API odpovedi, logoch, ani testovacích výstupoch.

## 2. Izolácia tenantov

Každé pripojenie má `company_id`.
Všetky query filtrujú cez `company_id` z user membership.
Žiadny cross-tenant prístup — overuje `require_company_member`.
Ownership check: `connection.company_id == user.active_company_id`.

## 3. SSRF ochrana

Pri pripájaní externých URL:
- Iba HTTPS schéma (http povolené len v development)
- Blokovať private IP: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, ::1, fc00::/7
- Max 3 HTTP presmerovania, každé overené
- Timeout: 15s connect, 30s read
- Max veľkosť odpovede: 10 MB
- Žiadne userinfo v URL (username:password@host)

## 4. Webhook overenie

HMAC-SHA256 podpis:
  Hlavička: `X-Integration-Signature: sha256=<hex>`
  Telo: raw request body
  Kľúč: per-connection webhook secret (šifrovaný v DB)

Replay ochrana:
  Hlavička: `X-Integration-Timestamp: <unix_ts>`
  Okno: ±5 minút od server času
  Hlavička: `X-Integration-Event-Id: <uuid>`
  Deduplikácia: `integration_events.external_id` UNIQUE

## 5. Rate limiting

Používa existujúci `app/shared/infrastructure/rate_limit.py`:
  POST /connections: 5/hour per company
  POST /sync: 10/hour per connection
  POST /webhooks: 100/min per connection

## 6. Audit

Každá citlivá operácia sa zaznamená:
  - `activity_events` (existujúci model)
  - Log: actor_id, action, connection_id, company_id, timestamp
  - Citlivé údaje sa maskujú v logoch

## 7. Rotácia a odvolanie

PATCH /connections/{id}: výmena credentials (staré sa prepíšu)
DELETE /connections/{id}: status → disconnected, credentials sa vymažu
Token rotation: adaptér môže navrhnúť rotáciu (NEOVERENÉ — future)

## 8. Idempotencia

Sync jobs: `external_batch_id` deduplikácia
Webhook events: `external_id` UNIQUE constraint
Duplicate POST /sync (rovnaký batch): vráti existujúci sync_job_id
