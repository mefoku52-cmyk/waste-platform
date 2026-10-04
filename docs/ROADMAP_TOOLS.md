# ROADMAP — AI nástroje pre CMEP platformu

**Dátum:** 2026-10-04
**Zdroj:** AI asistent CMEP (návrh v chate)
**Status:** NÁVRH — neimplementované

## Nové nástroje

| Nástroj | Popis a prínos | Priorita |
|---|---|---|
| **create_listing** | Umožní zadávať novú ponuku priamo z chatu (bez prechodu do UI). | VYSOKÁ |
| **update_listing** / **delete_listing** | Editácia a deaktivácia existujúcich ponúk cez asistenta — rýchlejšia správa. | STREDNÁ |
| **create_company** / **update_company** | Rýchle pridávanie alebo úprava firemných profilov (napr. pri onboardingu nových partnerov). | VYSOKÁ |
| **upload_document** | Jednoduché nahrávanie a priradenie dokumentov k firmám alebo ponukám. | STREDNÁ |
| **search_inquiries** | Vyhľadávanie dopytov (inquiries) podľa materiálu alebo lokality — doplní prehľad o dopyte. | STREDNÁ |
| **export_stats_csv** | Export štatistík alebo aktivít do CSV pre ďalšiu analýzu mimo platformy. | NÍZKA |
| **notify_user** | Posielanie notifikácií (e-mail, push) pri dôležitých udalostiach (nová ponuka, expirácia, nový dopyt). | STREDNÁ |

## Úpravy existujúcich nástrojov

1. **Zrušenie alebo úprava** — napr. `search_nearby_companies` ak nie je využívaný.
2. **Zmena limitov / stránkovania** — prispôsobiť `page_size` podľa potreby používateľov.
3. **Rozšírenie filtrov** — pridať ďalšie parametre (napr. `tier` do `search_companies`).

## Implementačné poznámky (neskôr)

- Každý nástroj musí mať: permission check, audit trail, unit testy
- `create_*` nástroje vyžadujú potvrdenie používateľa (nie tichý write)
- `delete_*` nástroje vyžadujú approval workflow
- `notify_user` — napojiť na existujúci notifications modul + Resend
- `upload_document` — použiť existujúci uploads modul (má T1 trailing slash bug)
- Všetky nástroje musia rešpektovať agent_platform permission engine

## Poradie implementácie (návrh)

1. `create_listing` (killer feature — rýchly win)
2. `create_company` + `update_company` (onboarding)
3. `search_inquiries` (doplní search)
4. `notify_user` (napojí sa na existujúce notifikácie)
5. `update_listing` + `delete_listing` (management)
6. `upload_document` (závisí od T1 fixu)
7. `export_stats_csv` (nice-to-have)

## Bezpečnostné poznámky

- Všetky write nástroje cez `agent_platform/application/tools/`
- Permission check cez `permission_engine`
- Audit každého volania
- Rate limiting per user
- Žiadne priame DB zápisy — vždy cez service layer

## TODO

- [ ] Odhad práce pre každý nástroj (hodiny)
- [ ] Rozhodnúť či `search_nearby_companies` zrušiť alebo ponechať
- [ ] Dohodnúť prioritu s produktom
- [ ] Pridať do hlavného ROADMAP_CURRENT.md keď bude čas
