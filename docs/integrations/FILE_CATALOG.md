# CMEP Integrations — Katalóg súborov (Etapa 2)

Každý súbor má konkrétnu zodpovednosť. Prázdne súbory sa nevytvárajú.

## Domain

| Súbor | Účel | Závislosti | Testy |
|---|---|---|---|
| domain/entities/integration.py | Typ externého systému, stav, identifikácia | — | test_integration_entity.py |
| domain/entities/integration_connection.py | Pripojenie firmy k externému systému | companies | test_connection_entity.py |
| domain/entities/sync_job.py | Synchronizačná úloha a stav | — | test_sync_job_entity.py |
| domain/entities/webhook_subscription.py | Odber externých udalostí | — | test_webhook_subscription_entity.py |
| domain/entities/integration_event.py | Udalosť v integračnom procese | — | test_integration_event_entity.py |
| domain/value_objects/integration_type.py | ERP/WAREHOUSE/ACCOUNTING/TRANSPORT/CUSTOM | — | test_integration_type.py |
| domain/value_objects/integration_status.py | active/disconnected/error/suspended | — | test_integration_status.py |
| domain/value_objects/sync_status.py | pending/running/completed/failed/retrying/cancelled | — | test_sync_status.py |
| domain/repositories/integration_repository.py | Rozhranie pre integrácie | — | test_integration_repository.py |
| domain/repositories/connection_repository.py | Rozhranie pre pripojenia | — | test_connection_repository.py |
| domain/repositories/sync_repository.py | Rozhranie pre sync úlohy | — | test_sync_repository.py |
| domain/services/integration_policy.py | Pravidlá pre integrácie | entitlements | test_integration_policy.py |
| domain/services/integration_permissions.py | Oprávnenia pre operácie | authorization | test_integration_permissions.py |

## Application

| Súbor | Účel | Závislosti | Testy |
|---|---|---|---|
| application/services/connection_service.py | Správa pripojení | connection_repository, credential_service | test_connection_service.py |
| application/services/integration_registry.py | Register dostupných integrácií a adaptérov | adapters | test_integration_registry.py |
| application/services/sync_service.py | Koordinácia synchronizácie | sync_repository, adapters | test_sync_service.py |
| application/services/webhook_service.py | Prijímanie a spracovanie webhookov | connection_repository, event_repository | test_webhook_service.py |
| application/services/credential_service.py | Šifrovanie/dešifrovanie credentials | cryptography (Fernet) | test_credential_service.py |
| application/services/integration_health_service.py | Stav pripojení, chyby | connection_repository, sync_repository | test_health_service.py |
| application/use_cases/connect_integration.py | UC: pripojiť externý systém | connection_service | test_connect_integration.py |
| application/use_cases/disconnect_integration.py | UC: odpojiť | connection_service | test_disconnect_integration.py |
| application/use_cases/test_connection.py | UC: otestovať spojenie | connection_service, adapter | test_test_connection.py |
| application/use_cases/start_sync.py | UC: spustiť synchronizáciu | sync_service | test_start_sync.py |
| application/use_cases/retry_sync.py | UC: opakovať neúspešnú úlohu | sync_service | test_retry_sync.py |
| application/use_cases/process_webhook.py | UC: spracovať webhook | webhook_service | test_process_webhook.py |
| application/dto/integration_dto.py | DTO pre integrácie | — | test_integration_dto.py |
| application/dto/connection_dto.py | DTO pre pripojenia | — | test_connection_dto.py |
| application/dto/sync_dto.py | DTO pre synchronizáciu | — | test_sync_dto.py |

## Infrastructure

| Súbor | Účel | Závislosti | Testy |
|---|---|---|---|
| infrastructure/models/integration_model.py | SQLAlchemy model integrations | Base | test_integration_model.py |
| infrastructure/models/integration_connection_model.py | SQLAlchemy model connections | Base | test_connection_model.py |
| infrastructure/models/sync_job_model.py | SQLAlchemy model sync_jobs | Base | test_sync_job_model.py |
| infrastructure/models/webhook_subscription_model.py | SQLAlchemy model webhook_subs | Base | test_webhook_model.py |
| infrastructure/models/integration_event_model.py | SQLAlchemy model events | Base | test_event_model.py |
| infrastructure/repositories/sql_integration_repository.py | SQL impl integration_repository | models | test_sql_integration_repo.py |
| infrastructure/repositories/sql_connection_repository.py | SQL impl connection_repository | models | test_sql_connection_repo.py |
| infrastructure/repositories/sql_sync_repository.py | SQL impl sync_repository | models | test_sql_sync_repo.py |
| infrastructure/adapters/base_adapter.py | Rozhranie pre adaptéry | — | test_base_adapter.py |
| infrastructure/adapters/erp_adapter.py | ERP adaptér (stub) | base_adapter | test_erp_adapter.py |
| infrastructure/adapters/warehouse_adapter.py | Sklad adaptér (stub) | base_adapter | test_warehouse_adapter.py |
| infrastructure/adapters/accounting_adapter.py | Účtovníctvo adaptér (stub) | base_adapter | test_accounting_adapter.py |
| infrastructure/adapters/transport_adapter.py | Doprava adaptér (stub) | base_adapter | test_transport_adapter.py |
| infrastructure/encryption/fernet_encryptor.py | Fernet šifrovanie credentials | cryptography | test_fernet_encryptor.py |
| infrastructure/queue/db_sync_queue.py | DB-backed synchronizačná fronta | sync_repository, scheduler | test_db_sync_queue.py |
| infrastructure/scheduler/sync_scheduler.py | Plánovanie opakovaných sync | scheduler, sync_service | test_sync_scheduler.py |

## Presentation

| Súbor | Účel | Závislosti | Testy |
|---|---|---|---|
| presentation/router.py | REST API pre integrácie | use_cases, auth | test_integrations_api.py |
| presentation/schemas/integration_schemas.py | Pydantic schémy vstupov/výstupov | pydantic | test_integration_schemas.py |
| presentation/schemas/webhook_schemas.py | Pydantic schémy pre webhooky | pydantic | test_webhook_schemas.py |
| presentation/dependencies.py | DI pre služby | services | test_dependencies.py |

## Modul __init__ a registrácia

| Súbor | Účel |
|---|---|
| __init__.py | Modul marker |
| domain/__init__.py | Domain marker |
| application/__init__.py | Application marker |
| infrastructure/__init__.py | Infrastructure marker |
| presentation/__init__.py | Presentation marker |
| tests/__init__.py | Test marker |

## Zmeny v existujúcich súboroch

| Súbor | Zmena | Dôvod |
|---|---|---|
| app/shared/presentation/api_router.py | +1 riadok: include_router(integrations_router) | Mount API (PROTECTED — zdôvodnené) |
| app/shared/infrastructure/db/register_models.py | +5 importov nových modelov | Registrácia tabuliek |
| requirements.txt | +1: cryptography | Fernet šifrovanie credentials |
| .env.example | +INTEGRATIONS_ENCRYPTION_KEY | Šifrovací kľúč |
