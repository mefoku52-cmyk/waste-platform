# CMEP Integrations — Synchronizácia (Etapa 2)

## Prehľad

Synchronizácia prenáša dáta medzi CMEP a externými systémami (ERP, sklad, účtovníctvo, doprava).
Je samostatný asynchrónny proces — neblokuje API požiadavky.

## Architektúra

DB-backed fronta (nie Redis queue):
  - `sync_jobs` tabuľka → stav úlohy
  - `integration_events` tabuľka → jednotlivé záznamy
  - APScheduler polling → spracovanie pending úloh
  - Manuálne spustenie cez POST /connections/{id}/sync

Dôvod DB namiesto Redis:
  Redis je voliteľný (fallback na memory), nepoužíva sa ako queue.
  DB garantuje perzistenciu a auditnosť.

## Stavy sync úlohy

```
pending → running → completed
                  → failed → retrying → completed/failed
pending → cancelled
```

Pravidlá:
  - pending: úloha vytvorená, čaká na spracovanie
  - running: adaptér pracuje
  - completed: úspešne dokončená
  - failed: chyba, čaká na retry
  - retrying: opakovaný pokus
  - cancelled: zrušená používateľom alebo systémom

## Prevody

Jednosmerný (inbound): externý → CMEP
Jednosmerný (outbound): CMEP → externý
Obojsmerný: iba po výslovnom nastavení (config `bidirectional: true`)

Pri konflikte údajov:
  - Systém NIKDY automaticky neprepíše existúce firemné dáta
  - Konflikt sa zaznamená do integration_events (status=conflict)
  - Notifikácia cez existujúci notifications modul
  - Používateľ musí explicitne potvrdiť prepísanie

## Idempotencia

  - `sync_jobs.external_batch_id` — deduplikácia rovnakého batchu
  - `integration_events.external_id` — deduplikácia jednotlivých záznamov
  - Duplicitný POST /sync s rovnakým batch → vráti existujúci sync_job_id

## Opakovanie chýb

  - Max 3 retry pokusy
  - Exponential backoff: 1min, 5min, 15min
  - Po 3 neúspechoch: status=failed, notifikácia
  - Žiadne nekonečné opakovanie

## Validácia a mapovanie

  - Adaptér definuje `validate_config(config) → list[str]`
  - Mapovanie polí: config `field_mapping: { external_field: cmep_field }`
  - Validácia dát: adaptér `validate_data(records) → list[errors]`
  - Nevalidné záznamy: zaznamenané do events (status=invalid), neprepašú

## Audit

  - Každá sync úloha: sync_job záznam s started_at, completed_at, records_processed
  - Každý prenesený záznam: integration_event s external_id, status
  - activity_events: actor_id, action="sync_start/sync_complete/sync_fail"
  - Notifikácie: Telegram/Resend pri úspechu/zlyhaní
