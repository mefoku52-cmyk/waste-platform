# CMEP — Inventúra existujúceho stavu (Etapa 1)

Dátum: 2026-11-01
Vetva: fix/chat-security-and-actions
Commit: 7c813e9
Stav: clean (iba untracked CMEP-FIX-RENDER-CRASH-REPORT.txt)

============================================================
1. GIT A KONTEXT
============================================================

Aktuálna vetva: fix/chat-security-and-actions
Posledné commity:
  7c813e9 fix(security+agent): navigator only for NAVIGATE intent, IDOR fixes, chat_router dedup
  0c71d6c Fix: chat_router používa get_or_create namiesto nefunkčnej get_by_session_id
  535f4e9 Merge: Add missing files + get_by_session_id method

Pracovný strom: čistý (žiadne uncommitted zmeny okrem report .txt)
Žiadny nový modul `integrations` zatiaľ neexistuje.

============================================================
2. EXISTUJÚCE MODULY (app/modules/)
============================================================

21 doménových modulov:
  admin, agent_platform, analytics, auth, billing, chat,
  companies, company_memberships, company_pages, company_reviews,
  compliance, documents, events, inquiries, lead_finder,
  listings, notifications, prediction, recommendations,
  transport, uploads, users

Poznámka: existuje aj `agent_platform_NEW_BACKUP_20261028_192546`
— starý backup adresár (neimportovaný, bez __init__.py v koreni).

============================================================
3. EXISTUJÚCE EXTERNÉ INTEGRÁCIE
============================================================

A) PLATBY — app/modules/billing/
   Súbory:
     infrastructure/models.py  — BillingPaymentOrderModel, BillingWebhookEventModel
     presentation/router.py    — Stripe Checkout, Stripe predplatné
   Poskytovatelia:
     ✅ Stripe Checkout — funkčný (https://api.stripe.com)
     ✅ Stripe Webhook — funkčný (podpisoverenie, idempotencia cez BillingWebhookEventModel)
     ⚠️ GoPay — DEPRECATED / NOT IMPLEMENTED
        .env.example má GOPAY_* premenné, ale kód vždy vracia 503
        Settings pravdepodobne nemá GOPAY polia (NEOVERENÉ)
   Tarify (zo zdrojáku):
     SubscriptionTier: FREE, PRO, AI, AI_NAVIGATION
     Stripe ceny: ai=29€/mes, ai_navigation=99€/mes
   Entitlements:
     app/modules/companies/application/entitlements.py
     CompanyEntitlementService — has_tier(company_id, minimum)
     _TIER_ORDER: FREE=0, PRO=1, AI=2, AI_NAVIGATION=3

B) TELEGRAM — app/modules/notifications/
   Súbory:
     application/telegram_service.py  — notify_pipeline_failure, admin alerts
     infrastructure/telegram_client.py — HTTP klient
     presentation/telegram_router.py   — webhook endpoint
   Stav: ✅ funkčné odosielanie správ + webhook
   Token: TELEGRAM_BOT_TOKEN v .env.example

C) REGISTER FIRIEM (RPO) — app/modules/companies/application/rpo.py
   API: https://api.statistics.sk/rpo/v1/search (SUSR, bez API kľúča)
   Funkcia: lookup_ico(raw) → dict (ok, exists, ico, legalName, city)
   Stav: ✅ funkčné read-only napojenie, žiadne tajomstvá

D) AI A KORMIDELNÍK — app/modules/agent_platform/
   AI gatewaye:
     infrastructure/ai/cerebras_gateway.py   — Cerebras
     infrastructure/ai/groq_gateway.py        — Groq
     infrastructure/ai/mistral_gateway.py     — Mistral
     infrastructure/ai/chain_gateway.py       — Chain (failover)
     infrastructure/ai/voice_gateway.py       — Edge TTS
     infrastructure/ai/model_gateway.py      — spoločné rozhranie
     infrastructure/ai/_net.py                — spoločná HTTP infra
   Navigator:
     navigator/navigator_bridge.py      — bridge s TaskCoordinator
     navigator/task_coordinator.py       — koordinácia úloh
     navigator/generic_api_adapter.py    — generický adaptér
     navigator/model_adapter.py          — adaptér modelov
     navigator/permissions.py             — oprávnenia agenta
   Nástroje:
     infrastructure/tools/ — 20+ súborov (tool_registry, tool_dispatcher,
     cmep_company_search, cmep_listing_search, client_action_validation, ...)
   Bezpečnosť:
     domain/control/agent_gate.py  — gate pre agent akcie
     application/permission/        — permission engine
     application/policy/            — policy engine
     application/security/           — security engine
   Konfigurácia:
     CEREBRAS_API_KEY, CEREBRAS_API_URL, CEREBRAS_MODEL v .env.example

E) EMAIL — app/shared/infrastructure/email/
   resend_sender.py — Resend API (RESEND_API_KEY, RESEND_FROM_EMAIL)
   sender.py        — EmailSender interface
   Stav: ✅ funkčné (Resend)

F) DEEPL — preklady
   DEEPL_API_KEY v .env.example
   NEOVERENÉ kde presne sa používa (pravdepodobne v company_pages alebo compliance)

============================================================
4. INFRAŠTRUKTÚRA
============================================================

Databáza:
  PostgreSQL v produkcii (asyncpg)
  SQLite v developmente (aiosqlite)
  ORM: SQLAlchemy 2.0 (declarative_base)
  Base: app/shared/infrastructure/db/base.py
  Model registration: app/shared/infrastructure/db/register_models.py
  Migrácie: Alembic (migrations/versions/ — 22 migračných súborov)
  Session: app/shared/infrastructure/db/session.py (async get_db_session)

Redis:
  Config: app/core/config.py → RedisSettings
  Použitie: rate limiting (app/shared/infrastructure/rate_limit.py)
  jwt_revocation_store.py
  Fallback: in-memory ak Redis nedostupný
  URL: redis://127.0.0.1:6379/0 (.env.example)

Scheduler:
  APScheduler (AsyncIOScheduler)
  app/shared/infrastructure/scheduler.py
  CronTrigger pre denné úlohy
  Notifikácia zlyhania cez Telegram

Deployment:
  Docker: Dockerfile (python:3.14-slim, non-root user)
  Render: žiadny render.yaml v repozitári (NEOVERENÉ — možno v Render dashboard)
  Port: dynamický (ENV PORT, default 8000)

Bezpečnosť:
  JWT: app/shared/infrastructure/security/jwt_service.py (PROTECTED)
  Revocation: jwt_revocation_store.py (PROTECTED)
  Authorization: app/shared/presentation/authorization.py
    — current_user_id, is_platform_admin, membership_company_ids,
      require_company_member, require_company_admin
  Rate limiting: app/shared/infrastructure/rate_limit.py
  Turnstile: app/shared/infrastructure/turnstile.py
  CORS: konfigurovateľný cez CORS_ORIGINS

Šifrovanie:
  ⚠️ Žiadny explicitný encryption modul neexistuje v app/
  Žiadne použitie Fernet/cryptography/encrypt/decrypt v kóde
  Uploads podpisovanie: UPLOADS_SIGNING_SECRET (fallback na JWT_SECRET_KEY)
  NOVÝ modul bude musieť zaviesť šifrovanie pre externé credentials

============================================================
5. API ROUTING
============================================================

Hlavný router: app/shared/presentation/api_router.py (PROTECTED)
  — mountuje všetky modulové routery pod APIRouter()
  — 34 router includov v api_router.py

Prefixy (z router definícií):
  /admin, /agent-platform, /analytics, /auth, /billing, /chat,
  /companies, /company-pages, /company-reviews, /compliance,
  /documents, /events, /inquiries, /listings, /notifications,
  /prediction, /recommendations, /transport, /uploads, /users

Mount v main.py:
  app.include_router(api_router, prefix="/api/v1")
  Health: /health, /ready (bez auth)
  Ops: /ops (ops_router)
  Metrics: /metrics (metrics_router)

Konvencia: prefix="/modul-name", tags=["modul-name"]
Nový /integrations prefix — ŽIADNY konflikt neexistuje.

============================================================
6. DATABÁZOVÉ MODELY (registrované)
============================================================

19 model súborov, 30+ tabuliek:
  admin:          AdminAuditEntryModel
  agent_platform:  AgentAuditRecordModel, AiConversationModel,
                   AiMessageModel, AlertRecordModel, ApprovalRequestModel,
                   ControlStateModel, SecurityEventModel
  analytics:       AnalyticsEventModel
  auth:            RefreshSessionModel
  billing:         BillingPaymentOrderModel, BillingWebhookEventModel
  chat:            ChatMessageModel, ChatThreadModel
  companies:       CompanyModel
  company_memberships: CompanyMembershipModel
  company_pages:   CompanyPageModel, CompanyPhotoModel
  company_reviews: CompanyReviewModel
  compliance:      ComplianceRecordModel
  documents:       DocumentModel
  events:          ActivityEventModel
  inquiries:       InquiryModel
  lead_finder:     OutreachCandidateModel
  listings:        ListingsModel, ListingViewModel
  notifications:   NotificationModel
  users:           User2FAModel, UserModel

Tabuľka `integrations` alebo podobná — NEEXISTUJE.

============================================================
7. AUTORIZÁCIA A OPRÁVNENIA
============================================================

Platform admin:
  settings.PLATFORM_ADMIN_EMAILS (čiarkou separované)
  PLATFORM_ADMIN_ROLE_CODES = {"platform_admin"}
  is_platform_admin(current_user) — kontrola emailu

Company admin:
  COMPANY_ADMIN_ROLES = {"owner", "admin"}
  require_company_admin(current_user, company_id)
  require_company_member(current_user, company_id)

Tenant izolácia:
  membership_company_ids(current_user) → frozenset[str]
  current_user_id(current_user) → str | None

Dependencia:
  require_current_user (from app.shared.presentation.auth_dependencies)

============================================================
8. FRONTEND (apps/web/src/)
============================================================

Next.js aplikácia (App Router)
Dashboard sekcie:
  admin/, ai-demo/, chat/, companies/, company/,
  documents/, inquiries/, listings/, settings/, subscription/, transport/

Features (src/features/):
  admin/, agent-platform/, auth/, chat/, companies/,
  company-pages/, compliance/, documents/

Settings sekcia:
  apps/web/src/app/dashboard/settings/
  — zatiaľ iba /security podstránka
  — ŽIADNE integrations podstránka neexistuje

API proxy:
  Next.js rewrites /api/v1/* → API_PROXY_TARGET
  NEXT_PUBLIC_API_BASE_URL=/api/v1

============================================================
9. TESTY
============================================================

Štruktúra:
  tests/unit/         — 120+ unit test súborov
  tests/integration/  — 10 integračných test súborov
  tests/api/          — 2 API testy
  tests/modules/      — prediction tests
  app/modules/*/tests/ — modulové testy (agent_platform, lead_finder)

Python verzia: 3.14 (Dockerfile: python:3.14-slim)
Test runner: pytest
Coverage: pytest-cov (nainštalovaný)

Chýbajúce v lokálnom venv: ruff, mypy (sú v Render Docker)

============================================================
10. CHÝBAJÚCE ČASTI PRE INTEGRAČNÝ MODUL
============================================================

NEEXISTUJE:
  1. app/modules/integrations/ — celý modul
  2. Databázové tabuľky: integrations, integration_connections,
     integration_events, sync_jobs, webhook_subscriptions
  3. Migrácie pre integračné tabuľky
  4. API endpointy /integrations/*
  5. Šifrovanie externých credentials (žiadny crypto modul v kóde)
  6. Frontend /dashboard/settings/integrations
  7. Synchronizačná fronta (Redis queue alebo DB-backed)
  8. Webhook prijímanie a overovanie podpisov pre externé systémy
  9. Adaptéry (ERP, warehouse, accounting, transport)
  10. docs/integrations/ (okrem tohto INVENTORY.md)

EXISTUJE A DA SA VYUŽIŤ:
  1. Authorization framework (require_company_member, require_company_admin)
  2. DB session a model registration pattern
  3. Alembic migrácie
  4. Rate limiting (Redis-backed)
  5. Scheduler (APScheduler)
  6. Notifications (Telegram, Resend email)
  7. Entitlements (CompanyEntitlementService)
  8. Events (ActivityEventModel)
  9. Audit (AdminAuditEntryModel, AgentAuditRecordModel)
  10. api_router mount pattern

============================================================
11. RIZIKÁ A POZNÁMKY
============================================================

1. Šifrovanie: Neexistuje žiadny crypto modul. Nový modul musí zaviesť
   bezpečné šifrovanie (napr. Fernet z cryptography balíka) pre externé
   API kľúče a heslá. Overiť či `cryptography` je v requirements.txt.

2. SSRF: Pri pripájaní externých URL treba validovať schémy (iba HTTPS),
   blokovať private IP rozsahy, kontrolovať presmerovania.

3. SQLite vs PostgreSQL: Migrácie musia podporovať obe databázy.
   PostgreSQL používa UUID stĺpce, SQLite STRING.

4. GoPay: Označené ako DEPRECATED. Neimplementovať.

5. agent_platform_NEW_BACKUP_20261028_192546: Starý backup adresár.
   Nezmazávať (pravidlo 11), ale nepoužívať.

6. api_router.py je PROTECTED — pridanie /integrations mountu
   vyžaduje osobitné zdôvodnenie a schválenie.

7. Render konfigurácia nie je v repozitári. Nasadenie sa konfiguruje
   cez Render dashboard. NEOVERENÉ.

8. .env.example obsahuje GOPAY_* premenné, ale Settings ich pravdepodobne
   nemapuje. NEOVERENÉ — treba skontrolovať app/core/config.py Settings.

============================================================
12. ZHRNUTIE PRE ETAPU 2
============================================================

Nový modul `app/modules/integrations/` bude samostatný modul
napájajúci sa na:
  - companies (company_id, membership)
  - company_memberships (oprávnenia)
  - billing/entitlements (tier kontrola)
  - notifications (upozornenia na sync stavy)
  - events (audit udalostí)
  - shared/infrastructure (db, redis, scheduler, rate_limit)
  - shared/presentation (auth, authorization)

Nevytvára duplicitné riešenie pre:
  - platby (billing vlastní)
  - AI (agent_platform vlastní)
  - RPO lookup (companies/rpo.py vlastní)
  - notifikácie (notifications vlastní)

MUSÍ zaviesť:
  - šifrovanie externých credentials
  - SSRF ochranu
  - webhook podpisoverenie
  - synchronizačnú frontu
  - audit všetkých operácií

============================================================
  KONIEC INVENTÚRY — Etapa 1 dokončená
============================================================
