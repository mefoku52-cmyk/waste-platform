# CMEP Live Inspections (streaming) — platformová časť

Platforma (`waste-platform`) je **zdroj pravdy** pre identitu, tenantu a
stav obhliadky. Streamingová služba (`cmep-streaming`) spracúva iba médiá a
**nepracuje s používateľmi ani s databázou**.

Podrobný popis architektúry, kontraktu identifikátorov a konfigurácie:
`cmep-streaming/docs/LIVE_INSPECTIONS.md`.

## Modul `app/modules/inspections/`

| Súbor | Úloha |
|---|---|
| `infrastructure/models.py` | tabuľky `inspections` (stav relácie) a `inspection_events` (audit udalostí, `event_uid` jednoznačný) |
| `infrastructure/repositories.py` | čítanie/aktualizácia, deduplikácia, `find_active_by_listing` |
| `application/services.py` | pravidlá: kto smie spustiť, kto smie byť viewer, ukončenie, konzistencia so streamingom |
| `application/streaming_tokens.py` | mint krátkoodobných HMAC tokenov pre streaming (`insp`, `offerId` = inspection id) |
| `infrastructure/streaming_client.py` | jediný server-side kanál platforma → streaming (`POST /internal/inspections/{id}/end`) |
| `presentation/router.py` | HTTP endpointy (nižšie) |

## Endpointy

| Endpoint | Kto | Účel |
|---|---|---|
| `POST /api/v1/inspections` | člen firmy vlastníka ponuky | vytvorí obhliadku, vráti `publishUrl` (token + `offer`) |
| `GET /api/v1/inspections?listingId=` | účastník | aktuálna obhliadka + `canPublish` / `canJoin` (gating pre UI) |
| `POST /api/v1/inspections/join` | counterpart chatu na ponuke | priradí viewera, vráti `viewerUrl` (token + room id) |
| `GET /api/v1/inspections/{id}` | účastník | stav obhliadky (iný používateľ dostane 404) |
| `POST /api/v1/inspections/{id}/publisher-link` | vlastník firmy | nový publisher URL (napr. po zatvorení karty) |
| `POST /api/v1/inspections/{id}/recording-consent` | vlastník firmy | výslovný súhlas s nahrávaním (bez neho `rec=0`) |
| `POST /api/v1/inspections/{id}/end` | vlastník firmy | ukončí obhliadku + uzavrie miestnosť v streamingu (idempotentné) |
| `GET /api/v1/inspections/{id}/verify` | **interný** (`X-CMEP-Internal-Key`) | server-side rozhodnutie pre streaming (fail-closed) |
| `POST /api/v1/inspections/events` | **interný** (`X-CMEP-Internal-Key`) | príjem udalostí zo streamingu (idempotentné podľa `eventUid`) |

Bez `CMEP_INTERNAL_API_KEY` sú interné endpointy fail-closed (403) —
integrácia je vtedy prakticky vypnutá.

## Pravidlá

- **Publisher** = člen firmy, ktorá vlastní ponuku (`company_memberships`).
- **Viewer** = používateľ z druhej firmy, ktorý má chat vlákno na danej ponuke
  (`chat_threads`) — žiadne manuálne zadávanie ID.
- `companyId` sa **nikdy** neberie z tela požiadavky; vždy z členstva.
- Obhliadka je jednoznačne viazaná na `listing_id`; súčasne je aktívna
  len jedna (`state` mimo `ended`).
- Udalosti zo streamingu sú **iba metadata** (id, rola, čas) — nikdy obsah
  správ ani médiá.

## Konfigurácia

```
CMEP_STREAMING_SIGNING_SECRET=   # zhodný so SESSION_SIGNING_SECRET v cmep-streaming
CMEP_INTERNAL_API_KEY=           # zhodný s CMEP_INTERNAL_API_KEY v cmep-streaming
CMEP_STREAMING_PUBLIC_URL=       # na akej adrese bežia publish/viewer stránky
CMEP_STREAMING_INTERNAL_URL=     # optional; fallback na PUBLIC_URL
```

Migrácia: `migrations/versions/insp_2026111101_add_inspections_tables.py`
(tabuľky `inspections`, `inspection_events`).
