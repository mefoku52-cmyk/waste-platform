# CMEP Integrations — Architektúra (Etapa 2)

Dátum: 2026-11-01
Navazuje na: docs/integrations/INVENTORY.md

============================================================
1. CIEĽ
============================================================

Nový samostatný modul `app/modules/integrations/` pre správu
externých integrácií firiem (ERP, sklad, účtovníctvo, doprava).

Nie je to nová platforma — je to rozšírenie existujúceho CMEP.

============================================================
2. ARCHITEKTONICKÉ ROZHODNUTIA
============================================================

A) DDD vrstvenie (rovnaké ako existujúce moduly)
   domain/         — entity, value objects, repository rozhrania
   application/    — služby, use cases, DTO
   infrastructure/ — SQLAlchemy modely, adaptéry, clients
   presentation/   — FastAPI router, schemas, dependencies

B) Šifrovanie credentials
   `cryptography` balík NIE je v requirements.txt → treba pridať.
   Použiť Fernet symetrické šifrovanie.
   Kľúč: INTEGRATIONS_ENCRYPTION_KEY v .env (fallback na JWT_SECRET_KEY).
   Šifrovať: API kľúče, heslá, tokeny externých systémov.
   Nikdy nevracať v API odpovedi ani logoch.

C) Synchronizácia
   DB-backed fronta (sync_jobs tabuľka) namiesto Redis queue.
   Dôvod: Redis je voliteľný (fallback na memory), nepoužíva sa ako queue.
   Spracovanie: APScheduler polling + manuálne spustenie.
   Idempotencia: external_id + sync_job_id deduplikácia.

D) Webhooky
   Prijímanie: POST /integrations/webhooks/{connection_id}
   Overenie: HMAC-SHA256 podpis (per-connection secret).
   Replay ochrana: timestamp okno + nonce deduplikácia.

E) SSRF ochrana
   Pri pripájaní externých URL:
   - Iba HTTPS schéma
   - Blokovať private IP (10.x, 172.16-31.x, 192.168.x, 127.x, ::1)
   - Max 3 presmerovania, každé overené
   - Timeout: 15s connect, 30s read

F) api_router mount
   Pridanie `api_router.include_router(integrations_router)` do
   app/shared/presentation/api_router.py (PROTECTED súbor).
   Odôvodnenie: konzistencia s ostatnými modulmi, žiadny iný spôsob
   mountu neexistuje. Jeden riadok pridania.

G) Migrácia
   Nová Alembic migrácia pre 5 tabuliek:
   - integrations
   - integration_connections
   - integration_events
   - sync_jobs
   - webhook_subscriptions

============================================================
3. DÁTOVÝ TOK
============================================================

Pripojenie:
  User → POST /integrations/connections
    → auth (require_current_user)
    → company check (require_company_member)
    → tier check (CompanyEntitlementService)
    → credential encryption (Fernet)
    → IntegrationConnectionModel (DB)
    → audit (ActivityEventModel)
    → 201 Created (bez tajných údajov)

Synchronizácia:
  User → POST /integrations/connections/{id}/sync
    → auth + company + ownership check
    → SyncJobModel (status=pending)
    → APScheduler / async task
    → adapter.fetch() (externý systém)
    → validácia + mapovanie
    → zápis do integration_events
    → SyncJobModel (status=completed/failed)
    → notification (Telegram/Resend)
    → audit

Webhook:
  Externý → POST /integrations/webhooks/{connection_id}
    → HMAC overenie podpisu
    → replay check (timestamp + nonce)
    → idempotencia (external_event_id)
    → IntegrationEventModel
    → spracovanie (async)
    → 200 OK

============================================================
4. DOMÉNOVÉ ENTITY
============================================================

IntegrationType (value object):
  ERP, WAREHOUSE, ACCOUNTING, TRANSPORT, CUSTOM

IntegrationStatus (value object):
  active, disconnected, error, suspended

IntegrationConnection (entity):
  id, company_id, integration_type, name, status,
  base_url, encrypted_credentials, config_json,
  created_at, updated_at, last_sync_at, last_sync_status

SyncJob (entity):
  id, connection_id, status, direction (inbound/outbound),
  started_at, completed_at, error_message, records_processed,
  external_batch_id

SyncStatus (value object):
  pending, running, completed, failed, retrying, cancelled

WebhookSubscription (entity):
  id, connection_id, secret_hash, event_types,
  active, created_at, updated_at

IntegrationEvent (entity):
  id, connection_id, sync_job_id, event_type,
  external_id, payload_json, processed_at, status

============================================================
5. ADAPTÉR ROZHRANIE
============================================================

base_adapter.py:
  class BaseAdapter(ABC):
    @abstractmethod
    async def test_connection(credentials) -> TestResult
    @abstractmethod
    async def fetch_data(query) -> list[dict]
    @abstractmethod
    async def push_data(records) -> PushResult
    @abstractmethod
    def validate_config(config) -> list[str]

ERP/Warehouse/Accounting/Transport:
  Dedia z BaseAdapter, pridávajú špecifické mapovanie.
  Spočiatku stub implementácie (rozšíriteľné neskôr).

============================================================
6. NÁVRH API ENDPOINTOV
============================================================

Prefix: /integrations (v rámci api_router, pod /api/v1)

  GET    /integrations/available        — zoznam dostupných typov
  GET    /integrations/connections       — pripojenia firmy
  POST   /integrations/connections        — vytvoriť pripojenie
  GET    /integrations/connections/{id}   — detail pripojenia
  PATCH  /integrations/connections/{id}   — aktualizovať
  DELETE /integrations/connections/{id}   — odpojiť
  POST   /integrations/connections/{id}/test    — test spojenia
  POST   /integrations/connections/{id}/sync    — spustiť synchronizáciu
  GET    /integrations/connections/{id}/history  — história operácií
  POST   /integrations/webhooks/{connection_id} — prijať webhook
  GET    /integrations/health             — zdravotný stav integrácií

Bezpečnosť každého endpointu:
  - require_current_user
  - require_company_member (okrem health — platform admin)
  - ownership check (connection.company_id == user's company)
  - žiadne tajné údaje v odpovedi
  - audit log

============================================================
7. ZÁVISLOSTI NA EXISTUJÚCICH MODULOCH
============================================================

  companies           → CompanyModel (company_id, existence check)
  company_memberships → require_company_member, require_company_admin
  companies/entitlements → CompanyEntitlementService.has_tier()
  notifications       → TelegramService, ResendSender (sync upozornenia)
  events              → ActivityEventModel (audit udalostí)
  shared/db           → Base, get_db_session, register_models
  shared/presentation → require_current_user, authorization
  shared/infrastructure → rate_limit, scheduler

============================================================
8. RIZIKÁ
============================================================

1. PROTECTED api_router.py — pridanie 1 riadku include_router.
   Odôvodnenie: jediný spôsob mountu, konzistencia s 34 ostatnými.
2. `cryptography` nie je v requirements.txt → pridanie dependency.
3. Migrácia musí podporovať SQLite aj PostgreSQL.
4. Prvé adaptéry budú stub (rozšíriteľné neskôr).
5. Synchronizácia cez APScheduler polling (nie Redis queue).
6. Žiadne zmeny v existujúcich moduloch okrem api_router (1 riadok).

============================================================
  KONIEC ARCHITEKTÚRY — Etapa 2 dokončená
============================================================
