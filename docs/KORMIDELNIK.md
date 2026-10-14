# Kormidelník — AI chat agent CMEP

> Interná technická dokumentácia chat agenta ("Kormidelník").
> Vetva: `feat/kormidelnik-agent`. Všetky citácie sú `súbor:riadok`
> v stave vetvy; každé tvrdenie je označené stavom (viď legenda nižšie).

## Legenda stavov

| Label | Význam |
|---|---|
| `implemented` | Kód existuje v repozitári a je napojený do produkčnej cesty. |
| `tested` | Existuje automatizovaný test, ktorý túto cestu reálne spúšťa. |
| `simulated` | Overené len cez fake/mock alebo izolovaný harness, nie reálnou službou. |
| `unverified` | Existuje v kóde, ale nebolo overené reálnym behom (bez testu / len staticky). |

Táto verzia dokumentu je **recon dávka** — všetok kód je prečítaný a citovaný,
ale **diagnostické behy** (izolovaný harness, load testy) sú v samostatnej
správe `docs/KORMIDELNIK_DIAGNOSTIKA.md`. Nič nižšie nie je označené ako
`tested`, ak to reálne nespustil test.

---

## 1. Čo Kormidelník je

Chat asistent platformy CMEP (Circular Materials Exchange Platform) — slovenský
B2B marketplace pre obehové materiály. Používateľ píše v prirodzenom jazyku;
agent:

1. **odpovie textom** (LLM),
2. **zavolá serverové nástroje** (vyhľadávanie firiem/ponúk, čítanie vlastných
   dát, admin čítanie) — `implemented`,
3. **vráti UI akcie** (navigácia, vyplnenie formulára, toast, karty) — frontend
   ich aplikuje na aktuálnu stránku — `implemented`,
4. **pamätá si konverzáciu** cez rolling summary — `implemented`.

Vstupný bod: `POST /api/v1/agent-platform/chat`
(`app/modules/agent_platform/presentation/chat_router.py:623`).

---

## 2. Celý tok jednej správy (end-to-end)

Poradové kroky v `user_ai_chat` (`chat_router.py:623-839`):

| # | Krok | Kód | Stav |
|---|---|---|---|
| 1 | Validácia vstupu (`message` 1-4000 znakov) | `UserAiChatRequest` `chat_router.py:496` | `implemented` |
| 2 | Prázdny text → `status="unavailable"` | `chat_router.py:634-641` | `implemented` |
| 3 | **Entitlement gate** (402/403) — admin obchádza | `_check_ai_entitlement` `chat_router.py:523-546` | `implemented` |
| 4 | `actor_id` z current_user; bez neho `unavailable` | `chat_router.py:648-655` | `implemented` |
| 5 | `session_id` = vstup alebo nové UUID | `chat_router.py:656` | `implemented` |
| 6 | Načítanie/pamäť: `get_or_create` + posledných 20 + summary → `build_history` | `chat_router.py:660-687` | `implemented` |
| 7 | **Intent klasifikácia** (deterministická) | `classify_intent` `chat_router.py:689` | `tested` (`test_intent_classifier.py`) |
| 8 | Zloženie system promptu (BASE + addendum + persona + page + intent hint) | `_build_system_prompt` `chat_router.py:204-224` | `tested` (`test_role_aware_prompt.py`, `test_page_context.py`) |
| 9 | **Security check** (heuristika; NEBLOKUJE okrem `block`) | `_apply_security_check` `chat_router.py:370-493` | `implemented` |
| 10 | Ak `decision == "block"` → neutrálna odpoveď `unavailable` | `chat_router.py:716-722` | `implemented` |
| 11 | **Orchestrátor** — LLM + tool loop (max 6 iterácií) | `orchestrator.respond` `chat_router.py:725` | `tested` (`test_phase3_pipeline.py` atď.) |
| 12 | Spracovanie prázdneho textu (client action → "Hotovo."; server tool → "Skúsil som…") | `chat_router.py:750-781` | `implemented` |
| 13 | Zápis `user` + `assistant` správy (best-effort) + detached summary | `chat_router.py:783-799` | `tested` (`test_summarizer.py`, `test_conversation_repository.py`) |
| 14 | Rozdelenie tool_calls na `client_actions` vs `server tool_calls` | `chat_router.py:810-817` | `implemented` |
| 15 | Voliteľná TTS syntéza (`voice_response`) | `synthesize_with_edge_tts` `chat_router.py:820-827` | `implemented` |
| 16 | Zloženie odpovede (`status`, `reply`, `source`, `cards`, `intent`, …) | `UserAiChatResponse` `chat_router.py:829-839` | `implemented` |

Odpoveď `UserAiChatResponse` (`chat_router.py:511-520`):
`status`, `reply`, `source`, `session_id`, `tool_calls`, `client_actions`,
`cards`, `audio_base64`, `intent`.

---

## 3. Orchestrátor a tool loop

`app/modules/agent_platform/application/agent/agent_orchestrator.py`.

- **Max iterácií**: `MAX_TOOL_ITERATIONS = 6` (`:47`). Po prekročení vráti
  text „Prepáč, nepodarilo sa mi dokončiť odpoveď v rozumnom čase."
  (`:490-495`).
- **Max kariet na turn**: `MAX_TOTAL_CARDS = 24` (`:49`), dedup podľa
  `(type, id)` (`:123-129`).
- **Poradie pre každý tool call** (`:218-488`):
  1. publish `TOOL_REQUESTED` (best-effort) — `:224-230`
  2. parse argumentov z JSON (`:232-242`; neplatný JSON → `{}`)
  3. ak je to **client action** → NEvykonáva sa handler, len validácia — `:247`, `:372-418`
  4. **policy** `AllowlistPolicyEngine.decide` → `DENY` / `REQUIRE_APPROVAL` — `:253-301`
  5. **permission** `ActorToolPermissionEngine.authorize`, scope musí byť
     namapovaný (`tool_scope_unmapped`) — `:303-368`
  6. **handler** `handle(ToolRequest)` → `executed` / `failed` / `exception` — `:420-474`
  7. `finally`: audit + publish `TOOL_EXECUTED/FAILED/DENIED/APPROVAL_REQUESTED` — `:475-488`
- **Karty**: `_collect_cards` volá `card_builder` len po **úspešnom** server
  tooli (`:453-459`); zlyhanie buildera sa prehltne (`:118`).
- **Provider**: `OrchestrationResult.provider = response.provider_metadata.get("provider")`
  (`:206`) — `source` v odpovedi už nie je hardcoded (Blok 4).

Kritické: **orchestrátor sám neautorizuje** — autorizácia je v policy/permission
a v handleroch naviazaných na scope volajúceho (`dependencies.py:93-283`).

---

## 4. Tool katalóg (čo agent vie)

Zdroj schém: `app/modules/agent_platform/infrastructure/tools/tool_schemas.py`.

### 4.1 Serverové READ nástroje (každý prihlásený)

| Nástroj | Handler | Scope | Stav |
|---|---|---|---|
| `search_companies` | `CmepCompanySearchHandler` | `companies:search` | `implemented` |
| `search_listings` | `CmepListingSearchHandler` | `listings:search` | `implemented` |
| `search_nearby_companies` | `CmepNearbyCompaniesHandler` | `recommendations:read` | `implemented` |
| `get_listing_transport` | `CmepListingTransportHandler` | `recommendations:read` | `implemented` |
| `get_my_listings` | `CmepUserToolsHandler` | `listings:read` | `implemented` |
| `get_my_company` | `CmepUserToolsHandler` | `listings:read` | `implemented` |
| `get_listing_details` | `CmepUserToolsHandler` | `listings:read` | `implemented` |
| `get_listing_stats` | `CmepUserToolsHandler` | `listings:read` | `implemented` |
| `get_company_listings` | `CmepUserToolsHandler` | `listings:read` | `implemented` |
| `get_recommendations` | `CmepUserToolsHandler` | `listings:read` | `implemented` |

Mapovanie scope: `dependencies.py:120-158`.

### 4.2 Admin-only nástroje (pripnuté len adminovi)

`dependencies.py:160-182`:

| Nástroj | Scope |
|---|---|
| `project_read_file` | `admin:read` |
| `project_list_dir` | `admin:read` |
| `get_platform_stats` | `admin:read` |
| `get_recent_activity` | `admin:read` |
| `get_companies_with_tiers` | `admin:read` |
| `get_my_company_context` | `admin:read` |

`ProjectReadHandler` (`infrastructure/tools/project_read.py`) — READ-ONLY
čítanie repozitára: fixný `_ALLOWED_ROOT` (`:42`), blokácia `..`, `\`, NUL,
`%2e`, denied adresárov (`.git`, `node_modules`, …), symlink containment
(`:100-127`), max 1 MB / 100k znakov (`:44-45`), len textové prípony (`:49`).
Testy: `test_project_read_tools.py`, `test_project_read_production.py`.

### 4.3 Client actions (frontend vykoná, backend len validuje)

Zdroj: `tool_schemas.py:591-616`. Zoznam `CLIENT_ACTION_NAMES` je **jediný
zdroj** — `chat_router.CLIENT_TOOL_NAMES = CLIENT_ACTION_NAMES`
(`chat_router.py:227`).

Navigácia: `navigate(url)`, `open_listing`, `open_company`, `open_new_listing`,
`open_listings_list`, `open_companies`, `open_dashboard`, `open_inquiries`,
`open_new_company`, `open_documents`, `open_new_document`, `open_chat`,
`open_settings`.
UI: `fill_form_field(field, value)`, `highlight_field(field)`,
`show_toast(message, level)`.

**Admin-only client action**: `open_admin` (`tool_schemas.py:580-587`,
`ADMIN_CLIENT_ACTION_SCHEMAS` `:611`) — LLM ho dostane len admin
(`dependencies.py:182`).

Validácia: `infrastructure/tools/client_action_validation.py`:

- `_SAFE_ID_RE = ^[A-Za-z0-9_-]{1,64}$` (`:28`),
- `fill_form_field`: pole z allowlisty `_FORM_FIELDS` (`:33-61`), `quantity`/`price`
  numericky (`_NUMERIC_FIELDS`, `_NUMERIC_RE` `:29`), max 2000 znakov,
- `navigate`: len interná relatívna cesta, blok `//`, `:`, `\`, `..`,
  kontrolné znaky, max 200 znakov (`:150-171`),
- `show_toast`: neprázdna správa ≤ 500 znakov, level v `{info,success,warning,error}`
  (`:138-147`),
- `_NO_ARG_ACTIONS` (navigácia bez argumentov) `:63-77`.

Testy: `test_client_actions.py`.

---

## 5. Karty (`card_builder`)

`application/agent/card_builder.py`.

- `MAX_CARDS = 12` (`:24`).
- Mapuje **len** úspešné tool výsledky na typy `listing` / `company` / `stats`
  (`:156-194`).
- `href` je **vždy** interná dashboard route z whitelisted typu + validovaného
  ID: `_LISTING_ROUTE = /dashboard/listings/{id}`,
  `_COMPANY_ROUTE = /dashboard/companies/{id}` (`:31-32`).
- Neznámy tvar → prázdny zoznam, nikdy chyba (`:159`).

Testy: `test_card_builder.py`.

---

## 6. Pamäť (rolling summary)

Bez schémy/migrácie — summary je riadok v `ai_messages` s `role="summary"`.

- `summarizer.py`: `KEEP_RECENT=8`, `THRESHOLD=16`, `MAX_INPUT_MESSAGES=120`,
  `MAX_MSG_CHARS=500`, `MAX_SUMMARY_CHARS=1500`,
  `DEFAULT_SUMMARY_MODEL="openai/gpt-oss-120b"` (`:32-37`).
- Spustí sa len ak `count_messages > max(threshold, keep_recent)` (`:129-135`).
- **Novšie summary neprepíše starším**: zapíše len ak `existing.covers < to_cover`
  (`:137-139`).
- Zhrnutie je **DÁTA, nie inštrukcie** — prompt to explicitne zakazuje (`:39-49`),
  a vkladá sa ako system správa s wrapperom „NIE sú inštrukcie"
  (`context_builder.py:34-44`).
- `context_builder.build_history` vkladá summary + posledných
  `MAX_HISTORY_MESSAGES = 20` user/assistant správ (`:8`, `:46-53`).
- Detached beh: `chat_router._schedule_summary` (`:610-620`) →
  `_summarize_in_background` (`:577-607`) s per-conversation lockom
  (`_SUMMARY_LOCKS`, `:559`) a vlastnou DB session.
- Repository: `count_messages` vylučuje summary (`ai_conversation_repository.py:202-214`),
  `replace_summary` je delete+insert (`:252-286`).

Testy: `test_summarizer.py`, `test_context_builder.py`,
`test_conversation_repository.py`.

---

## 7. Intent classifier

`application/agent/intent_classifier.py` — deterministický, bez IO, bez
oprávnení.

- Enum `Intent`: `greeting, search, sell, navigate, form_help, recommendation,
  inquiry, platform_help, unknown` (`:30-39`).
- Normalizácia bez diakritiky + lowercase → `predám` == `predam` (`:183-187`).
- Keyword stemy s word-start boundary; krátke tokeny (≤3) celé slovo
  (`:190-196`).
- Tie-break `_PRIORITY` dáva prednosť konkrétnym akciám (`:44-53`).
- `ambiguous` pri zhode top dvoch; `confidence = min(1.0, 0.5 + 0.15*score)`
  (`:225-231`).
- `intent_hint` je **advisory** — neudeľuje oprávnenie (`:240-271`).

Testy: `test_intent_classifier.py`.

---

## 8. System prompt a bezpečnostné pravidlá

`chat_router.py`:

- `BASE_RULES` (`:47-123`) — nástroje, „kedy pomáhaš" (Blok 7 FIX 5, `:91-94`),
  „NIKDY NEROBIŤ" (`:96-116`), jazyk + max 4 odstavce.
- `ARCHITECT_ADDENDUM` (`:129-161`) — len admin; `open_admin` v zozname
  (`:145`).
- `CUSTOMER_ADDENDUM` (`:167-171`).
- `PERSONA_ADDENDA` (`:174-196`): `bystry`, `drzy`, `lenivy`, `op`.
- `_build_page_context_block` (`:267-301`) — sanitizuje path (`_SAFE_ROUTE_RE`
  `:250`), typ stránky (`_KNOWN_PAGE_TYPES` `:230-249`), entity id
  (`_SAFE_CONTEXT_ID_RE` `:251`), entity label (`_sanitize_context_text`
  `:254-264` — odstráni kontrolné znaky/newlines, oreže).
- `_detect_security_patterns` (`:304-358`): `prompt_injection` (0.9),
  `data_leakage` (0.8), `permission_escalation` (0.85).
- `_apply_security_check` (`:370-493`): **vlastná DB session** (aby commit
  neovplyvnil hlavný tok), zapisuje observation + signal + alert; vráti
  najvážnejší decision. **NEBLOKUJE chat** — pozri nižšie Riziká.

---

## 9. Frontend napojenie

- `apps/web/src/lib/ai-agent/dashboard-routes.ts` — jediný zdroj dashboard rout
  (root, listings, listingNew, listing(id), companies, companyNew, company(id),
  inquiries, documents, documentNew, chat, settings, admin) + `safeEntityId`
  (`SAFE_ID = ^[A-Za-z0-9_-]{1,64}$`).
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`:
  - timeout 60s (Blok 7 FIX 1),
  - `navigate` handler (Blok 7 FIX 2),
  - `show_toast` lokálny toast (Blok 7 FIX 3),
  - `NO_ARG_NAV_ACTIONS` tabuľka (Fáza 7),
  - truthful rendering (Fáza 8).
- `page-context.ts`, `form-fields.ts`, `use-ai-form-filling.ts` — kontext
  stránky a polia formulárov (Fáza 4).
- `apps/web/src/app/dashboard/admin/page.tsx` — client-side admin guard
  (`useIsPlatformAdmin` → redirect).

Frontend testy: **vitest binárka chýba** v `node_modules` → nedajú sa spustiť
(`unverified`).

---

## 10. Konfigurácia a prostredie

- AI reťaz: `ChainModelGateway([GroqModelGateway, CerebrasModelGateway,
  MistralModelGateway])` — prvý úspech vyhráva (`dependencies.py:266-272`).
- Model posielaný orchestrátorom: `"openai/gpt-oss-120b"`
  (`dependencies.py:280`).
  - **Pozor**: Groq `request.model` rešpektuje; Cerebras aj Mistral používajú
    `CEREBRAS_MODEL`/`MISTRAL_MODEL` env ako autoritu a `request.model`
    ignorujú (Blok 8). Model routing je zdroj možných 404.
- Rate limit: `/agent-platform/chat` 20/60 + 120/3600;
  `/agent-platform/voice` 10/60 + 60/3600
  (`app/.../rate_limit_middleware.py`).
- Env kľúče (mimo gitu): `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `MISTRAL_API_KEY`,
  `CEREBRAS_MODEL`, `MISTRAL_MODEL` (posledné dve nie sú v `.env` v repe).

---

## 11. Testy (existujúce, `app/modules/agent_platform/tests/`)

`test_chat_gate.py` (entitlement), `test_role_aware_prompt.py`,
`test_page_context.py`, `test_intent_classifier.py`, `test_summarizer.py`,
`test_context_builder.py`, `test_conversation_repository.py`,
`test_card_builder.py`, `test_client_actions.py`, `test_agent_policy_gate.py`,
`test_agent_permission_gate.py`, `test_agent_audit.py`, `test_admin_tools.py`,
`test_project_read_tools.py`, `test_project_read_production.py`,
`test_openlist_readonly.py`, `test_phase3_pipeline.py`,
`test_phase4_1_dispatcher.py`, `test_phase4_async_execution.py`,
`test_phase5_tool_wiring.py`.

Celá sada (celý repo, posledné overenie): **1115 passed, 1 xfailed**.

---

## 11b. Diagnostický beh — `verified` (2026-10-11)

Izolovaný harness `$TMPDIR/kormidelnik_diag/harness.py` (+ `latency_probe.py`,
`latency_probe2.py`, `uuid_probe*.py`) beží proti **reálnemu Postgresu 18.6**
(port 5433, asyncpg = produkčný dialekt), aby výsledky neboli sqlite-špecifické.
Externé služby (LLM gateway, entitlement) sú simulované cez `dependency_overrides`;
žiadne produkčné zápisy. 36 kontrol v skupinách:

- **A** orchestrátor rozhodovacie cesty (policy/permission/handler/timeout)
- **B** prompt (role/persona), page-context sanitizácia, intent, security, karty
- **C** rolling summary proti reálnemu repozitáru (threshold, persist, monotónnosť)
- **D** HTTP end-to-end cez ASGITransport (401/402/403/200/422/404, unavailable cesty)
- **E** paralelné/zaťažové behy (orchestrátor N=40, HTTP+DB N=20, izolácia pamäte)
- **F** DB portabilita (SQLite vs Postgres, UUID object vs string)

**Výsledok: 34 PASS, 2 FAIL** (oba reálne nálezy, nie chyba harnessu).

| # | Severita | Zistenie (`verified`) | Dôkaz | Dopad | Stav (2026-10-11) |
|---|---|---|---|---|---|
| N1 | stredná | Serverový tool zamietnutý policy (aj **neznámy** tool) sa aj tak objaví v `collected_calls` → v odpovedi `tool_calls`. `append()` pre ne-client tool beží **pred** policy checkom. | `agent_orchestrator.py` (pôvodne `:247-251` append pred `:253` policy) | Response hlási nástroj, ktorý sa nikdy nevykonal a bol zamietnutý → zavádzajúca telemetria/`server_tool_calls`. **Bez bezpečnostného dopadu** (nevykonal sa). | **OPRAVENÉ** — `append` presunutý až po policy+permission+handler-exists; 6 nových regresných testov `test_orchestrator_collected_calls.py` (povolený/zamietnutý/neznámy/unmapped/denied/client-action). |
| N2 | nízka (dev/test) | `get_or_create` posiela `user_id`/`company_id` ako **string** do `UUID(as_uuid=True)` stĺpca bez konverzie (`_uuid_or_none` sa tu nepoužije). Postgres to strpí; SQLite padá (`'str' object has no attribute 'hex'`). Testy posielajú UUID objekty → bug maskujú. | `ai_conversation_repository.py` `get_or_create`; F1(ok)/F2(fail)/F3(ok) | Produkcia (Postgres) **OK**. Na SQLite (dev/smoke) `get_or_create` padá → `chat_router.py:678-687` to spolchne → **pamäť ticho vypnutá**. | **OPRAVENÉ** — `user_id`/`company_id` prechádzajú cez `_uuid_or_none` (helper rozšírený o `uuid.UUID \| None`); 5 nových kontrakt testov v `test_conversation_repository.py` (UUID objekt/string/None/idempotencia/chyba). SQLite 8 passed; **Postgres+asyncpg 5/5** (standalone probe `n2_pg_contract.py`, real PG 18.6 — oficiálny fixture je hardcoded SQLite). |
| N3 | stredná | Chat cesta robí **3 commity/turn** (`get_or_create` + 2× `append_message`) + detached sumarizér otvára ďalšiu session/turn → pri 20 paralelných requestoch sa zápisy serializujú. | `chat_router.py:661,785-794,799`; `ai_conversation_repository.py:139,196`; `latency_probe2` | p50 pri 20 paralelných: `/health` **48ms**, chat+reálna DB **2674ms**, chat bez DB write 385ms. Namerané lokálne (Android Postgres, 5ms fake gateway) — Render sa môže líšiť, štruktúra commit-per-message je však fixná. | **ZOSTÁVA (zdokumentované, bez implementácie)** — počet commitov ani transakčná architektúra sa nemení (rozhodnutie 2026-10-11). Návrh optimalizácie vr. záťažových testov: sekcia 11c. |

### 11c. N3 — návrh optimalizácie (NIE implementované)

**Meranie (spôsob):** `latency_probe.py` + `latency_probe2.py` cez `httpx.ASGITransport`
+ `dependency_overrides` (fake gateway 5ms, fake user/entitlement), reálny Postgres 18.6,
Android (Termux). 20 paralelných requestov, p50 z `asyncio.gather`; prvý request = warmup
(nie je v meraní).

| Scenár (N=20 paralelne) | wall | p50 | max |
|---|---|---|---|
| `GET /health` (transport baseline) | 88 ms | 48 ms | 79 ms |
| chat + reálna DB (default) | 2999 ms / 1301 ms | 2674 ms / 1062 ms | 2979 ms / 1298 ms |
| chat + NULL konverzačný repo (bez DB write) | 477 ms | 385 ms | 452 ms |

Interpretácia: transport je rýchly; **serializácia je v DB vrstve** (3 commity/turn
`get_or_create`+2×`append_message`, každý so session commitom, plus detached sumarizér =
session navyše). `wall ≈ 20 × single-request` → zápisy sa radia. Sekvenčný baseline
~70–98 ms/request ukazuje, že každý commit nesie režiu (fsync na Android f2fs; na Rende
sa čísla líšia, ale štruktúra commit-per-message je fixná).

**Návrh (nevykonané):**
1. `get_or_create` + 2× `append_message` zlúčiť do **jednej transakcie** (jeden commit/turn):
   `begin()` na request session, `flush()` namiesto `commit()` po každom messagi.
   Očakávaný efekt: ~3× menej commitov → záťažová krivka sa posunie.
2. Sumarizér: len ak `count_messages > THRESHOLD` a konverzácia nebola sumarizovaná
   v posledných N minútach (session reusable, nie commit-anotácia).
3. **Regresné testy pred nasadením:** `test_conversation_repository` s fake counterom
   commitov (spy na `Session.commit`) → assert 1 commit/turn; load test
   `20× chat` p50 < cca 400 ms pri fake gateway 5 ms (porovnateľné s "bez DB write").
4. **Záťažový test:** opakovať `latency_probe2` pred/po zmene — rozdiel p50 + wall
   je kritérium akceptácie. Žiadna zmena sa nenasadzuje bez nového merania.

---

## 12. Otvorené body / riziká (`unverified`)

| # | Riziko | Dôkaz | Dopad |
|---|---|---|---|
| R1 | Security check blokuje LEN vzory mapované na `block` v `DefaultSecurityEngine`: `data_leakage` a `permission_escalation` (`security_engine.py:15-26`). `prompt_injection` → `alert` (chat **pokračuje**). Frázy sa matchujú presne (substring), takže obchvat je triviálny. Blokácia na HTTP úrovni je **overená** v diagnostike D8 (blocked → 200 `unavailable`, orchestrátor sa nezavolá, `gw_calls=0`); zostáva `unverified` len sila samotných vzorov. | `chat_router.py:304-358`, `:716-722`; `security_engine.py:15-26` | Prompt injection prejde do LLM; chránia ho len textové pravidlá v prompte. |
| R2 | Model routing: Cerebras/Mistral ignorujú `request.model`; orchestrátor posiela gpt-oss-120b. Pri výpadku Groq môže fallback vracať 404 namiesto odpovede. | `dependencies.py:280`, Blok 8 | Degradácia odpovedí pri výpadku primárneho providera. |
| R3 | Chat odpoveď má len `unavailable` pri chybe; nevracia sa HTTP kód (vždy 200). Chýbajúca granularita pre klienta. | `chat_router.py:733-748` | Klient nerozozná typ zlyhania. |
| R4 | `_build_page_context_block` vkladá `form_fields` bez validácie hodnôt (len `str(f)`); path/id/label sanitizované, polia nie. | `chat_router.py:289-290` | Teoretický vektor cez klientsky poslané polia (nízka). |
| R5 | Detached summary beží s `asyncio.create_task` bez `await` — pri viacworkerovom deployi (`_SUMMARY_LOCKS` je proces-lokálny) môžu dva workery sumarizovať súčasne. | `chat_router.py:554-620` | Duplicitná práca; monotónny `covers` guard bráni regresii. |
| R6 | Frontend `vitest` sa nedá spustiť (chýba binárka) → UI logika `dashboard-routes`/handlerov je `unverified` behom. | `node_modules` | Navigačné cesty neoverené automaticky. |
| R7 | `open_admin` je v `CLIENT_ACTION_NAMES` (allowlist policy pre všetkých), hoci schéma sa pripína len adminovi. Klient môže teoreticky poslať `open_admin` ručne. | `tool_schemas.py:611-616`, `dependencies.py:182`, `client_action_validation.py:75` | Nízke — UI má vlastný admin guard (`/dashboard/admin`). |

---

## 13. Súvisiace súbory (prehľad)

```
app/modules/agent_platform/
├── presentation/
│   ├── chat_router.py              # endpoint, prompt, security, page-context
│   └── dependencies.py             # DI: gateway chain, tools, scopes, audit
├── application/
│   ├── agent/
│   │   ├── agent_orchestrator.py   # tool loop, policy/permission gate
│   │   ├── card_builder.py         # UI karty
│   │   └── intent_classifier.py    # deterministický intent
│   └── memory/
│       ├── summarizer.py           # rolling summary
│       └── context_builder.py      # história + summary do promptu
├── infrastructure/
│   ├── ai/                         # groq/cerebras/mistral/chain gateways
│   ├── tools/
│   │   ├── tool_schemas.py         # schémy + CLIENT_ACTION_NAMES
│   │   ├── client_action_validation.py
│   │   └── project_read.py         # admin READ-ONLY repo
│   └── persistence/
│       └── ai_conversation_repository.py
└── domain/memory/                  # AiConversation, AiMessage, AiSummary
apps/web/src/lib/ai-agent/          # page-context, form-fields, routes
apps/web/src/features/agent-platform/components/ai-chat-widget.tsx
```
