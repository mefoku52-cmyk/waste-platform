# CMEP Integrations — Implementačný plán (Etapa 2)

Práca je rozdelená na malé overiteľné etapy. Každá etapa má jasné výstupy.

## ETAPA 3A — Doménové jadro a šifrovanie

Krok 1: Domain entities a value objects
  - integration.py, integration_connection.py, sync_job.py
  - webhook_subscription.py, integration_event.py
  - integration_type.py, integration_status.py, sync_status.py
  - domain/repositories rozhrania
  - domain/services (integration_policy, integration_permissions)
  Testy: unit testy všetkých entít a value objects

Krok 2: Šifrovanie
  - infrastructure/encryption/fernet_encryptor.py
  - Pridať `cryptography` do requirements.txt
  - Pridať INTEGRATIONS_ENCRYPTION_KEY do .env.example
  Testy: test_fernet_encryptor (encrypt → decrypt roundtrip, wrong key, empty)

Krok 3: Databázové modely
  - 5 SQLAlchemy modelov (integration, connection, sync_job, webhook, event)
  - Registrácia v register_models.py
  - Alembic migrácia (SQLite + PostgreSQL kompatibilná)
  Testy: model creation, constraints, relationships

Výstup: doménové objekty + šifrovanie + DB modely + migrácia + testy

## ETAPA 3B — Aplikačná vrstva

Krok 4: Služby
  - credential_service (šifrovanie/dešifrovanie cez FernetEncryptor)
  - connection_service (CRUD nad pripojeniami)
  - integration_registry (register adaptérov)
  - sync_service (koordinácia synchronizácie)
  - webhook_service (overenie HMAC, replay, idempotencia)
  - integration_health_service (stav pripojení)
  Testy: unit testy všetkých služieb (mock repositories)

Krok 5: Use cases
  - connect_integration, disconnect_integration, test_connection
  - start_sync, retry_sync, process_webhook
  Testy: unit testy use cases (mock services)

Krok 6: Adaptéry
  - base_adapter (abstraktné rozhranie)
  - erp_adapter, warehouse_adapter, accounting_adapter, transport_adapter
  - Stub implementácie (test_connection funguje, fetch/push vráti prázdne)
  Testy: test_base_adapter, test adaptérov so mock HTTP

Výstup: služby + use cases + adaptéry + testy

## ETAPA 3C — Prezentačná vrstva

Krok 7: API router a schemas
  - presentation/router.py (všetky endpointy z API.md)
  - presentation/schemas/ (Pydantic vstup/výstup)
  - presentation/dependencies.py (DI)
  - Mount v api_router.py (+1 riadok, PROTECTED)
  Testy: API testy (auth, company check, ownership, masking)

Výstup: funkčné API + testy

## ETAPA 4A — Synchronizácia

Krok 8: Fronta a scheduler
  - infrastructure/queue/db_sync_queue.py
  - infrastructure/scheduler/sync_scheduler.py
  - APScheduler polling pre pending úlohy
  - Retry s exponential backoff (max 3)
  Testy: test_db_sync_queue, test_sync_scheduler

Krok 9: Webhook prijímanie
  - HMAC overenie, replay ochrana, idempotencia
  - POST /integrations/webhooks/{connection_id}
  Testy: test_webhook_service (valid/invalid signature, replay, duplicate)

Výstup: synchronizácia + webhooky + testy

## ETAPA 5 — Frontend

Krok 10: Integrations UI
  - apps/web/src/app/dashboard/settings/integrations/page.tsx
  - apps/web/src/features/integrations/ (hooks, components)
  - Zoznam dostupných integrácií, pripojené systémy, stav, test, sync, história
  - Žiadne tajné údaje v UI
  Testy: frontendové testy (ak existuje test framework)

Výstup: UI pre správu integrácií

## ETAPA 6 — Záverečné overenie

Krok 11: Validácia
  - Spustiť všetky nové testy
  - Spustiť existujúce testy (regresia)
  - Skontrolovať importy
  - Skontrolovať router registráciu
  - Skontrolovať Git diff
  - Skontrolovať bezpečnosť (masking, SSRF, auth)

Výstup: potvrdenie bez regresií

## Závislosti medzi etapami

```
3A (domain+crypto+models) → 3B (services+usecases+adapters) → 3C (API)
3C → 4A (sync+webhooks)
3C → 5 (frontend)
4A → 6 (overenie)
5 → 6 (overenie)
```

## Odhad rozsahu

| Etapa | Súbory | Testy | Čas |
|---|---|---|---|
| 3A | ~15 | ~12 | najväčšia |
| 3B | ~18 | ~15 | veľká |
| 3C | ~5 | ~8 | stredná |
| 4A | ~4 | ~6 | stredná |
| 5 | ~8 | ~3 | stredná |
| 6 | 0 | 0 | malá |

Celkom: ~50 nových súborov, ~44 testov
