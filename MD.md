Rozumiem. Máš 5 duplikovaných odpovedí. Vrátim ti jeden čistý dokument — strom (kocky) + handoff bez duplikátov. Skopíruj si to do MD.md (prepíš starý).

---

CMEP — Master Backlog & Handoff

Dátum: 2026-10-07 · HEAD: 5c89eac · Branch: main == origin/main · Alembic head: c7d8e9f0a1b2

---

ČASŤ 1 — ČO SA DNES SPRÁVILO (2026-10-07)

11 commitov, 10 sessions uzavretých (A–J).

# Commit Popis
1 aab3d72 HISTORY/SESSION_STATE — E2E verifikácia
2 768fb19 docstring + error_responses AI draft route → 409
3 543c7bb AI draft multi-company fix (vyberie firmu s AI tierom)
4 36c2934 HISTORY zaevidovanie B+C
5 2146852 Unit test AI draft route (4 testy)
6 0e089d7 Meta Pixel integrácia (kód, bez ID)
7 621a43b .env.example placeholders (Pixel + GoPay)
8 2fbbc49 Unit test /billing/status
9 d3d83ad Logo firmy (migrácia + BE + FE)
10 1820220 Aktívne ponuky na detaile firmy + AI panel i18n + GoPay company_id fix
11 5c89eac SESSION_STATE close

V produkcii overené: AI draft POST /ai-draft → 200, provider=groq. Publish → 200, marketplace OK.

---

ČASŤ 2 — STROM OTVORENÝCH PRÁC

```
                    ┌─────────────────────────────┐
                    │  ROOT: vsetko co nie je     │
                    │  na 100% hotove             │
                    └──────────────┬──────────────┘
                                   │
       ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
       ▼           ▼           ▼       ▼           ▼           ▼
   ╔═══════╗  ╔═══════╗  ╔═══════╗ ╔═══════╗  ╔═══════╗  ╔═══════╗
   ║   A   ║  ║   B   ║  ║   C   ║ ║   D   ║  ║   E   ║  ║   F   ║
   ║AI RT  ║  ║EXTERN ║  ║FEATUR ║ ║INFRA  ║  ║ANDROID║  ║TECH   ║
   ║WOW    ║  ║CREDS  ║  ║       ║ ║       ║  ║       ║  ║DEBT   ║
   ╚═══╤═══╝  ╚═══╤═══╝  ╚═══╤═══╝ ╚═══╤═══╝  ╚═══╤═══╝  ╚═══╤═══╝
       │           │           │       │           │           │
       ▼           ▼           ▼       ▼           ▼           ▼
```

A) AI REAL-TIME ASISTENT  ← TOP PRIORITA (WOW 10/10)

```
                 ┌──────────────────────┐
                 │ Firma vytvara ponuku │
                 │ AI komunikuje v case │
                 │ Text sa pise pred nou│
                 └──────────┬───────────┘
                            │
      ┌──────────┬──────────┼──────────┬──────────┐
      ▼          ▼          ▼          ▼          ▼
  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌────────┐
  │  A1   │ │  A2   │ │  A3   │ │  A4   │ │   A5   │
  │BACKEND│ │FRONT- │ │PERSONA│ │VIZUÁL │ │ HLAS   │
  │  SSE  │ │ END   │ │PICKER │ │TYPING │ │(FUTURE)│
  └───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘ └────────┘
      │         │         │         │
  ┌───┴───┐ ┌───┴───┐ ┌───┴───┐ ┌───┴───┐
  │A1.1   │ │A2.1   │ │A3.1   │ │A4.1   │
  │novy   │ │fetch +│ │kopiruj│ │kurzor │
  │POST   │ │Readab.│ │personu│ │blika  │
  │/stream│ │Stream │ │       │ │"AI…"  │
  ├───────┤ ├───────┤ ├───────┤ ├───────┤
  │A1.2   │ │A2.2   │ │A3.2   │ │A4.2   │
  │Groq   │ │setPar-│ │+perso-│ │progre-│
  │stream=│ │tial   │ │na v   │ │ss bar │
  │True   │ │       │ │req    │ │       │
  ├───────┤ ├───────┤ ├───────┤ ├───────┤
  │A1.3   │ │A2.3   │ │A3.3   │ │A4.3   │
  │yield  │ │render │ │system │ │"Stop" │
  │chunk  │ │panel  │ │prompt │ │       │
  ├───────┤ ├───────┤ ├───────┤ ├───────┤
  │A1.4   │ │A2.4   │ │A3.4   │ │A4.4   │
  │fallba-│ │fallba-│ │local- │ │live   │
  │ck POST│ │ck POST│ │Storage│ │feedb. │
  └───────┘ └───────┘ └───────┘ └───────┘
```

Commit: feat(listings): streaming ai draft (SSE) + persona + typing effect
Odhad: A1+A2 = 1 deň · A3 = 2 hod · A4 = 3 hod · A5 = neskôr

B) EXTERNÉ INTEGRÁCIE (čakajú na credentials)

```
                  ┌────────────────────┐
                  │  B) EXTERNE        │
                  │  Cakaju na creds   │
                  └─────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
         ┌─────────┐                 ┌─────────┐
         │   B1    │                 │   B2    │
         │ GOPAY   │                 │META     │
         │ platby  │                 │PIXEL    │
         └────┬────┘                 └────┬────┘
              │                           │
    ┌─────┬───┼─────┬─────┐               │
    ▼     ▼   ▼     ▼     ▼               ▼
  ┌───┐┌───┐┌───┐┌───┐┌───┐          ┌──────┐
  │B1.││B1.││B1.││B1.││B1.│          │B2.1  │
  │ 1 ││ 2 ││ 3 ││ 4 ││ 5 │          │Pixel │
  │cre││DB ││FE ││san││pro│          │ID    │
  │ds ││tab││str││dbox│d  │          └───┬──┘
  └───┘└───┘└───┘└───┘└───┘              │
                                       ┌──┴──┐
                                       │B2.2 │
                                       │env +│
                                       │rebu.│
                                       └──┬──┘
                                          │
                                       ┌──┴──┐
                                       │B2.3 │
                                       │Event│
                                       │Mgr  │
                                       └─────┘
```

Commit: feat(billing): activate gopay · feat(web): meta pixel live
Odhad: B1 = 2 hod (s creds) · B2 = 30 min

C) FEATURES NA DOKONČENIE

```
                  ┌────────────────────┐
                  │  C) FEATURES       │
                  └─────────┬──────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
     ┌───────┐          ┌───────┐          ┌───────┐
     │  C1   │          │  C2   │          │  C3   │
     │PUSH   │          │PREDIK-│          │PREKLA-│
     │PO PUB │          │CIA    │          │DY     │
     └───┬───┘          └───┬───┘          └───┬───┘
         │                  │                  │
   ┌─────┼─────┐       ┌────┼────┐        ┌────┼────┐
   ▼     ▼     ▼       ▼    ▼    ▼        ▼    ▼    ▼
 ┌───┐┌───┐┌───┐   ┌───┐┌───┐┌───┐    ┌───┐┌───┐┌───┐
 │C1.││C1.││C1.│   │C2.││C2.││C2.│    │C3.││C3.││C3.│
 │ 1 ││ 2 ││ 3 │   │ 1 ││ 2 ││ 3 │    │ 1 ││ 2 ││ 3 │
 │sub││tri││end│   │ena││ove││bri│    │gre││kľú││pre│
 │scr││ggr││poi│   │ble││riť││dge│    │p  ││če ││lo │
 │mod││pub││nt │   │dev││dá-││do │    │    ││   ││žiť│
 │el ││lish││  │   │   ││ta ││rec│    │    ││   ││   │
 └───┘└───┘└───┘   └───┘└───┘└───┘    └───┘└───┘└───┘
```

Commit: feat(notifications)… · feat(prediction)… · i18n: extract…
Odhad: C1 = 1 deň · C2 = 1 deň · C3 = 3 hod

D) INFRA / PRODUCTION

```
                  ┌────────────────────┐
                  │  D) INFRA          │
                  └─────────┬──────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
  ┌──────┐               ┌──────┐               ┌──────┐
  │  D1  │               │  D2  │               │  D3  │
  │RENDER│               │ALEMB │               │GITHUB│
  │BILL  │               │IC na │               │ACTION│
  │failed│               │prod  │               │start.│
  └──┬───┘               └──┬───┘               └──┬───┘
     │                      │                      │
     ▼                      ▼                      ▼
  doplniť                overiť                 Support
  kartu                  Dockerfile             ticket
  v Render               CMD                    status
```

Odhad: D1 = 5 min · D2 = 15 min · D3 = čaká na GitHub

E) ANDROID APP (greenfield)

```
                  ┌────────────────────┐
                  │  E) ANDROID        │
                  │  V repe NIC        │
                  └─────────┬──────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
         ┌─────────┐                 ┌─────────┐
         │   E1    │                 │   E2    │
         │CAPACITOR│                 │ REACT   │
         │web obal │                 │ NATIVE  │
         │2 týždne │                 │ 6-8 týž.│
         └─────────┘                 └─────────┘
```

Odporúčanie: odložiť na Q1 2026, kým nemáme 100 firiem na webe.

F) TECH DEBT (P2)

```
                  ┌────────────────────┐
                  │  F) TECH DEBT      │
                  └─────────┬──────────┘
                            │
   ┌──────────┬─────────────┼─────────────┬──────────┐
   ▼          ▼             ▼             ▼          ▼
 ┌───┐     ┌───┐         ┌───┐         ┌───┐
 │F1 │     │F2 │         │F3 │         │F4 │
 │up-│     │fla│         │Re-│         │ma-│
 │loa│     │ky │         │dis│         │ss │
 │d/ │     │te-│         │v  │         │as-│
 │308│     │st │         │Ter│         │sig│
 └───┘     └───┘         └───┘         └───┘
   │         │             │             │
 redirect  mockovanie   fakeredis     manuálny
 _slashes  lookup_ico   fixture       test PATCH
```

Odhad: 1 deň celé

---

ČASŤ 3 — ODPORÚČANÉ PORADIE

# Čo Odhad Blokátor
1 A) AI real-time streaming 1 deň —
2 B1) GoPay aktivácia 2 hod creds
3 B2) Meta Pixel live 30 min Pixel ID
4 D1+D2) Render billing + Alembic 30 min karta
5 A3) Persona picker 2 hod A1+A2
6 C1) Push po publishi 1 deň —
7 C2) Predikcia 1 deň —
8 C3) Preklady 3 hod —
9 F) Tech debt 1 deň —
10 E) Android mesiace —

---

ČASŤ 4 — HANDOFF: FAKTY ZO SYSTÉMU

A) AI streaming — kde to je

· app/modules/listings/application/listing_drafter.py — ListingDrafter.draft(*, prompt) -> DraftedListing (async), is_provider_configured() (statická)
· app/modules/agent_platform/infrastructure/ai/groq_gateway.py — pozor: nie infrastructure/groq_gateway.py, ale infrastructure/ai/groq_gateway.py
· apps/web/src/lib/api/http.ts — NEPODPORUJE stream → treba raw fetch() pre SSE
· apps/web/src/features/listings/components/ai-draft-panel.tsx — BUG: kontroluje status === 403, ale BE vracia 409

Prvý diagnostický príkaz:

```bash
cat app/modules/agent_platform/infrastructure/ai/groq_gateway.py
```

B1) GoPay — kde to je

· app/modules/billing/presentation/router.py — _cfg(), _ready(), _token(), POST /checkout, GET|POST /notify, GET /status
· Chýba: migrácia billing_transactions, FE stránka /dashboard/billing, credentials
· BUG: int(cfg["goid"]) bez try/except → spadne ak GOID nie je číslo

B2) Meta Pixel

· Kód v layout.tsx hotový, čaká na NEXT_PUBLIC_META_PIXEL_ID

C1) Push po publishi

· NotificationEntity: user_id, type, title, message, is_read, related_entity_id
· Notifikácia je per-user_id, NIE per-company_id → treba prejsť membership
· accepted_material_types je str | None, formát neznámy → overiť pred implementáciou

C2) Predikcia

· app/modules/prediction/ — 16 súborov v domain/
· PREDICTION_SERVICE_ENABLED flag v application/config.py
· prediction_bridge.py už existuje a je importovaný v recommendations/application/service.py → len ho zapnúť

D2) Alembic na Renderi

· Dockerfile nemá alembic upgrade head
· render.yaml neexistuje
· → migrácia c7d8e9f0a1b2 nebeží na prod automaticky

F) Tech debt — stav

· F1: uploads/presentation/router.py riadky 102, 169, 209, 277
· F2: test_company_transition.py:18 UŽ MÁ mock_lookup_ico → možno už vyriešené
· F3: 9 testov chce Redis na 127.0.0.1:6379
· F4: PATCH testy chýbajú

---

ČASŤ 5 — ZNÁME BUGY (3)

1. ai-draft-panel.tsx — if (status === 403) → má byť 409
2. billing/checkout — int(cfg["goid"]) bez try/except
3. Chýba tabuľka billing_transactions

---

ČASŤ 6 — PRAVIDLÁ

· Žiadny git reset --hard, git checkout --, git clean
· PRISNYR.txt — nikdy nemazať, necommitnúť
· Jeden commit = jedna logická zmena
· Push iba s explicitným OK
· Žiadne secrets do chatu
· Pred editom: diagnostika → dôkaz → minimálna úprava → verify
· Master režim: kolá (Kolo 1 = krok 1 všetkých sessions, atď.)

---

~280 riadkov. Žiadny duplikát. Stromy zachované. Handoff fakty bez opakovania.

Skopíruj si to do MD.md (prepíš starý 1700-riadkový).
