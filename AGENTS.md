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

## Blok 4 (report-only) — chat `source="groq"` misnomer
- `app/modules/agent_platform/presentation/chat_router.py:642` a `:694` hardcodujú `source="groq"`, hoci odpoveď môže prísť z Mistral (fallback) — pozri `presentation/dependencies.py:259-273` (`FallbackModelGateway(primary=Groq, fallback=Mistral)`).
- `ModelResponse.provider_metadata` nesie `{"provider": "groq"|"mistral", "model": ...}` (`groq_gateway.py:124`, `mistral_gateway.py:131`), ale `OrchestrationResult` (`agent_orchestrator.py:50-54`) ho ZAHADZUJE.
- Patch (nemenené, len návrh): pridať `provider` do `OrchestrationResult` + v `respond()` ho naplniť z `response.provider_metadata.get("provider")`; v `chat_router` nahradiť `source="groq"` za `result.provider or "user-ai"` (resp. `"user-ai"` na unavailable ceste). Žiadne testy neassertujú `source=="groq"`.
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
- **Rate limit middleware** — burst+hourly pre /agent-platform/chat a /voice/*

### Čaká (BLOK 4-6)
- **BLOK 4** — chat source fix (source="groq" hardcoded pri Mistral fallback) — do-not-touch (report only)
- **BLOK 5** — .sql schema drift (activity_events.sql, admin_audit_entries.sql, render_missing_tables.sql mimo Alembic)
- **BLOK 6** — finálne testy (ruff, ty, pytest)

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
