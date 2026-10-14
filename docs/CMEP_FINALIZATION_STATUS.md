# CMEP Finalization Status — pracovný dokument Kormidelníka

Aktualizované: 2026-10-11 (2. audit, lokalne opravy) · Vetva: `feat/kormidelnik-agent` @ `1e61f77` (HEAD; zmeny NESTAGED, bez commitu)
Pravidlá: všetky zmeny lokálne, žiadny commit/push/deploy bez výslovného schválenia.
Stavové kódy: HOTOVÉ A OVERENÉ / IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ / ROZPRACOVANÉ / NEIMPLEMENTOVANÉ / BLOKOVANÉ / VYŽADUJE PRODUKČNÉ OVERENIE

---

## A. Verejná časť

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| Vstupná stránka | HOTOVÉ A OVERENÉ | `apps/web/src/app/page.tsx` | Meta Pixel + `/events/contact`, UTM tracking | smoke cez sadu | N/A |
| Navigácia | HOTOVÉ A OVERENÉ | header/footer, LanguageSwitcher 5 jazykov | — | — | N/A |
| Registrácia/prihlásenie | HOTOVÉ A OVERENÉ | login/register + Turnstile + 2FA + verify-email | Google login backend je, tlačidlo chýba | test_auth_endpoints, test_two_factor_service | L |
| Responzívnosť/prístupnosť | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | Tailwind; **app/loading, app/error, app/not-found, app/global-error PRIDANÉ (2. audit)** | FE testy stále chýbajú (vitest = blocked) | tsc 0 + build OK | M |
| Reálne dáta dôveryhodne | HOTOVÉ A OVERENÉ | dáta z DB cez API | — | — | N/A |
| Analytika návštev | HOTOVÉ A OVERENÉ | `/analytics/acquisition/events`, `/analytics/admin/stats` | test_acquisition (2 testy, slabé) | test_acquisition | M |

## B. Používateľská platforma

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| Dashboard | HOTOVÉ A OVERENÉ | `dashboard/layout.tsx` (useAuthRequired) + app-shell | client-side flash (useEffect redirect) — server ostáva autorita | tsc/build | L |
| Ponuky materiálov | HOTOVÉ A OVERENÉ | listings CRUD + publish + marketplace + matches | multi-foto (len 1 fotka) — BLOKOVANÉ rozsahom | test_listing_service, test_listings_* | M |
| Vyhľadávanie/filtrovanie | HOTOVÉ A OVERENÉ | listing-filters.tsx, marketplace | — | — | M |
| Firemné profily | HOTOVÉ A OVERENÉ | companies CRUD + RPO check + tier | RPO lookup nie je zavolaný vo formulári | test_company_* | M |
| Dopyty | HOTOVÉ A OVERENÉ | inquiries CRUD, received/sent | žiadny dedikovaný inquiry formulár (len button) | test_inquiry_service | M |
| Komunikácia/chat | HOTOVÉ A OVERENÉ | chat threads, unread badge | chat-window/thread-list komponenty UNUSED | test_chat_* (4 súbory) | M |
| **Notifikácie** | **HOTOVÉ A OVERENÉ (2. audit)** | backend 7 endpointov + **bell zavesený v dashboard-header** + markRead + unread polling 10 s | UUID bug OPRAVENÝ (`_uuid()` v repositories.py), xfail zrušený + 4 testy | 50 passed (notifications) | N/A |
| Používateľské účty/nastavenia | HOTOVÉ A OVERENÉ | settings/security (2FA), users PATCH | — | test_users_endpoints | N/A |
| Administrácia | HOTOVÉ A OVERENÉ (2. audit) | `/dashboard/admin` + **guards: recommendations + users/[id] + layout**, **link na recommendations pridaný do admin page** | lead_finder/telegram lokálny `_require_admin` namiesto shared (kozmetika, 403 vs ForbiddenDomainError) | test_admin_smoke + guards | L |
| Analytika (admin) | HOTOVÉ A OVERENÉ | `/admin/stats`, `/analytics/admin/stats`, events reports | analytics router/testy slabé (len 2 unit) | test_business_metrics, test_acquisition | M |

## C. AI Kormidelník

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| N1 — tool_calls len vykonané | HOTOVÉ A OVERENÉ | commit `1e61f77`, append za policy/permission/handler | overené auditom + 6 testov | test_orchestrator_collected_calls (6) | N/A |
| N2 — UUID SQLite/Postgres | HOTOVÉ A OVERENÉ | `_uuid_or_none` v ai_conversation_repository | overené SQLite 8 + PG probe 5/5 | test_conversation_repository (+5) | N/A |
| N3 — transakcie/výkon | ROZPRACOVANÉ | docs/KORMIDELNIK.md 11c (návrh) | **rozhodnutie: NEIMPLEMENTOVAŤ bez samostatného posúdenia**; 3 commity/turn | baseline | N/A |
| Policy → permission → handler | HOTOVÉ A OVERENÉ | allowlist_policy_engine, actor_tool_permission_engine | deny-by-default | test_agent_policy_gate, test_agent_permission_gate | N/A |
| Neznáme tooly / zlé argumenty | HOTOVÉ A OVERENÉ | forbidden_tool_names, client_action_validation, registry guard | — | test_client_actions, test_agent_contracts | N/A |
| Server-side oprávnenia | HOTOVÉ A OVERENÉ | governance routers admin-gated (require_admin) | — | test_admin_tools | N/A |
| Audit stavov (úspech/denied/error/approval) | HOTOVÉ A OVERENÉ | `_audit` v finally + OUTCOME + sqlalchemy_event_publisher | event publisher `:58` má bare pass | test_agent_audit | N/A |
| Navigácia vnútri platformy | HOTOVÉ A OVERENÉ | client_action_validation (internal-only navigate), dashboard-routes, NO_ARG_NAV_ACTIONS | frontend `navigate` handler nevaliduje proti whitelistu (low, defense-in-depth) | test_client_actions | L |
| Pravdivé hlásenie neimplementovaných akcií | HOTOVÉ A OVERENÉ | BASE_RULES „KEĎ POMÁHAŠ", denied → unavailable cesta | — | test_chat_gate | N/A |
| Pamäť konverzácií | HOTOVÉ A OVERENÉ | ai_messages, rolling summary (role=summary) | detached task, per-conversation lock | test_conversation_repository, test_summarizer, test_context_builder | N/A |
| Izolácia user/company | HOTOVÉ A OVERENÉ | session_id scoping, `_first_company_id` | — | test_conversation_repository | N/A |

## D. Rozšírené funkcie a hlas

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| AI vyhľadávanie | HOTOVÉ A OVERENÉ | ai-draft, cmep_*_handler (listing/company search) | — | test_cmep_company_search_handler | M |
| **AI draft stream gate** | **OPRAVENÉ (2. audit)** | `listings/router.py` ai_draft_stream: **AI tier gate pridaný** (409, rovnaký ako /ai-draft; frontend už 409 spracúval ako ai_tier_required) | predtým stream fungoval pre každého prihláseného (cost abuse) | test_ai_draft_stream_route (7) | N/A |
| Predikcie | HOTOVÉ A OVERENÉ | prediction modul (18 testov) | provider registry + baseline | tests/modules/prediction (18) | M |
| Automatické trasy | HOTOVÉ A OVERENÉ | recommendations/route, distance logistics | — | test_distance_logistics | M |
| Výpočty cien | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | recommendation pricing slots | chýba priame testovanie | sada | L |
| Pomoc pri vytváraní ponúk | HOTOVÉ A OVERENÉ | AiDraftPanel + useAiFormFilling (listing+company) | — | test_page_context, test_form_filling | M |
| APK „Krok" | NEIMPLEMENTOVANÉ | — | nie je v repo (žiadny Android build) | — | L |
| **Hlasový agent** | **IMPLEMENTOVANÉ, čiastočne OVERENÉ (2. audit)** | transcribe (Groq Whisper) + edge-tts + voice_live token (Deepgram) | **13 hermetických testov PRIDANÝCH** (auth, entitlement, 415/400/413, mocked provider 200/502, token 503/502/200); live API kľúče na Render neoverené | test_voice_endpoints (13) | M |
| Voice oprávnenia/súhlas/audio | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | bearer na /voice/transcribe; audio ide cez providera | GDPR/zretazenie audio tokov — produkčné overenie | — | M |

## E. Dizajn a UX

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| Konzistencia rozhrania | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | ui/ komponenty, cmep-dark.css | — | — | L |
| Loading/prázdne/chybové/úspešné stavy | **ROZPRACOVANÉ → PRIDANÉ (2. audit)** | **app/loading.tsx + app/error.tsx + app/not-found.tsx + app/global-error.tsx (branded)** | alert() v uploadoch; dashboard-level loading/error/not-found stále chýbajú | — | M |
| Formuláre a feedback | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | react-hook-form + zod; 4 formuláre pokryté | — | — | L |

## F. Dokumentácia a právna

| Požiadavka | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| Licencia/obchodné/ochrana/DSA | HOTOVÉ A OVERENÉ | /license /terms /privacy /dsa + 5 jazykov (i18n) | dokumenty HTML untracked v dokumenty/ | — | N/A |
| Technická dokumentácia | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | docs/ (PLATFORM_MAP, KORMIDELNIK, SECURITY_AUDIT…) | — | — | N/A |
| Zmeny dokumentov oddelené od kódu | HOTOVÉ A OVERENÉ | AGENTS.md/KORMIDELNIK.md ostávajú nedotknuté | — | — | N/A |

## G. Testy a bezpečnosť

| Oblasť | Stav | Dôkaz | Chýba / riziko | Testy | Priorita |
|---|---|---|---|---|---|
| Jednotkové/integračné | HOTOVÉ A OVERENÉ (2. audit) | **plná sada 1185 passed, 0 xfailed** (1165 + 7 stream + 13 voice) | 1 warning: duplicate Operation ID billing_notify (benign, zdokumentované) | plná sada | N/A |
| **compliance testy** | **HOTOVÉ (15)** | tenant izolácia CRUD + admin bypass | — | tests/unit/test_compliance_module.py | N/A |
| **documents testy** | **HOTOVÉ (12)** | tenant izolácia CRUD + status zmena admin-only | — | tests/unit/test_documents_module.py | N/A |
| billing checkout/webhook | **HOTOVÉ (8 Stripe)** | checkout 503/422/metadata, webhook podpis/promote/ignore | GoPay BLOKOVANÉ (obchodné); /billing/notify bez podpisu (inert kým GoPay disabled) | tests/unit/test_billing_stripe.py | M |
| Auth/authorization | HOTOVÉ A OVERENÉ | JWT + revocation + 2FA; require_admin/require_platform_admin | lead_finder + telegram lokálny `_require_admin` (kozmetika) | test_jwt_*, test_authorization, test_auth_* | L |
| Izolácia dát | HOTOVÉ A OVERENÉ | tenant checks v routeroch (company member/admin), _ensure_notification_owner | DB-level RLS nie je; `POST /listings/ai-draft` + `POST /events` trustujú body companyId (low) | test_documents/compliance (izolácia) | L |
| Validácia vstupov | HOTOVÉ A OVERENÉ | Pydantic, 422 handler bez input leak | — | api/test_exception_handlers | N/A |
| Frontend procesy | ROZPRACOVANÉ | finest **0 FE testov; vitest script ukazuje na nenainštalovanú dep** | tsc/build fungujú (0 chýb) | npm run build | M |
| Build/statická kontrola | HOTOVÉ A OVERENÉ (2. audit) | ruff čistý na zmenených, tsc 0, next build OK | CI na GitHub Actions MŔTVY (startup_failure) — BLOKOVANÉ externé | lokálne gate | N/A |
| Konkurencia/paralelizmus | IMPLEMENTOVANÉ, NEÚPLNE OVERENÉ | detached summary task, per-conv lock; N3 merané | N3 návrh v KORMIDELNIK.md 11c | — | L |

## Konkrétne otvorené nedostatky (zoraď. podľa priority)

1. **[M] FE testy (vitest)** — 0 FE testov; vitest nenainštalovaný → nová dependency = vyžaduje schválenie (blocked).
2. **[M] Analytics router testy** — len 2 unit testy dnes.
3. **[L] lead_finder + telegram `_require_admin`** — lokálna kópia namiesto shared `require_admin` (semanticky rovnaké; len typ výnimky 403 vs ForbiddenDomainError). Kozmetika, bez zmeny.
4. **[L] `POST /listings/ai-draft` + `POST /events`** — trustujú body `companyId` bez membership check (write-time, žiadny read leak).
5. **[L] `navigate` client action** — nevaliduje cieľ proti whitelistu dashboardRoutes (backend už internal-only kontroluje).
6. **[L] Google login tlačidlo** — backend je, UI nie (mimo rozsahu?).
7. **[L] alert() v uploadoch** — nahradiť inline error state.

## Blokácie (externé / vyžadujú usera)

- **GoPay** — odmietnutý provider (obchodné rozhodnutie 2026-10-10). Kód fail-closed: GOPAY_* nie sú v Settings (extra="ignore") → `_ready()` vždy False → checkout/notify 503. `POST /billing/notify` je bez podpisu, ale INERT (kým GoPay disabled, nevolá sa smerom von). Celý GoPay modul = kandidát na zmazanie po rozhodnutí usera.
- **Stripe verzifikácia** — „Payments paused" (externé).
- **GitHub Actions startup_failure** (od 23.9.) — infra GitHubu; release images sa nepostavia cez Actions.
- **N3 (transakcie/výkon agenta)** — rozhodnutie usera (3 commity/turn, 2674 ms merané).
- **APK „Krok"** — nie je v rozsahu repo.
- **MISTRAL_MODEL / CEREBRAS / GROQ / DEEPGRAM live kľúče na Render** — neoverené; lokálne chýbajú (overené prázdne/getenv). `.env.example` doplnený o placeholder y (2. audit).

## Zmeny vykonané v 2. audite (lokálne, NESTAGED, bez commitu)

- `app/modules/listings/presentation/router.py` — **ai_draft_stream AI tier gate** (+24/−4; 409 pre free tier, multi-company AI preference; frontend už 409 očakával).
- `tests/unit/test_ai_draft_stream_route.py` — nový, 7 testov (auth 401, free tier 409, bez firmy 409, ok s AI, multi-company, explicit company_id, free explicit 409).
- `tests/unit/test_voice_endpoints.py` — nový, 13 testov (transcribe: 401/403/409/415/400/413/200/502/admin bypass; token: 401/503/502/200).
- `apps/web/src/app/loading.tsx`, `error.tsx`, `not-found.tsx`, `global-error.tsx` — nové branded stránky.
- `apps/web/src/app/dashboard/admin/page.tsx` — sekcia „Odporúčania" s linkom na /admin/recommendations (doteraz orphan route).
- `.env.example` — doplnené MISTRAL_/CEREBRAS_/GROQ_STT_MODEL/DEEPGRAM_/STRIPE_ placeholder y (dokumentácia, žiadne tajomstvá).

## Výsledky testov (2. audit)

- Plná hermetická sada: `.venv/bin/pytest app/tests app/modules tests -q -p no:cacheprovider -o addopts=""` → **1185 passed, 0 failed, 0 xfailed** (1 benign warning: duplicate Operation ID `billing_notify`).
- `npx tsc --noEmit` → 0 chýb. `npm run build` → OK (exit 0).
- ruff check → čistý na všetkých zmenených súboroch; ruff format len na moje riadky (diff overený).
- Predchádzajúce sady: 1165 passed (pred 2. auditom) → 1185 (+7 stream, +13 voice).
- Obmedzenia: žiadne FE unit testy (vitest blocked); PG probe bežal len v predchádzajúcej diagnostike (36 kontrol, N1/N2 fixed); live provideri (Groq/Mistral/Cerebras/Deepgram/Stripe) NIE sú volaní v testoch; Render env neoveriteľný lokálne.