# CMEP Integrations — README

## Prehľad

Tento adresár obsahuje dokumentáciu pre nový modul externých integrácií
v rámci existujúcej platformy CMEP (TRČ — Circular Materials Exchange Platform).

Modul `app/modules/integrations/` umožní firmám pripájať externé systémy
(ERP, sklad, účtovníctvo, doprava) a synchronizovať dáta s CMEP.

## Dokumenty

| Súbor | Obsah |
|---|---|
| INVENTORY.md | Inventúra existujúceho stavu (Etapa 1) |
| ARCHITECTURE.md | Cieľová architektúra a dátové toky (Etapa 2) |
| FILE_CATALOG.md | Katalóg všetkých nových súborov |
| API.md | API rozhranie — endpointy a schémy |
| SECURITY.md | Bezpečnostné požiadavky a mechanizmy |
| SYNCHRONIZATION.md | Synchronizácia — stavy, idempotencia, retry |
| IMPLEMENTATION_PLAN.md | Implementačný plán rozdelený na etapy |

## Stav

- ✅ Etapa 1 — Inventúra dokončená
- ✅ Etapa 2 — Architektúra dokončená
- ⏸️ Etapa 3 — Implementácia jadra (čaká na schválenie)
- ⏸️ Etapa 4 — Synchronizácia (čaká)
- ⏸️ Etapa 5 — Frontend (čaká)
- ⏸️ Etapa 6 — Záverečné overenie (čaká)

## Pravidlá

- Žiadny deploy, commit ani push
- Žiadne produkčné zásahy
- Žiadne databázové migrácie proti produkcii
- Chránené súbory neupravovať bez schválenia
- Tajné údaje nikdy neodhaľovať
- Každá zmena musí mať dôvod a test

## Ďalší krok

Po schválení Etapy 1 a 2 prejsť na Etapu 3A — doménové jadro a šifrovanie.
