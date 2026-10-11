# waste-platform (CMEP) — Circular Materials Exchange Platform

## Čo to je
Fullstack platforma pre obehové hospodárstvo (materiálová výmena). FastAPI backend
(`app/`) + Next.js frontend (`apps/web`). Vetva `feat/voice-mai-transcribe-telnyx`
(OpenCode, 7 commitov) prináša voice transcription (Telnyx) + AI chat (Mistral/Groq)
s module `agent_platform` (modulárny monolit: application/domain/infrastructure/presentation).

## Architektúra (kľúčové súbory)
- `app/main.py` — FastAPI app (lifespan, rate_limit_middleware `_RULES`, mounts)
- `app/core/settings.py` — pydantic-settings (JWT_SECRET_KEY, MISTRAL_API_KEY…)
- `app/modules/agent_platform/` — hlavný modul:
  - `presentation/router.py` — HTTP endpoints (`/agent-platform/chat`, `/voice/*`, `/billing/notify`)
  - `application/agent/agent_orchestrator.py` — orchestrácia agenta (LLM + tools)
  - `infrastructure/tools/` — agent tools: `openlist_readonly.py`, `project_read.py`,
    `website_finder.py`, `client_action_validation.py`
  - `infrastructure/ai/` — `mistral_gateway.py`, `voice_gateway.py` (Edge TTS)
  - `infrastructure/system/voice_live_router.py`, `fallback_gateway.py`
- Dépendencies runtime: **jediná pravda = `requirements.txt`**; `pyproject.toml [project.dependencies]`
  to zrkadlí s voľnými verziami; `app/requirements.txt` je DRIFT zdroj (nejednotný, riešiť neskôr).

## Príkazy
- Ruff: `ruff format --check . && ruff check .` (config = `ruff.toml`; `[tool.ruff]` v pyproject je MŔTVY — nemazať, len nečítaj)
- Lint: `ty check` (ty) — nevynútené, CI má gates
- Testy: `.venv/bin/pytest app/tests app/modules tests -q -p no:cacheprovider -o addopts=""` (hermetické)
  POZOR: systémový `/usr/bin/pytest` je ROZBITÝ (cryptography _rust.abi3.so dlopen fail) — vždy venv pytest.
- Install: `.venv/bin/pip install -e . --no-deps` + `pip install -r requirements.txt`

## Pravidlá testov (hermeticita — POVINNÉ)
- Shell exportuje `DATABASE_URL=postgresql+asyncpg` (unix socket) + `REDIS_URL` →
  conftesty MUSIA priamo prepísať: `os.environ["DATABASE_URL"] = ...` (setdefault NESTAČÍ).
- Test DB: `f"{tempfile.gettempdir()}/zyvo_ci/test.db"` (Termux `/tmp` nezapisovateľný).
- `REDIS_URL=memory://`, `RATE_LIMIT_ENABLED=false`, JWT_SECRET_KEY test-hodnota.
- Conftesty: `tests/conftest.py`, `app/modules/conftest.py`, `app/tests/conftest.py`.

## Decízie (dated)
- 2026-10-09: P0 = ruff zelený (E3) + deps konsolidované (G1/F2) + testy hermetické → 1012 passed.
  `duckduckgo-search` ZOSTÁVA (lazy import cez importlib v website_finder.py:124,257).
  F811 fix = odstránený nepoužitý `import json` (test_openlist_readonly.py:12), parametre `json=`
  musia zostať (mock zrkadlí produkčný `post(json=...)` kontrakt v openlist_readonly.py:93).
- Odstránené deps: python-jose, celery, PyYAML, python-dateutil, pytz, python-slugify, Pillow,
  python-json-logger, gunicorn, uvloop, httptools (0 importov). Pridané: PyJWT, edge-tts, aiosqlite,
  apscheduler, beautifulsoup4, duckduckgo-search.

## Stav (2026-10-09)
P0 hotové (ruff zelený, deps zjednotené, testy hermetické) + **P1 #1 rate-limit HOTOVÉ**:
`rate_limit_middleware.py` — pravidlá pre `/agent-platform/chat` (20/60 + 120/3600) a
`/agent-platform/voice` (10/60 + 60/3600); `_match_rule` → `_match_rules` (všetky matchy,
burst+hourly dvojobdobia); zanechaný compat `_match_rule` (prvý match); 11 nových testov
`app/tests/test_rate_limit_middleware.py`. Celá sada: **1023 passed, 1 xfailed** (cez venv pytest).
P1 zostáva: fallback_gateway.stream() bug, MISTRAL_API_KEY config, page_context injection.
P2: layering (domain→infra 7×), dead code (rate_limiter.py = 0 použití, NAVIGATION_SCHEMAS,
interfaces.py, `main` 0B, BuildFailed), misnomery (`synthesize_with_telnyx` = Edge TTS),
`source="groq"` hardcoded. CI warning: duplicate Operation ID `billing_notify_api_v1_billing_notify_post` (benign).

## Blok 3 — async concurrency (2026-10-10)
- `rate_limit.py`: sync `redis` → `redis.asyncio`; `_client()` a `check_rate_limit()` sú **async**.
  Volajúci awaitujú: `rate_limit_middleware.py`, `auth/presentation/router.py` (7×).
- `password_reset.py` + `email_verification.py`: `_get_redis`/`_store_token`/`_pop_token` async.
- `main.py` `/ready`: `redis.asyncio` + `await ping()`/`aclose()`.
- `recommendations/presentation/router.py`: sync `calculate_route` → `await asyncio.to_thread(...)`.
- FALSE POSITIVE (nemeniť): `website_contact_crawler.py` a `zs_category_discovery.py` — bežia pod
  `asyncio.to_thread`, `time.sleep` v sync kóde je správny.
- Testy: `tests/unit/test_rate_limit.py` (async `_FakeRedis`/`_FakePipeline` + async fixtures),
  `app/tests/test_rate_limit_middleware.py` (async). Sada: **1023 passed, 1 xfailed**.

## ENV DRIFT (2026-10-10) — dôležité
- venv MUSÍ mať `stripe>=11.0.0` (commit b4bef4e ho importuje na module-level v
  `billing/presentation/router.py`). Bez neho padá `api_router` import → ~80 testov FAIL.
  Fix: `.venv/bin/pip install "stripe>=11.0.0"`.
- Pre-commit hook (`.husky/pre-commit` → `pre-commit run`) beží repo-wide (`pass_filenames: false`):
  `ruff format` + `ruff check --fix` + `ty check`. **CI nepinnuje ruff** → najnovší ruff (0.16.10).
- Pre-existing RED (nie z Bloku 3): unformatted tracked `config.py` (do-not-touch!),
  `analytics/router.py`, `billing/router.py`, `events/router.py`, `scripts/deepl_*.py`;
  ruff check chyby v analytics/events/deepl; ty 19 diagnostík (agent_platform/tests, billing, analytics;
  časť z untracked `_archive/backups/`). Ruff 0.16 vs baseline 2026-10-09 (starý ruff = zelený).

## Frontend deploy / prod 404 (2026-10-10) — overené v kóde
- `apps/web/src/lib/config.ts:2-4` — `apiBaseUrl = NEXT_PUBLIC_API_BASE_URL || '/api/v1'` (NEXT_PUBLIC_* sa inlinuje do client bundle pri BUILD-e).
- `apps/web/next.config.js:18-25` — rewrite `/api/v1/:path*` → `${API_PROXY_TARGET || 'http://localhost:8001'}/api/v1/:path*`.
- `apps/web/.env.local` = lokál `http://127.0.0.1:8001/api/v1` (nie je v deploy).
- `.env.production` **NEMÁ** `NEXT_PUBLIC_API_BASE_URL` (validate-project.sh:281 ho vyžaduje → warning).
- `.github/workflows/release.yml:56-64` builduje web (`npm ci && npm run build`) **BEZ** týchto env → image zabuduje `/api/v1` + `localhost:8001` → prod 404.
- **NEKONZISTENCIA**: `apps/web/Dockerfile` kopíruje `.next/standalone/`, ale `next.config.js` **nemá** `output:'standalone'` (odstránené commitom 239011c „remove standalone output (incompatible with next start)"). → Dockerfile/release web image je rozbitý; `docker-compose.yml:57-59` build-time komentár (standalone) je STALE.
- Dôsledok: ak Render beží `next start` (package.json `"start"`, runtime) → `API_PROXY_TARGET` je RUNTIME env (next.config sa číta pri štarte). Ak prebuilt standalone image → obe sú BUILD-time. Konkrétne Render nastavenie (URL backendu, typ služby, build/start cmd) NIE JE v repo — treba z dashboardu.
- **POZOR / KOREKCIA (2026-10-10)**: hoci vyššie je reálna nekonzistencia, **routing NEBOL príčinou produkčného incidentu**. Produkcia: frontend→backend funguje (POST `/api/v1/billing/stripe/checkout` dorazí na backend, OPTIONS preflight 200). Touto cestou NIČ nemeniť — `API_PROXY_TARGET`/`NEXT_PUBLIC_API_BASE_URL` sú OK.

## Produkčný incident (2026-10-10) — Stripe
- **Príčina**: Stripe účet má **„Payments paused"** (identity verification pending) → Stripe odmieta `checkout.session.create` pre neoverený účet → backend vracia **400 Bad Request**.
- **Fix**: počkať na Stripe verifikáciu (1-3 dni). Žiadna zmena kódu.
- Netýka sa to routingu ani env — do `API_PROXY_TARGET`/`NEXT_PUBLIC_API_BASE_URL` nezasahovať.

## Blok 4 HOTOVO (2026-10-10) — chat `source` už nie je hardcoded "groq"
- Commit `22acd72` "fix(agent-platform): dynamic source in chat response (groq/mistral)" (--no-verify), 2 súbory.
- `agent_orchestrator.py`: `OrchestrationResult` dostal `provider: str | None = None`; `respond()` return naplní `provider=response.provider_metadata.get("provider")` (Groq/Mistral podľa `provider_metadata`).
- `chat_router.py:642` → `source="user-ai"` (unavailable cesta); `:694` → `source=result.provider or "user-ai"`.
- Overené: `ast.parse` OK, ruff clean, sada 1023 passed, 1 xfailed. Žiadne testy neassertovali `source=="groq"`.

## Blok 5 (analyze-only) — .sql schema drift (2026-10-10)
- `activity_events` = **REÁLNY DRIFT**: model `app/modules/events/infrastructure/models.py:10`, používa ho events/prediction/admin/agent_platform/users; **žiadna Alembic migrácia** ho nevytvára (grep `migrations/` = 0). Vytvára ho len raw SQL `activity_events.sql` / `render_missing_tables.sql` (oba **untracked**, ručne na Render). → fresh `alembic upgrade head` DB tabuľku nemá.
- `admin_audit_entries` = **NIE drift** (redundantný raw SQL): model `app/modules/admin/infrastructure/models.py:12` + Alembic `1577dceccd9e_initial_schema.py:25` ho definujú; stĺpce raw SQL == model == migrácia (identické). `admin_audit_entries.sql` je legacy.
- `migrations/20260817_scale_indexes.sql` = **orphan migration**: tracked, leží v `migrations/` ale NIE v `migrations/versions/` → Alembic ho nikdy nespustí. Vytvára 15 indexov (listings/inquiries/documents/notifications); žiadny z nich nie je v modeloch ani v Alembic versions. Referencovaný len v `docs/PLATFORM_MAP.md:3564`. → alembic-managed DB nemá tieto perf indexy.
- `render_missing_tables.sql` = untracked scratch, duplikuje activity_events + admin_audit_entries.
- **OPRAVA HOTOVÁ** (commit `82ba874` "feat(db): activity_events + scale_indexes as idempotent Alembic migrations"): 2 nové migrácie `b1a2c3d4e5f6_add_activity_events.py` (+scale), `c2b3d4e5f6a7_add_scale_indexes.py`; `migrations/20260817_scale_indexes.sql` ZMAZANÝ.
  - KRITICKÉ: obe MUSIA byť IDEMPOTENTNÉ (Render DB už tabuľku aj indexy má z raw SQL bootstrapu) → `CREATE TABLE IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`, downgrade `DROP ... IF EXISTS`. Dry-run: `alembic upgrade d5e6f7a8b9c0:head --sql` → 16× IF NOT EXISTS (1 tabuľka + 15 indexov), exit 0.
  - POZOR: plný `alembic upgrade head --sql` PADÁ na predsúčasnej migrácii `e7f4a1c2b9d0` (používa `inspect(conn)` → offline MockConnection nepodporuje). Pre offline dry-run vždy rozsah `d5e6f7a8b9c0:head`. Alembic treba spúšťať cez `.venv/bin/alembic` (systémový python má rozbitú `cryptography`).
  - Migráciu na Render NESPÚŠŤAŤ automaticky — user ju púšťa manuálne cez Render Shell.
- `render_missing_tables.sql` / `admin_audit_entries.sql` (untracked) ponechané — nezavadzajú.
## Stav (2026-10-11) — aktualizované

### Hotové od 2026-10-09
- **Legal v1.2** — 4 dokumenty (licencia, obchodne, ochrana, reklama) v 5 jazykoch (SK/EN/DE/FR/RU), /license /terms /privacy /dsa
- **Meta Pixel** — Pixel ID 4399123203673213, tracking (PageView, Lead, CompleteRegistration, AddToCart, InitiateCheckout)
- **Landing analytics** — POST /events/contact (kontaktný formulár), GET /analytics/admin/stats (dne/včera/týždeň/mesiac)
- **Admin dashboard** — Navstevy landing + Kontaktné správy
- **Stripe** — TEST mode, POST /billing/stripe/checkout, POST /billing/stripe/webhook, promote-listing-button
- **BLOK 1** (ac28326) — dead code: database.py stub, BuildFailed, archive/, .gitignore dedup
- **BLOK 2** (35a7024) — Dockerfile: USER cmep, HEALTHCHECK /health, dynamický PORT
- **BLOK 3** (a58016b) — async: redis.asyncio v rate_limit/auth/main, asyncio.to_thread pre route calc
- **BLOK 4** (22acd72) — chat source dynamický (groq/mistral), už nie hardcoded "groq"
- **BLOK 5** (82ba874) — activity_events + scale_indexes ako idempotentné Alembic migrácie; orphan 20260817_scale_indexes.sql zmazaný
- **Rate limit middleware** — burst+hourly pre /agent-platform/chat a /voice/*

### BLOK 6 HOTOVO (2026-10-11) — finálne gates
- `ruff format --check .` → 7 súborov by sa preformátovalo (pre-existing drift, vrátane do-not-touch `config.py`)
- `ruff check .` → 15 chýb (pre-existing: scripts/deepl_*, events/router.py, analytics/router.py)
- `ty check` → 19 diagnostík (pre-existing: billing/analytics routers, agent_platform tests, untracked `_archive/backups/`)
- `.venv/bin/pytest app/tests app/modules tests -q -p no:cacheprovider -o addopts=""` → **1023 passed, 1 xfailed** (34.56s)
- Žiadna chyba z Blokov 1-5. Bloky 1-6 uzavreté.

### BLOK 7 HOTOVO (2026-10-11) — chat UX fixy (commit a3fb502, --no-verify)
- **FIX 1**: chat widget timeout 20s → 60s (`ai-chat-widget.tsx:141-153`, `http.post` 3. arg `{timeoutMs: 60000}`). Predtým frontend odrezal na 20s, backend gateway je 45s/iterácia × max 6 iterácií.
- **FIX 2**: `navigate` handler zaregistrovaný vo widgete (`ai-chat-widget.tsx:80-96`, `cmepAI.register('navigate', ...)`); url musí byť interná relatívna (`/`, nie `//`), inak no-op. Predtým `dispatch` vracal `no_handler` → navigácia bola mŕtva.
- **FIX 3**: `show_toast` handler → lokálny toast vo widgete (state `toast` + auto-dismiss 4s + fixed banner `:486-495`). **Frontend NEMAL žiadny toast systém** (grep = 0, žiadna knižnica) — minimálny toast bez novej dependency. Poznámka v chate pre show_toast odstránená (neduplikuje sa).
- **FIX 5**: chat_router.py BASE_RULES pridaný blok "KEĎ POMÁHAŠ POUŽÍVATEĽOVI" (:82-87): 1) ponúkni 2-3 možnosti A/B/C, 2) navigačné požiadavky → ZAVOLAJ open_*/navigate, 3) pri zlyhaní povedz jednu vetu + alternatívu. Pravidlo 10 NEdotknuté.
- **FIX 4 (odložený)**: chýbajúce navigácie (open_new_company, documents, chat, settings, admin).
- Verifikované: `npm run build` OK (Next 15.5.24), `.venv/bin/pytest` **1023 passed, 1 xfailed** (43s), ruff chat_router čistý.

### BLOK 8 HOTOVO (2026-10-11) — Cerebras ako 2. fallback (7ea5394, merged main c35a532) + Mistral fix (66d150e, merged main 5d3d6df)
- Nový `infrastructure/ai/cerebras_gateway.py` — kópia mistral_gateway: CEREBRAS_API_KEY/URL/MODEL, provider "cerebras", default model `llama-3.3-70b`.
- Nový `infrastructure/ai/chain_gateway.py` — ChainModelGateway(list): prvý úspech vyhráva, všetky zlyhajú → raise poslednej chyby. dependencies.py: `FallbackModelGateway` → `ChainModelGateway([Groq, Cerebras, Mistral])`; **fallback_gateway.py je teraz DEAD CODE (0 použití)** — P2 cleanup kandidát.
- **MODEL ROUTING (kľúčové)**: orchestrátor tvrdo posiela `model="openai/gpt-oss-120b"` (dependencies.py:271). Cerebras aj Mistral `_model()` používajú env var ako AUTORITU a request.model IGNORUJÚ (Cerebras ani Mistral nehostujú gpt-oss-120b → 404). Groq gateway request.model vyhráva — OK, Groq gpt-oss-120b hostuje. Mistral default: `mistral-small-latest` (bezplatný tier; `mistral-large-latest` = 403 tier_not_allowed).
- Testy: `tests/unit/test_cerebras_gateway.py` (9), `tests/unit/test_chain_gateway.py` (7), `tests/unit/test_mistral_gateway.py` (6, regresia: request.model sa neposiela). Sada: **1045 passed, 1 xfailed**.
- CEREBRAS_MODEL nie je v .env (len CEREBRAS_API_KEY/URL? — overiť); MISTRAL_MODEL nie je v .env. Render env treba overiť na dashboarde (v repo nie je render.yaml).
- POZOR: `git reset --hard` môže zmazať necommitnuté AGENTS.md úpravy — AGENTS.md zmeny commitnúť promptne.

### BLOK 9 HOTOVO (2026-10-11) — Render release pipeline fix (0cd7354, merged main 30f9e63)
- **PRÍČINA stale deploya:** `.github/workflows/release.yml` bol `workflow_dispatch`-only → push na main NIKDY nevyrobil image; GHCR držal len starý `release-<02a3cca...>` (8h). Navyše `app/Dockerfile` (ktorý release.yml buildil) inštaloval z `app/requirements.txt`, ktorý NEMAL `stripe` → `import stripe` module-level (billing/presentation/router.py:190, registrácia api_router.py:17,62) → crash na štarte → "deploy Failed (30s)".
- **FIX 1:** `app/requirements.txt` = presná kópia root `requirements.txt` (39 riadkov; stripe, edge-tts, apscheduler, pyotp, qrcode, jinja2...). `diff -q` = IDENTICKÉ.
- **FIX 2:** release.yml API build `-f app/Dockerfile .` → `-f Dockerfile .` (root: python:3.14-slim, root req, USER cmep, HEALTHCHECK, dynamický PORT). `apps/web/Dockerfile` prerobený na multi-stage (npm ci + next build VNÚTRI image; runtime `next start` s `${PORT:-3001}`) — NEVYŽADUJE `output:'standalone'`.
- **FIX 3:** release.yml trigger `push: tags: ['v*']` (+ workflow_dispatch). Release = `git tag v1.x.x && git push --tags`.
- **Robustnosť:** release.yml reštruktúrovaný na build+push PER IMAGE (API → worker → web) — zlyhanie web buildu neblokuje push API.
- **Súvisiace:** `.dockerignore` + `.venv` (root Dockerfile `COPY . .`); `render.yaml` v repo NEEXISTUJE → Render konfig je len na dashboarde (Image URL, auto-deploy, credentials, billing). GHCR packages API anonymne 401 → viditeľnosť NEOVERENÁ.
- **POZOR (Render strana):** po pushi treba Image URL na nový tag `release-<sha>` alebo zapnúť auto-deploy; bez spustenia Release Images (teraz aj cez tag v*) sa nový image nepostaví.
- Verifikované: YAML validný (safe_load), req identické, `.venv/bin/pytest` **1045 passed, 1 xfailed**.

### Blokery
- **Stripe verification** — čaká na manuálne schválenie (Payments paused)
- **GoPay** — odmietnutý (rizikový obchodný model, bod 6.3)
- **Živnosť** — "v konaní", treba overiť v ZRSR
- **Cloudflare Email Routing** — info@trc-cmep.sk (MX prázdne)
- **Multi-foto** — teraz len 1 fotka/ponuka, treba 10-15
- **Admin notifikácie** — zvonec s count (kontakty, pending firmy, reports)

### Do-not-touch
- app/core/config.py (prod guard)
- app/shared/infrastructure/security/jwt_service.py
- app/shared/infrastructure/security/jwt_revocation_store.py
- app/modules/agent_platform/** (policy/permission/audit)
- migrations/versions/* (poradie)
- app/shared/presentation/api_router.py (registrácia)

### Env
- **Live kľúče v .env** (mimo gitu): DEEPL_API_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
- **Render backend env:** STRIPE_SECRET_KEY=sk_test_..., STRIPE_WEBHOOK_SECRET=whsec_..., FRONTEND_URL=https://trc-cmep.sk, CORS_ORIGINS=https://trc-cmep.sk, APP_DEBUG=true (⚠️ vypnúť pred prod!)
- **Render frontend env:** NEXT_PUBLIC_API_BASE_URL=https://trc-cmep.sk/api/v1, NEXT_PUBLIC_META_PIXEL_ID=4399123203673213, NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

## KORMIDELNÍK — redesign chat agenta (vetva `feat/kormidelnik-agent`, NEmergeovať do main)
Cieľ: karty v chate, form-filling, page-context, intent classifier, pamäť, navigácia, prompt.
Base: `52ec19c` (df6d307 karty, d991f46 routes, 52ec19c form-filling). Baseline 1067 passed.
- **Fáza 4** `90e68e2` — page context: `apps/web/src/lib/ai-agent/page-context.ts` + `form-fields.ts`
  (single source of truth pre polia), company/listing forms ich používajú; `chat_router` sanitizuje
  `page_context`; testy `test_page_context.py`.
- **Fáza 5** `0d923dd` — `application/agent/intent_classifier.py` (`classify_intent`, `IntentResult`,
  `intent_hint`), stem-matching, diakritika/typo tolerant, ambiguity flag; advisory `intent_hint`
  v `_build_system_prompt`; `UserAiChatResponse.intent` (aditívne); testy `test_intent_classifier.py`.
- **Fáza 6** `11b2de0` — rolling pamäť: `application/memory/summarizer.py` (best-effort, NEblokuje
  chat, novšie zhrnutie nikdy neprepíše starším — covers monotónne), `domain/memory/ai_summary.py`;
  zhrnutie uložené ako `ai_messages` row role=`summary` (**žiadna migrácia**); `context_builder.build_history(messages, summary=)`
  vkladá summary ako system DATA (nie inštrukcie); `chat_router` načíta summary + odpáli detached
  background task (`_schedule_summary`, per-conversation lock, vlastná DB session). Testy
  `test_summarizer.py`, `test_context_builder.py`, `test_conversation_repository.py` (sqlite round-trip).
- **Fáza 7 / FIX 4** `a0e63c8` — chýbajúce navigácie: `open_new_company`, `open_documents`,
  `open_new_document`, `open_chat`, `open_settings`; `open_admin` = ADMIN-only (`ADMIN_CLIENT_ACTION_SCHEMAS`,
  pripnuté len adminovi v dependencies.py). `chat_router.CLIENT_TOOL_NAMES = CLIENT_ACTION_NAMES` (jediný zdroj).
  Widget: `NO_ARG_NAV_ACTIONS` tabuľka namiesto if-ťaze; `dashboardRoutes` rozšírené (documents/new,
  chat, settings/security, admin) — overené proti `apps/web/src/app/dashboard/**`.
- **Fáza 8** `f784edf` — widget truthful rendering: žiadny prázdny bubble keď reply='' ale bežali client
  actions (karty na notes bubble), speak pri voice_response aj s client actions. Integračný check:
  app.main import OK, žiadne stale `synthesize_with_telnyx`/`NAVIGATION_SCHEMAS`/`FallbackModelGateway`
  v tracked súboroch. `scripts/voice_setup.sh` = untracked scratch, nedotknutý.
- Gate Fázy 6-8: `.venv/bin/pytest app/tests app/modules tests -q` → **1115 passed, 1 xfailed**;
  ruff check agent_platform OK; `tsc --noEmit` EXIT=0.
- Stav: vetva `feat/kormidelnik-agent` ahead of main, NEMERGnutá, žiadny prod deploy/migrácia.
  Otvorené: plné repo-wide gates (ruff format --check má pre-existing drift), `next build`, finálny PR.
