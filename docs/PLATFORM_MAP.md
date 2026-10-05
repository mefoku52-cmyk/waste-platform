# ♻️ Waste Platform — Kompletná mapa

> Generované: 2026-10-05 17:19 · 466 commitov · 23 kategórií · klasifikácia podľa ciest

## Obsah
- [1. Lead Finder](#1-lead-finder) (42)
- [2. Agent Platform](#2-agent-platform) (38)
- [3. Uploads & Signed URLs](#3-uploads--signed-urls) (5)
- [4. Listings](#4-listings) (5)
- [5. Notifications](#5-notifications) (3)
- [7. Auth & Security](#7-auth--security) (13)
- [8. Admin & Analytics](#8-admin--analytics) (4)
- [9. Backend moduly](#9-backend-moduly) (62)
- [10. Backend core / worker](#10-backend-core--worker) (11)
- [11. Admin UI](#11-admin-ui) (20)
- [12. Dashboard UI](#12-dashboard-ui) (38)
- [13. Landing / auth UI](#13-landing--auth-ui) (16)
- [14. Frontend features](#14-frontend-features) (50)
- [15. Frontend (build, config)](#15-frontend-build-config) (39)
- [16. Docs & Roadmap](#16-docs--roadmap) (16)
- [17. Scripts & ops](#17-scripts--ops) (27)
- [18. DB migrations](#18-db-migrations) (5)
- [20. CI / CD](#20-ci--cd) (8)
- [21. Tests](#21-tests) (26)
- [96. Fixes](#96-fixes) (9)
- [97. Refactors](#97-refactors) (1)
- [98. Chore](#98-chore) (15)
- [99. Ostatné](#99-ostatné) (13)

---

## 1. Lead Finder
*42 commitov · 141 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `be2a298` | 2026-10-05 | feat(observability): business metrics + scheduler alerts + ready probe |
| `38bb0ba` | 2026-10-05 | feat(email-finder): apply D2 rule for free email providers |
| `23910be` | 2026-10-05 | feat(lead-outreach): auto-approve + batch send endpoints |
| `e236a60` | 2026-10-04 | feat(db): add phone/website/source_url to outreach_candidates |
| `12b9d8b` | 2026-10-04 | feat(lead-outreach): draft pending NEW candidates (batch) |
| `385c0d1` | 2026-10-04 | feat(lead-finder): wire ZS category discovery into pipeline |
| `7612826` | 2026-10-04 | feat(lead-finder): ZS category discovery + D2 filter fix |
| `1fad979` | 2026-10-04 | feat(lead-outreach): AI fallback + provider status endpoint |
| `ebb9bd1` | 2026-10-04 | fix(website-finder): trip DDG breaker on first timeout |
| `bf95404` | 2026-10-04 | fix(website-finder): pin duckduckgo-search==5.3.1 (no primp) |
| `bba2af0` | 2026-10-04 | feat(crawler): short TTL for negative cache entries |
| `ce113c3` | 2026-10-04 | feat(lead-finder): add free TLD filter |
| `ec8d465` | 2026-10-03 | refactor(directory-lookup): _pick returns card mailto only, no homepage fetch |
| `e96bb58` | 2026-10-03 | fix(website-finder): skip hst.link URL shortener in _SKIP_DOMAINS |
| `ae3d486` | 2026-10-02 | fix(directory-lookup): enforce free-domain filter in mailto branch |
| `4ee861c` | 2026-10-02 | fix(lead-finder): directory_lookup as primary email source |
| `a4885dd` | 2026-10-02 | On main: verify-baseline-hstlink |
| `3540996` | 2026-10-02 | fix(lead-finder): switch website_finder from Brave to DuckDuckGo |
| `b93eca9` | 2026-10-02 | Fix lead outreach approval and sending workflow |
| `7976b8e` | 2026-10-02 | fix: type email discovery flow |
| `317d4af` | 2026-09-30 | fix(lead-finder): filter irrelevant and free emails |
| `6aefe2b` | 2026-09-30 | refactor(lead-finder): switch from Google CSE to DuckDuckGo |
| `a8a966a` | 2026-09-30 | feat(outreach): auto email discovery + daily 9:00 scheduler + async httpx |
| `9616d13` | 2026-09-30 | fix(lead-finder): add emails_found to DiscoverDailyResponse schema |
| `88317c3` | 2026-09-30 | feat(lead-finder): automatic email discovery via Google CSE |
| `17af10a` | 2026-09-30 | feat(lead-outreach): GDPR-compliant AI email drafter\n\n- new system prompt with legal framework:\n  * GDPR Art. 6(1)(f) - legitimate interest\n  * Slovak Act 452/2021 Z.z. § 116 - B2B email\n- mandatory GDPR footer in every email:\n  * source of data (RPO - Statistical Office SR)\n  * legal basis, rights, contact\n- mandatory opt-out sentence 'STOP' before signature\n- stricter content rules (no false promises, no marketing cliches)\n- clear signature (Radoslav Cornanic, CMEP, trc-cmep@gmail.com)\n- only for legal entities (companies), never individuals |
| `69087a5` | 2026-09-30 | feat(lead-outreach): LegalEmailFinder module (ready for web search) |
| `4105593` | 2026-09-30 | feat(lead-outreach): automatic draft generation + pending workflow |
| `88e8421` | 2026-09-29 | Keep discovering RPO queries until 30 unseen ICO are collected. |
| `029e1e6` | 2026-09-29 | Always return discover payload when the batch is full. |
| `78d185a` | 2026-09-29 | Run RPO discover every 12 hours with a valid scheduler job. |
| `caec138` | 2026-09-29 | Run a single RPO query per discover click to stay under Render limit. |
| `765d904` | 2026-09-28 | Rotate RPO queries and reuse unsaved outreach candidates. |
| `a2cdb1c` | 2026-09-28 | Make RPO discover return companies within browser timeout. |
| `054dff8` | 2026-09-28 | Show daily RPO discover results on lead outreach admin page. |
| `ec6558c` | 2026-09-28 | Store daily RPO outreach candidates and draft emails without sending. |
| `ffc4f45` | 2026-09-26 | feat(lead-finder): batch drafter service + draft-batch endpoint (max 30) |
| `46c22d5` | 2026-09-26 | feat(lead-finder): outreach_candidates table + entity + repository |
| `d40298d` | 2026-09-26 | feat(email): Resend sender with daily limit + SMTP fallback |
| `f8e106e` | 2026-09-26 | feat(lead-finder): early-bird offer in AI draft (first 10 verified companies get AI tier) |
| `e2c08dc` | 2026-09-26 | feat(lead-finder): AI email drafter + admin draft/send endpoints |
| `08b989c` | 2026-09-26 | fix(ai): orchestrator uses current_user scope + remove debug block |

<details><summary>Súbory</summary>

**`be2a298`** — feat(observability): business metrics + scheduler alerts + ready probe
- `app/main.py`
- `app/modules/lead_finder/application/services/auto_approve.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/modules/notifications/application/telegram_service.py`
- `app/modules/notifications/presentation/summary_router.py`
- `app/shared/infrastructure/scheduler.py`
- `app/shared/presentation/api_router.py`
- `app/shared/presentation/business_metrics.py`
- `tests/unit/test_business_metrics.py`

**`38bb0ba`** — feat(email-finder): apply D2 rule for free email providers
- `app/modules/lead_finder/application/services/email_finder.py`
- `tests/unit/test_email_finder_filters.py`

**`23910be`** — feat(lead-outreach): auto-approve + batch send endpoints
- `app/modules/lead_finder/application/services/auto_approve.py`
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `tests/unit/test_auto_approve.py`

**`e236a60`** — feat(db): add phone/website/source_url to outreach_candidates
- `app/modules/lead_finder/infrastructure/persistence/models.py`
- `app/modules/lead_finder/infrastructure/persistence/repositories.py`
- `migrations/versions/c6d7e8f9a0b1_add_outreach_contact_fields.py`
- `tests/unit/test_category_discover_flow.py`

**`12b9d8b`** — feat(lead-outreach): draft pending NEW candidates (batch)
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `tests/unit/test_draft_new_flow.py`

**`385c0d1`** — feat(lead-finder): wire ZS category discovery into pipeline
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/infrastructure/persistence/repositories.py`
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `tests/unit/test_category_discover_flow.py`

**`7612826`** — feat(lead-finder): ZS category discovery + D2 filter fix
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `app/modules/lead_finder/application/services/zs_category_discovery.py`
- `tests/unit/test_directory_lookup.py`
- `tests/unit/test_zs_category_discovery.py`

**`1fad979`** — feat(lead-outreach): AI fallback + provider status endpoint
- `app/modules/lead_finder/application/services/email_drafter.py`
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `tests/unit/test_email_drafter_fallback.py`
- `tests/unit/test_lead_outreach_status.py`

**`ebb9bd1`** — fix(website-finder): trip DDG breaker on first timeout
- `app/modules/lead_finder/application/services/website_finder.py`
- `docs/DDG_MIGRATION.md`
- `tests/unit/test_website_finder_ddg_breaker.py`

**`bf95404`** — fix(website-finder): pin duckduckgo-search==5.3.1 (no primp)
- `app/modules/lead_finder/application/services/website_finder.py`
- `app/requirements.txt`
- `docs/DDG_MIGRATION.md`
- `requirements.txt`

**`bba2af0`** — feat(crawler): short TTL for negative cache entries
- `app/modules/lead_finder/application/services/website_contact_crawler.py`
- `tests/unit/test_website_contact_crawler.py`

**`ce113c3`** — feat(lead-finder): add free TLD filter
- `app/modules/lead_finder/application/services/email_finder.py`
- `tests/unit/test_email_finder_filters.py`

**`ec8d465`** — refactor(directory-lookup): _pick returns card mailto only, no homepage fetch
- `app/modules/lead_finder/application/services/directory_lookup.py`

**`e96bb58`** — fix(website-finder): skip hst.link URL shortener in _SKIP_DOMAINS
- `app/modules/lead_finder/application/services/website_finder.py`

**`ae3d486`** — fix(directory-lookup): enforce free-domain filter in mailto branch
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `docs/BACKLOG.md`
- `tests/unit/test_directory_lookup.py`

**`4ee861c`** — fix(lead-finder): directory_lookup as primary email source
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/email_finder.py`

**`a4885dd`** — On main: verify-baseline-hstlink
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/email_finder.py`

**`3540996`** — fix(lead-finder): switch website_finder from Brave to DuckDuckGo
- `.env.example`
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/website_finder.py`
- `requirements.txt`

**`b93eca9`** — Fix lead outreach approval and sending workflow
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/website_finder.py`
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`7976b8e`** — fix: type email discovery flow
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `tests/unit/test_daily_discover_flow.py`
- `tests/unit/test_daily_discover_helpers.py`
- `tests/unit/test_directory_lookup.py`

**`317d4af`** — fix(lead-finder): filter irrelevant and free emails
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/email_finder.py`
- `app/modules/lead_finder/application/services/website_finder.py`

**`6aefe2b`** — refactor(lead-finder): switch from Google CSE to DuckDuckGo
- `app/modules/lead_finder/application/services/website_finder.py`
- `requirements.txt`

**`a8a966a`** — feat(outreach): auto email discovery + daily 9:00 scheduler + async httpx
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/email_finder.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/shared/infrastructure/scheduler.py`

**`9616d13`** — fix(lead-finder): add emails_found to DiscoverDailyResponse schema
- `app/modules/lead_finder/presentation/router.py`

**`88317c3`** — feat(lead-finder): automatic email discovery via Google CSE
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/application/services/website_finder.py`
- `requirements.txt`

**`17af10a`** — feat(lead-outreach): GDPR-compliant AI email drafter\n\n- new system prompt with legal framework:\n  * GDPR Art. 6(1)(f) - legitimate interest\n  * Slovak Act 452/2021 Z.z. § 116 - B2B email\n- mandatory GDPR footer in every email:\n  * source of data (RPO - Statistical Office SR)\n  * legal basis, rights, contact\n- mandatory opt-out sentence 'STOP' before signature\n- stricter content rules (no false promises, no marketing cliches)\n- clear signature (Radoslav Cornanic, CMEP, trc-cmep@gmail.com)\n- only for legal entities (companies), never individuals
- `app/modules/lead_finder/application/services/email_drafter.py`

**`69087a5`** — feat(lead-outreach): LegalEmailFinder module (ready for web search)
- `app/modules/lead_finder/application/services/email_finder.py`

**`4105593`** — feat(lead-outreach): automatic draft generation + pending workflow
- `app/modules/lead_finder/presentation/router.py`
- `app/shared/infrastructure/scheduler.py`

**`88e8421`** — Keep discovering RPO queries until 30 unseen ICO are collected.
- `app/modules/lead_finder/application/services/daily_discover.py`

**`029e1e6`** — Always return discover payload when the batch is full.
- `app/modules/lead_finder/application/services/daily_discover.py`

**`78d185a`** — Run RPO discover every 12 hours with a valid scheduler job.
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/shared/infrastructure/scheduler.py`

**`caec138`** — Run a single RPO query per discover click to stay under Render limit.
- `app/modules/lead_finder/application/services/daily_discover.py`

**`765d904`** — Rotate RPO queries and reuse unsaved outreach candidates.
- `app/modules/lead_finder/application/services/daily_discover.py`

**`a2cdb1c`** — Make RPO discover return companies within browser timeout.
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/presentation/router.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `apps/web/src/lib/api/http.ts`

**`054dff8`** — Show daily RPO discover results on lead outreach admin page.
- `app/modules/lead_finder/application/services/daily_discover.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`ec6558c`** — Store daily RPO outreach candidates and draft emails without sending.
- `app/modules/lead_finder/application/services/daily_discover.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/shared/infrastructure/scheduler.py`

**`ffc4f45`** — feat(lead-finder): batch drafter service + draft-batch endpoint (max 30)
- `app/modules/lead_finder/application/services/batch_drafter.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/modules/lead_finder/tests/test_batch_drafter.py`

**`46c22d5`** — feat(lead-finder): outreach_candidates table + entity + repository
- `app/modules/lead_finder/domain/entities/outreach_candidate.py`
- `app/modules/lead_finder/infrastructure/persistence/models.py`
- `app/modules/lead_finder/infrastructure/persistence/repositories.py`
- `app/modules/lead_finder/tests/test_outreach_entity.py`
- `app/shared/infrastructure/db/register_models.py`
- `migrations/versions/a3c4d5e6f7a8_add_outreach_candidates.py`

**`d40298d`** — feat(email): Resend sender with daily limit + SMTP fallback
- `app/core/config.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/modules/lead_finder/tests/test_resend_sender.py`
- `app/shared/infrastructure/email/resend_sender.py`

**`f8e106e`** — feat(lead-finder): early-bird offer in AI draft (first 10 verified companies get AI tier)
- `app/modules/lead_finder/application/services/email_drafter.py`
- `app/modules/lead_finder/presentation/router.py`

**`e2c08dc`** — feat(lead-finder): AI email drafter + admin draft/send endpoints
- `app/modules/lead_finder/application/services/email_drafter.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/modules/lead_finder/tests/__init__.py`
- `app/modules/lead_finder/tests/test_email_drafter.py`
- `app/shared/presentation/api_router.py`

**`08b989c`** — fix(ai): orchestrator uses current_user scope + remove debug block
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/lead_finder/__init__.py`
- `app/modules/lead_finder/application/__init__.py`
- `app/modules/lead_finder/application/services/__init__.py`
- `app/modules/lead_finder/domain/__init__.py`
- `app/modules/lead_finder/domain/entities/__init__.py`
- `app/modules/lead_finder/infrastructure/__init__.py`
- `app/modules/lead_finder/infrastructure/orsr/__init__.py`
- `app/modules/lead_finder/infrastructure/persistence/__init__.py`
- `app/modules/lead_finder/infrastructure/resend/__init__.py`
- `app/modules/lead_finder/presentation/__init__.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`

</details>

## 2. Agent Platform
*38 commitov · 315 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `28680a3` | 2026-10-03 | fix(agent-platform): normalize governance datetimes to naive UTC |
| `1e8e1b3` | 2026-09-30 | security(agent-platform): remove personal name leak from public /control/status |
| `414943a` | 2026-09-30 | fix(security): naive UTC conversion for governance timestamps\n\nRoot cause: asyncpg rejects tz-aware datetime for TIMESTAMP WITHOUT TIME ZONE columns.\nThe previous _apply_security_check silently failed because of this.\n\n- new helper to_naive_utc in shared/infrastructure/db/timezone.py\n- applied in security_event_store (observation + signal)\n- applied in alert_repository, approval_repository, control_repository, audit_store\n- all datetime writes to governance tables now naive UTC\n\nThis fixes: alerts, security events, approvals, audit records all\nstayed at count=0 even after successful endpoint calls. |
| `4ecaabc` | 2026-09-30 | feat(web): Google Custom Search JSON API gateway\n\n- new GoogleWebSearchGateway (httpx, 100 queries/day free)\n- alias WebSearchGateway = GoogleWebSearchGateway (backward compat)\n- new WebResultNormalizer for safe internal records\n- requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID\n- Bing Search API retired Aug 11 2025, not usable |
| `437e2aa` | 2026-09-30 | debug(security): add POST /agent-platform/security/test-write |
| `5fec543` | 2026-09-30 | fix(security): write observation to DB + own session + diagnostics |
| `b4b1889` | 2026-09-30 | feat(security): AI chat blocking on critical patterns |
| `322ac6a` | 2026-09-30 | feat(security): detect prompt injection / leakage / escalation in AI chat |
| `e64dac7` | 2026-09-30 | feat(agent-platform): governance services, DI wiring, event bus, security engine, audit hook |
| `20cda59` | 2026-09-29 | Fix duplicate agent governance types and missing ControlMode/AsyncSession imports. |
| `2b27102` | 2026-09-28 | Fix agent_platform verify scripts for Termux bash. |
| `407481c` | 2026-09-28 | Add agent_platform inspect and contract verify scripts. |
| `04fa58e` | 2026-09-26 | chore: archive historical backups and dev noise |
| `b776ba6` | 2026-09-26 | feat(agent): transport + nearby companies READ-ONLY tools |
| `779a7f9` | 2026-09-26 | fix(agent): admin recent_activity datetime filter + cleaner chat error |
| `bf2b189` | 2026-09-26 | feat(agent): admin-only read tools (stats, activity, tiers, context) |
| `9041bbc` | 2026-09-26 | fix(agent-memory): use current_user_id() for actor_id (correct UUID) |
| `c70ab45` | 2026-09-26 | fix(agent-memory): commit conversation and message inserts (flush -> commit) |
| `f8c42a4` | 2026-09-26 | feat(agent): role-aware system prompt (architect vs customer) |
| `e999046` | 2026-09-26 | feat(agent-memory): conversation history in chat router + context builder |
| `2d66e56` | 2026-09-26 | feat(agent-memory): ai_conversations + ai_messages tables and repository |
| `1fbcd31` | 2026-09-26 | feat(agent): gate AI chat by company subscription tier (PRO/AI) |
| `46fee93` | 2026-09-26 | fix(agent): health reports chat=true (chat router is mounted and gated) |
| `8dad364` | 2026-09-26 | Publish agent tool events through existing event store |
| `b753b90` | 2026-09-26 | Record audit outcome for each agent tool decision |
| `7db6117` | 2026-09-26 | Wire permission gate before agent tool execution |
| `7eeb24e` | 2026-09-26 | Wire policy gate before agent tool execution |
| `58255ae` | 2026-09-26 | feat: AI scope from current_user + terms for GoPay |
| `2cf3c3d` | 2026-09-26 | fix(ai): require auth for chat + widget only for logged users + company scope by membership |
| `e323023` | 2026-09-26 | feat: AI agent tool calling + delete listing + promote listing (backend+frontend+i18n) |
| `ef0a600` | 2026-09-25 | feat(ai): add CMEP system prompt + security rules |
| `2d7e811` | 2026-09-25 | fix(groq): switch to openai/gpt-oss-120b (llama not available on account) |
| `fe5e9f3` | 2026-09-25 | fix(groq): use llama-3.3-70b-versatile + browser User-Agent |
| `82236cd` | 2026-09-25 | Build ModelRequest and ModelResponse with required fields for Groq. |
| `e652c61` | 2026-09-25 | Add Groq provider matching ModelGateway and ignore local backup files. |
| `6f25d00` | 2026-09-24 | Add user AI chat and Radoslav control status without live model or commands. |
| `e56f14e` | 2026-09-24 | Expose agent-platform health router without enabling chat. |
| `3f3bd0e` | 2026-09-24 | Add agent_platform module tree without wiring HTTP routers. |

<details><summary>Súbory</summary>

**`28680a3`** — fix(agent-platform): normalize governance datetimes to naive UTC
- `app/modules/agent_platform/application/approval/approval_service.py`
- `app/modules/agent_platform/infrastructure/persistence/approval_repository.py`
- `app/modules/agent_platform/infrastructure/persistence/control_repository.py`
- `tests/unit/test_timezone_naive_utc.py`

**`1e8e1b3`** — security(agent-platform): remove personal name leak from public /control/status
- `app/modules/agent_platform/presentation/control_router.py`

**`414943a`** — fix(security): naive UTC conversion for governance timestamps\n\nRoot cause: asyncpg rejects tz-aware datetime for TIMESTAMP WITHOUT TIME ZONE columns.\nThe previous _apply_security_check silently failed because of this.\n\n- new helper to_naive_utc in shared/infrastructure/db/timezone.py\n- applied in security_event_store (observation + signal)\n- applied in alert_repository, approval_repository, control_repository, audit_store\n- all datetime writes to governance tables now naive UTC\n\nThis fixes: alerts, security events, approvals, audit records all\nstayed at count=0 even after successful endpoint calls.
- `app/modules/agent_platform/infrastructure/audit/audit_store.py`
- `app/modules/agent_platform/infrastructure/persistence/alert_repository.py`
- `app/modules/agent_platform/infrastructure/persistence/approval_repository.py`
- `app/modules/agent_platform/infrastructure/persistence/control_repository.py`
- `app/modules/agent_platform/infrastructure/security/security_event_store.py`
- `app/shared/infrastructure/db/timezone.py`

**`4ecaabc`** — feat(web): Google Custom Search JSON API gateway\n\n- new GoogleWebSearchGateway (httpx, 100 queries/day free)\n- alias WebSearchGateway = GoogleWebSearchGateway (backward compat)\n- new WebResultNormalizer for safe internal records\n- requires GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID\n- Bing Search API retired Aug 11 2025, not usable
- `app/modules/agent_platform/infrastructure/web/__init__.py`
- `app/modules/agent_platform/infrastructure/web/web_result_normalizer.py`
- `app/modules/agent_platform/infrastructure/web/web_search_gateway.py`

**`437e2aa`** — debug(security): add POST /agent-platform/security/test-write
- `app/modules/agent_platform/presentation/security_router.py`

**`5fec543`** — fix(security): write observation to DB + own session + diagnostics
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/security_router.py`

**`b4b1889`** — feat(security): AI chat blocking on critical patterns
- `app/modules/agent_platform/application/security/security_engine.py`
- `app/modules/agent_platform/presentation/chat_router.py`

**`322ac6a`** — feat(security): detect prompt injection / leakage / escalation in AI chat
- `app/modules/agent_platform/presentation/chat_router.py`

**`e64dac7`** — feat(agent-platform): governance services, DI wiring, event bus, security engine, audit hook
- `app/modules/agent_platform/application/approval/approval_workflow.py`
- `app/modules/agent_platform/application/events/event_bus.py`
- `app/modules/agent_platform/application/events/event_dispatcher.py`
- `app/modules/agent_platform/application/events/event_processor.py`
- `app/modules/agent_platform/application/security/security_alert_service.py`
- `app/modules/agent_platform/application/security/security_risk_engine.py`
- `app/modules/agent_platform/application/security/security_signal_service.py`
- `app/modules/agent_platform/infrastructure/events/event_store.py`
- `app/modules/agent_platform/infrastructure/persistence/agent_repository.py`
- `app/modules/agent_platform/presentation/approvals_router.py`
- `app/modules/agent_platform/presentation/audit_router.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/presentation/security_router.py`
- `migrations/versions/a4b5c6d7e8f9_add_agent_governance_tables.py`

**`20cda59`** — Fix duplicate agent governance types and missing ControlMode/AsyncSession imports.
- `app/modules/agent_platform/application/alerts/alert_service.py`
- `app/modules/agent_platform/application/approval/approval_service.py`
- `app/modules/agent_platform/application/audit/audit_service.py`
- `app/modules/agent_platform/application/control/break_glass_service.py`
- `app/modules/agent_platform/application/control/control_service.py`
- `app/modules/agent_platform/application/control/emergency_service.py`
- `app/modules/agent_platform/application/security/security_engine.py`
- `app/modules/agent_platform/infrastructure/audit/audit_store.py`
- `app/modules/agent_platform/infrastructure/models.py`
- `app/modules/agent_platform/infrastructure/persistence/alert_repository.py`
- `app/modules/agent_platform/infrastructure/persistence/approval_repository.py`
- `app/modules/agent_platform/infrastructure/persistence/control_repository.py`
- `app/modules/agent_platform/infrastructure/security/security_event_store.py`
- `app/modules/agent_platform/presentation/alerts_router.py`
- `app/modules/agent_platform/presentation/approvals_router.py`
- `app/modules/agent_platform/presentation/audit_router.py`
- `app/modules/agent_platform/presentation/control_router.py`
- `app/modules/agent_platform/presentation/security_router.py`
- `app/shared/infrastructure/db/register_models.py`
- `app/shared/presentation/api_router.py`

**`2b27102`** — Fix agent_platform verify scripts for Termux bash.
- `app/modules/agent_platform/scripts/inspect_agent_platform.sh`
- `app/modules/agent_platform/scripts/verify_agent_contracts.sh`
- `app/modules/agent_platform/scripts/verify_policy_boundaries.sh`
- `app/modules/agent_platform/scripts/verify_security_events.sh`
- `app/modules/agent_platform/scripts/verify_tool_registry.sh`

**`407481c`** — Add agent_platform inspect and contract verify scripts.
- `app/modules/agent_platform/scripts/inspect_agent_platform.sh`
- `app/modules/agent_platform/scripts/verify_agent_contracts.sh`
- `app/modules/agent_platform/scripts/verify_policy_boundaries.sh`
- `app/modules/agent_platform/scripts/verify_security_events.sh`
- `app/modules/agent_platform/scripts/verify_tool_registry.sh`

**`04fa58e`** — chore: archive historical backups and dev noise
- `.gitignore`
- `_archive/README.md`
- `app/modules/agent_platform/infrastructure/tools/handler_adapters.py.backup-20260923_154738`
- `app/modules/agent_platform/infrastructure/tools/handler_adapters.py.backup-20260923_163639`
- `app/modules/agent_platform/infrastructure/tools/handler_adapters.py.backup-20260923_183446`
- `app/modules/agent_platform/infrastructure/tools/phase5_tool_wiring.py.backup-20260923_154738`
- `app/modules/agent_platform/infrastructure/tools/production_company_search.py.backup-20260923_181450`
- `app/modules/agent_platform/tests/test_phase5_tool_wiring.py.backup-20260923_154738`
- `app/modules/agent_platform/tests/test_phase5_tool_wiring.py.backup-20260923_163639`
- `app/modules/agent_platform/tests/test_phase5_tool_wiring.py.backup-20260923_183446`

**`b776ba6`** — feat(agent): transport + nearby companies READ-ONLY tools
- `app/modules/agent_platform/infrastructure/tools/cmep_listing_transport_handler.py`
- `app/modules/agent_platform/infrastructure/tools/cmep_nearby_companies_handler.py`
- `app/modules/agent_platform/infrastructure/tools/tool_schemas.py`
- `app/modules/agent_platform/presentation/dependencies.py`

**`779a7f9`** — fix(agent): admin recent_activity datetime filter + cleaner chat error
- `app/modules/agent_platform/infrastructure/tools/cmep_admin_tools.py`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`

**`bf2b189`** — feat(agent): admin-only read tools (stats, activity, tiers, context)
- `app/modules/agent_platform/infrastructure/tools/cmep_admin_tools.py`
- `app/modules/agent_platform/infrastructure/tools/tool_schemas.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_admin_tools.py`

**`9041bbc`** — fix(agent-memory): use current_user_id() for actor_id (correct UUID)
- `app/modules/agent_platform/presentation/chat_router.py`

**`c70ab45`** — fix(agent-memory): commit conversation and message inserts (flush -> commit)
- `app/modules/agent_platform/infrastructure/persistence/ai_conversation_repository.py`

**`f8c42a4`** — feat(agent): role-aware system prompt (architect vs customer)
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/tests/test_role_aware_prompt.py`

**`e999046`** — feat(agent-memory): conversation history in chat router + context builder
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/application/memory/__init__.py`
- `app/modules/agent_platform/application/memory/context_builder.py`
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_context_builder.py`

**`2d66e56`** — feat(agent-memory): ai_conversations + ai_messages tables and repository
- `app/modules/agent_platform/domain/memory/__init__.py`
- `app/modules/agent_platform/domain/memory/ai_conversation.py`
- `app/modules/agent_platform/domain/memory/ai_message.py`
- `app/modules/agent_platform/infrastructure/models.py`
- `app/modules/agent_platform/infrastructure/persistence/__init__.py`
- `app/modules/agent_platform/infrastructure/persistence/ai_conversation_repository.py`
- `app/shared/infrastructure/db/register_models.py`
- `migrations/versions/a2b3c4d5e6f7_add_ai_memory_tables.py`

**`1fbcd31`** — feat(agent): gate AI chat by company subscription tier (PRO/AI)
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_chat_gate.py`

**`46fee93`** — fix(agent): health reports chat=true (chat router is mounted and gated)
- `app/modules/agent_platform/presentation/router.py`

**`8dad364`** — Publish agent tool events through existing event store
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/infrastructure/events/sqlalchemy_event_publisher.py`
- `app/modules/agent_platform/presentation/dependencies.py`

**`b753b90`** — Record audit outcome for each agent tool decision
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_agent_audit.py`

**`7db6117`** — Wire permission gate before agent tool execution
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/infrastructure/permission/__init__.py`
- `app/modules/agent_platform/infrastructure/permission/actor_tool_permission_engine.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_agent_permission_gate.py`

**`7eeb24e`** — Wire policy gate before agent tool execution
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/infrastructure/policy/__init__.py`
- `app/modules/agent_platform/infrastructure/policy/allowlist_policy_engine.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/agent_platform/tests/test_agent_policy_gate.py`

**`58255ae`** — feat: AI scope from current_user + terms for GoPay
- `app/modules/agent_platform/presentation/dependencies.py`
- `apps/web/src/app/terms/page.tsx`

**`2cf3c3d`** — fix(ai): require auth for chat + widget only for logged users + company scope by membership
- `app/modules/agent_platform/infrastructure/tools/cmep_company_search_handler.py`
- `app/modules/agent_platform/presentation/chat_router.py`
- `apps/web/src/components/layout/app-shell.tsx`

**`e323023`** — feat: AI agent tool calling + delete listing + promote listing (backend+frontend+i18n)
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/infrastructure/ai/groq_gateway.py`
- `app/modules/agent_platform/infrastructure/ai/model_gateway.py`
- `app/modules/agent_platform/infrastructure/ai/model_request.py`
- `app/modules/agent_platform/infrastructure/ai/model_response.py`
- `app/modules/agent_platform/infrastructure/tools/cmep_company_search_handler.py`
- `app/modules/agent_platform/infrastructure/tools/cmep_listing_search_handler.py`
- `app/modules/agent_platform/infrastructure/tools/tool_schemas.py`
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/listings/application/services.py`
- `app/modules/listings/domain/entities.py`
- `app/modules/listings/domain/repositories.py`
- `app/modules/listings/infrastructure/mappers.py`
- `app/modules/listings/infrastructure/models.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/listings/presentation/schemas.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/listings/components/promote-badge.tsx`
- `apps/web/src/features/listings/components/promote-listing-button.tsx`
- `apps/web/src/features/listings/types.ts`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`
- `migrations/versions/f1a2b3c4d5e6_add_listing_promoted_until.py`

**`ef0a600`** — feat(ai): add CMEP system prompt + security rules
- `app/modules/agent_platform/presentation/chat_router.py`

**`2d7e811`** — fix(groq): switch to openai/gpt-oss-120b (llama not available on account)
- `app/modules/agent_platform/infrastructure/ai/groq_gateway.py`

**`fe5e9f3`** — fix(groq): use llama-3.3-70b-versatile + browser User-Agent
- `app/modules/agent_platform/infrastructure/ai/groq_gateway.py`

**`82236cd`** — Build ModelRequest and ModelResponse with required fields for Groq.
- `app/modules/agent_platform/infrastructure/ai/groq_gateway.py`
- `app/modules/agent_platform/presentation/chat_router.py`

**`e652c61`** — Add Groq provider matching ModelGateway and ignore local backup files.
- `app/modules/agent_platform/infrastructure/ai/groq_gateway.py`
- `app/modules/agent_platform/presentation/chat_router.py`

**`6f25d00`** — Add user AI chat and Radoslav control status without live model or commands.
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/control_router.py`
- `app/shared/presentation/api_router.py`

**`e56f14e`** — Expose agent-platform health router without enabling chat.
- `app/modules/agent_platform/presentation/__init__.py`
- `app/modules/agent_platform/presentation/router.py`
- `app/shared/presentation/api_router.py`

**`3f3bd0e`** — Add agent_platform module tree without wiring HTTP routers.
- `app/modules/agent_platform/__init__.py`
- `app/modules/agent_platform/application/__init__.py`
- `app/modules/agent_platform/application/agent/__init__.py`
- `app/modules/agent_platform/application/agent/agent_context.py`
- `app/modules/agent_platform/application/agent/agent_orchestrator.py`
- `app/modules/agent_platform/application/agent/agent_response.py`
- `app/modules/agent_platform/application/agent/agent_runtime.py`
- `app/modules/agent_platform/application/agent/agent_session.py`
- `app/modules/agent_platform/application/alerts/__init__.py`
- `app/modules/agent_platform/application/alerts/alert_service.py`
- `app/modules/agent_platform/application/approval/__init__.py`
- `app/modules/agent_platform/application/approval/approval_service.py`
- `app/modules/agent_platform/application/approval/approval_workflow.py`
- `app/modules/agent_platform/application/audit/__init__.py`
- `app/modules/agent_platform/application/audit/audit_service.py`
- `app/modules/agent_platform/application/control/__init__.py`
- `app/modules/agent_platform/application/control/break_glass_service.py`
- `app/modules/agent_platform/application/control/control_service.py`
- `app/modules/agent_platform/application/control/emergency_service.py`
- `app/modules/agent_platform/application/decisions/__init__.py`
- `app/modules/agent_platform/application/decisions/pipeline_decision.py`
- `app/modules/agent_platform/application/events/__init__.py`
- `app/modules/agent_platform/application/events/event_bus.py`
- `app/modules/agent_platform/application/events/event_dispatcher.py`
- `app/modules/agent_platform/application/events/event_processor.py`
- `app/modules/agent_platform/application/permission/__init__.py`
- `app/modules/agent_platform/application/permission/permission_engine.py`
- `app/modules/agent_platform/application/permission/permission_resolver.py`
- `app/modules/agent_platform/application/pipeline/__init__.py`
- `app/modules/agent_platform/application/pipeline/agent_pipeline.py`
- … +116 ďalších

</details>

## 3. Uploads & Signed URLs
*5 commitov · 16 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `9096160` | 2026-10-05 | feat(uploads): add HMAC-signed URLs for file access |
| `16f75bf` | 2026-09-30 | fix(T1+T2): uploads trailing slash + mock RPO in company test |
| `1619924` | 2026-09-19 | fix uploads: store files under APP_DATA_DIR persistent path |
| `a5867b6` | 2026-09-14 | fix(uploads): make GET /uploads/{file} public so <img> can render |
| `b6045da` | 2026-08-16 | P3.1: local file upload API /api/v1/uploads + FE upload helper |

<details><summary>Súbory</summary>

**`9096160`** — feat(uploads): add HMAC-signed URLs for file access
- `app/core/config.py`
- `app/modules/uploads/application/signing.py`
- `app/modules/uploads/presentation/router.py`
- `docs/BACKLOG.md`
- `tests/unit/test_uploads_signing.py`

**`16f75bf`** — fix(T1+T2): uploads trailing slash + mock RPO in company test
- `app/modules/uploads/presentation/router.py`
- `docs/PLATFORM_STATUS.md`
- `tests/unit/test_company_transition.py`

**`1619924`** — fix uploads: store files under APP_DATA_DIR persistent path
- `app/modules/uploads/presentation/router.py`

**`a5867b6`** — fix(uploads): make GET /uploads/{file} public so <img> can render
- `app/modules/uploads/presentation/router.py`

**`b6045da`** — P3.1: local file upload API /api/v1/uploads + FE upload helper
- `.gitignore`
- `app/modules/uploads/__init__.py`
- `app/modules/uploads/presentation/__init__.py`
- `app/modules/uploads/presentation/router.py`
- `app/shared/presentation/api_router.py`
- `apps/web/src/features/uploads/api.ts`

</details>

## 4. Listings
*5 commitov · 51 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `a4ff009` | 2026-09-22 | Require listing location before publish. |
| `7119b25` | 2026-09-20 | Fix listing detail fetch and add recommendation field migration. |
| `34c0355` | 2026-09-14 | feat(listings): listing views + stats (backend, alembic migration) |
| `f23108c` | 2026-08-16 | matching MVP: /listings/matches by materialType + FE Odporucane zhody |
| `cfba6b2` | 2026-08-08 | Feat: kompletna implementacia listings modulu (entity, model, mapper, repository, service, schemas, router) - vzorova sablona pre zvysnych 6 modulov |

<details><summary>Súbory</summary>

**`a4ff009`** — Require listing location before publish.
- `app/modules/listings/application/services.py`

**`7119b25`** — Fix listing detail fetch and add recommendation field migration.
- `app/modules/listings/domain/legal_regime.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `migrations/versions/d4e7b2c1a9f0_add_recommendation_fields.py`

**`34c0355`** — feat(listings): listing views + stats (backend, alembic migration)
- `Makefile`
- `app/modules/auth/infrastructure/repositories.py`
- `app/modules/inquiries/application/services.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/application/services.py`
- `app/modules/listings/domain/repositories.py`
- `app/modules/listings/infrastructure/models.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/listings/presentation/schemas.py`
- `app/shared/application/side_effects.py`
- `app/shared/infrastructure/db/register_models.py`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`
- `migrations/versions/a8f3c9d1e5b7_add_listing_views.py`

**`f23108c`** — matching MVP: /listings/matches by materialType + FE Odporucane zhody
- `app/modules/listings/application/services.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/router.py`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/listings/api.ts`
- `apps/web/src/features/listings/components/matches-panel.tsx`
- `apps/web/src/features/listings/hooks/use-matches.ts`

**`cfba6b2`** — Feat: kompletna implementacia listings modulu (entity, model, mapper, repository, service, schemas, router) - vzorova sablona pre zvysnych 6 modulov
- `app/modules/listings/application/services.py`
- `app/modules/listings/application/services.py.bak-20260808-064133`
- `app/modules/listings/domain/entities.py`
- `app/modules/listings/domain/entities.py.bak-20260808-063424`
- `app/modules/listings/domain/entities.py.bak2-20260808-063650`
- `app/modules/listings/domain/enums.py`
- `app/modules/listings/domain/enums.py.bak-20260808-063812`
- `app/modules/listings/domain/repositories.py`
- `app/modules/listings/domain/repositories.py.bak-20260808-064133`
- `app/modules/listings/infrastructure/mappers.py`
- `app/modules/listings/infrastructure/models.py`
- `app/modules/listings/infrastructure/models.py.bak-20260808-064022`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/infrastructure/repositories.py.bak-20260808-064058`
- `app/modules/listings/presentation/dependencies.py`
- `app/modules/listings/presentation/dependencies.py.bak-20260808-064342`
- `app/modules/listings/presentation/router.py`
- `app/modules/listings/presentation/router.py.bak-20260808-064342`
- `app/modules/listings/presentation/schemas.py`
- `app/modules/listings/presentation/schemas.py.bak-20260808-064303`

</details>

## 5. Notifications
*3 commitov · 22 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `391b98d` | 2026-10-04 | security(telegram): harden webhook, rate limit, redact token |
| `aec1a1b` | 2026-10-04 | feat(notifications): add Telegram bot integration |
| `1564ced` | 2026-09-16 | fix(notifications): add @abstractmethod to count_unread |

<details><summary>Súbory</summary>

**`391b98d`** — security(telegram): harden webhook, rate limit, redact token
- `app/core/config.py`
- `app/modules/notifications/application/telegram_service.py`
- `app/modules/notifications/infrastructure/telegram_client.py`
- `app/modules/notifications/presentation/telegram_router.py`
- `scripts/telegram_webhook_setup.sh`
- `tests/unit/test_telegram_webhook.py`

**`aec1a1b`** — feat(notifications): add Telegram bot integration
- `app/core/config.py`
- `app/modules/lead_finder/presentation/router.py`
- `app/modules/notifications/application/telegram_service.py`
- `app/modules/notifications/infrastructure/telegram_client.py`
- `app/modules/notifications/presentation/telegram_router.py`
- `app/shared/presentation/api_router.py`
- `tests/unit/test_telegram_service.py`

**`1564ced`** — fix(notifications): add @abstractmethod to count_unread
- `app/modules/chat/presentation/router.py`
- `app/modules/notifications/application/services.py`
- `app/modules/notifications/domain/repositories.py`
- `app/modules/notifications/infrastructure/repositories.py`
- `app/modules/notifications/presentation/router.py`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/notifications/api.ts`
- `apps/web/src/features/notifications/hooks/use-unread-count.ts`
- `apps/web/src/features/notifications/index.ts`

</details>

## 7. Auth & Security
*13 commitov · 74 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `8834f62` | 2026-09-30 | fix: outreach backfill UI, safe user cleanup, refresh ABC, notification mapper |
| `dcfd428` | 2026-09-30 | feat(auth): 2FA (TOTP) for admin accounts |
| `0b352e8` | 2026-09-19 | feat auth: email verification on registration (backend) |
| `b1662ee` | 2026-09-16 | fix(auth): use FRONTEND_URL env directly for reset email link (no localhost) |
| `7e331d0` | 2026-08-26 | chore: remove backups and obsolete temporary files |
| `e13d820` | 2026-08-18 | refactor(auth-api): unify auth errors and token revocation handling |
| `0b6e43e` | 2026-08-18 | test(auth): cover password reset revocation flow |
| `91a9c05` | 2026-08-16 | P0.2: clean password_reset.py – FRONTEND_URL link, resetToken only in dev |
| `0a6eeb5` | 2026-08-16 | P0.2: fix password_reset syntax; FRONTEND_URL + resetToken only in dev |
| `261c49a` | 2026-08-16 | P0.2 fix: FRONTEND_URL link + syntax; resetToken only in development |
| `8b507a1` | 2026-08-16 | security: rate limit login+forgot (Redis); cleanup login forgot text |
| `8930027` | 2026-08-16 | auth: forgot/reset password API + FE; JWT secrets stable; password_hash on update |
| `c79bc0e` | 2026-08-08 | Fix: presmerovanie auth na db.session (odstranenie duplicity), ocistenie api_router.py od duplicitnych health/metrics routes |

<details><summary>Súbory</summary>

**`8834f62`** — fix: outreach backfill UI, safe user cleanup, refresh ABC, notification mapper
- `app/modules/auth/infrastructure/mappers.py`
- `app/modules/auth/infrastructure/repositories.py`
- `app/modules/lead_finder/application/services/backfill_emails.py`
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `app/modules/notifications/presentation/mappers.py`
- `app/shared/infrastructure/scheduler.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `scripts/ops/e2e_smoke.py`
- `tests/unit/modules/auth/test_refresh_session_repository.py`
- `tests/unit/test_notifications_presentation.py`

**`dcfd428`** — feat(auth): 2FA (TOTP) for admin accounts
- `app/modules/auth/application/dto.py`
- `app/modules/auth/application/services.py`
- `app/modules/auth/application/two_factor.py`
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/auth/presentation/schemas.py`
- `app/modules/users/infrastructure/models.py`
- `app/shared/infrastructure/db/register_models.py`
- `app/shared/infrastructure/security/jwt_service.py`
- `migrations/versions/b5c6d7e8f9a0_add_user_2fa.py`
- `pyproject.toml`
- `requirements.txt`

**`0b352e8`** — feat auth: email verification on registration (backend)
- `app/modules/auth/application/email_verification.py`
- `app/modules/auth/application/services.py`
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/auth/presentation/schemas.py`
- `app/modules/users/application/services.py`
- `app/modules/users/domain/entities.py`
- `app/modules/users/domain/enums.py`
- `app/modules/users/presentation/router.py`

**`b1662ee`** — fix(auth): use FRONTEND_URL env directly for reset email link (no localhost)
- `app/modules/auth/application/password_reset.py`

**`7e331d0`** — chore: remove backups and obsolete temporary files
- `.backup-eslint/.eslintrc.json.bak`
- `.backup-eslint/package.json.bak`
- `.env.bak.20260817-115539`
- `.env.bak.20260817-115628`
- `.env.local.template`
- `.env.production.example`
- `app/modules/auth/domain/entities.py.bak`
- `app/modules/listings/domain/entities.py.bak2-20260808-063650`
- `fix_and_test.sh`

**`e13d820`** — refactor(auth-api): unify auth errors and token revocation handling
- `app/modules/auth/application/services.py`
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/auth/presentation/router.py`
- `app/shared/infrastructure/security/jwt_exceptions.py`
- `app/shared/infrastructure/security/jwt_service.py`
- `app/shared/presentation/auth_dependencies.py`
- `app/shared/presentation/error_schemas.py`
- `app/shared/presentation/exception_handlers.py`
- `app/shared/presentation/schemas.py`

**`0b6e43e`** — test(auth): cover password reset revocation flow
- `app/modules/auth/application/password_reset.py`
- `app/shared/infrastructure/db/base.py`
- `app/shared/infrastructure/security/jwt_revocation_store.py`
- `tests/test_auth_password_reset_revocation.py`

**`91a9c05`** — P0.2: clean password_reset.py – FRONTEND_URL link, resetToken only in dev
- `app/modules/auth/application/password_reset.py`

**`0a6eeb5`** — P0.2: fix password_reset syntax; FRONTEND_URL + resetToken only in dev
- `app/modules/auth/application/password_reset.py`

**`261c49a`** — P0.2 fix: FRONTEND_URL link + syntax; resetToken only in development
- `app/modules/auth/application/password_reset.py`

**`8b507a1`** — security: rate limit login+forgot (Redis); cleanup login forgot text
- `app/modules/auth/presentation/router.py`
- `app/shared/infrastructure/rate_limit.py`
- `apps/web/src/features/auth/components/login-form.tsx`

**`8930027`** — auth: forgot/reset password API + FE; JWT secrets stable; password_hash on update
- `app/modules/auth/application/password_reset.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/auth/presentation/schemas.py`
- `app/modules/users/infrastructure/repositories.py`
- `app/shared/infrastructure/email/sender.py`
- `apps/web/src/app/forgot-password/page.tsx`
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/features/auth/api.ts`
- `apps/web/src/features/auth/components/login-form.tsx`

**`c79bc0e`** — Fix: presmerovanie auth na db.session (odstranenie duplicity), ocistenie api_router.py od duplicitnych health/metrics routes
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/auth/presentation/dependencies.py.bak-20260808-003920`
- `app/shared/infrastructure/database.py.unused_duplicate`
- `app/shared/presentation/api_router.py`
- `app/shared/presentation/api_router.py.bak-20260808-004211`

</details>

## 8. Admin & Analytics
*4 commitov · 26 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `1fe6c46` | 2026-08-26 | refactor(admin): align admin module with layered structure |
| `cbc3009` | 2026-08-17 | phase: admin audit append-only; unified error schema; checkpoint prep |
| `9ed636e` | 2026-08-15 | security: filter notifications by user, documents by company membership, audit by actor |
| `c7e1e4c` | 2026-08-08 | stabilize API surface and dependency manifest |

<details><summary>Súbory</summary>

**`1fe6c46`** — refactor(admin): align admin module with layered structure
- `app/modules/admin/__init__.py`
- `app/modules/admin/models.py`
- `app/modules/admin/router.py`
- `app/modules/admin/service.py`

**`cbc3009`** — phase: admin audit append-only; unified error schema; checkpoint prep
- `app/modules/admin/presentation/router.py`
- `app/shared/presentation/error_schemas.py`

**`9ed636e`** — security: filter notifications by user, documents by company membership, audit by actor
- `app/modules/admin/application/services.py`
- `app/modules/admin/infrastructure/repositories.py`
- `app/modules/admin/presentation/router.py`
- `app/modules/documents/application/services.py`
- `app/modules/documents/infrastructure/repositories.py`
- `app/modules/documents/presentation/router.py`
- `app/modules/notifications/application/services.py`
- `app/modules/notifications/infrastructure/repositories.py`
- `app/modules/notifications/presentation/router.py`
- `apps/web/src/app/dashboard/page.tsx`

**`c7e1e4c`** — stabilize API surface and dependency manifest
- `app/modules/admin/application/services.py`
- `app/modules/admin/domain/entities.py`
- `app/modules/admin/infrastructure/repositories.py`
- `app/modules/admin/presentation/router.py`
- `app/modules/analytics/application/services.py`
- `app/modules/analytics/domain/entities.py`
- `app/modules/analytics/infrastructure/repositories.py`
- `app/modules/analytics/presentation/router.py`
- `app/requirements.txt`
- `app/shared/presentation/api_router.py`

</details>

## 9. Backend moduly
*62 commitov · 1939 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `b90a294` | 2026-09-30 | feat(turnstile): Cloudflare Turnstile captcha on /register |
| `05f747e` | 2026-09-30 | feat(admin): user detail, activity log, and hard delete with full cleanup |
| `e380cae` | 2026-09-30 | security(memberships): prevent tenant admin privilege escalation via role change |
| `ecac8dc` | 2026-09-30 | feat(prediction): expose PredictionService via HTTP + mount metrics router |
| `04f8845` | 2026-09-30 | audit: mark best-effort except blocks, fix unused imports |
| `2fa113e` | 2026-09-30 | feat(companies): contact reveal on company profile |
| `12d018e` | 2026-09-30 | feat(feedback): user feedback widget + admin inbox |
| `99e74e6` | 2026-09-28 | Show discover errors and keep RPO lookup under Render timeout. |
| `aea4042` | 2026-09-28 | Add official RPO company search beside ICO lookup. |
| `5071418` | 2026-09-26 | feat(companies): admin-only subscription tier endpoint (PATCH /companies/{id}/subscription-tier) |
| `adf3b97` | 2026-09-26 | feat(companies): expose subscriptionTier in API responses |
| `60fe77b` | 2026-09-26 | feat(entitlements): company tier service + DB-backed prediction gate |
| `8b8d954` | 2026-09-26 | feat(companies): add subscription_tier (free/pro/ai) column |
| `1118897` | 2026-09-26 | feat(matching): daily job + email templates + APScheduler |
| `04499cc` | 2026-09-25 | Phase 5: wire prediction explanation into enrichment |
| `bb85098` | 2026-09-23 | Phase 3: gate prediction with service flag and entitlement env. |
| `46a714d` | 2026-09-23 | Phase 2: normalize rule score to 0..1 for prediction adapter. |
| `334a95a` | 2026-09-23 | Phase 2: make rule scorer callable for adapter.score. |
| `e562eb8` | 2026-09-23 | Phase 2: await adapter.score when attaching prediction. |
| `4974172` | 2026-09-23 | Phase 2: attach prediction_score beside score_company without replacing it. |
| `7a2221d` | 2026-09-23 | Expose prediction status on recommendations without changing rule scores. |
| `858ede1` | 2026-09-23 | Add prediction module and attach disabled metadata to recommendations. |
| `393ab85` | 2026-09-23 | fix: align models and runtime schema behavior |
| `66874bd` | 2026-09-22 | Add user report button and admin report list. |
| `afe4645` | 2026-09-22 | Require valid RPO ICO on company create and split VAT field. |
| `3c2b7c0` | 2026-09-22 | Add official RPO ICO lookup for company verification. |
| `a41e02f` | 2026-09-22 | Block self-inquiries and load admin audit from /admin/all. |
| `48a50ee` | 2026-09-22 | Skip recommendation candidates missing city or accepted materials. |
| `a04c1a8` | 2026-09-22 | Attach actor company to listing_viewed events. |
| `e8d1687` | 2026-09-22 | Score listing interest and list logistics companies instead of OSM. |
| `bb03b6f` | 2026-09-22 | Stop dumping Nominatim HTML on 429 and throttle geocode. |
| `248f645` | 2026-09-22 | Add activity event ingest endpoint for match memory. |
| `e854601` | 2026-09-20 | Mark hazardous EWC prefixes and cover bio waste codes. |
| `a622882` | 2026-09-20 | Add glass textile oil WEEE families and fuzzy EWC edge cases. |
| `e6ba689` | 2026-09-20 | Normalize compact EWC codes like 170405 before family matching. |
| `58b3ef2` | 2026-09-20 | Match EWC codes by longest prefix so metal 17 04 is not construction. |
| `db2affa` | 2026-09-20 | Use EWC-style material families in recommendation scoring. |
| `41ac21c` | 2026-09-20 | Expand material aliases so listings match related accepted types. |
| `4f2f86f` | 2026-09-20 | Drop recommendation candidates whose accepted materials do not match the listing. |
| `cabf1a4` | 2026-09-20 | Do not fail the whole route when OSRM rejects exclude=motorway. |
| `1634186` | 2026-09-20 | Add accepted material types to company model and API schema. |
| `a303377` | 2026-09-20 | Add listing geo fields and material-aware recommendation scoring. |
| `32148f1` | 2026-09-20 | Add read-only listing recommendations for verified buyers. |
| `f86948d` | 2026-09-17 | feat(notifications): notify on inquiry status change and company verification |
| `a5122eb` | 2026-09-16 | fix(companies): use _is_admin helper in status transition (pydantic case) |
| `4509c5e` | 2026-09-16 | feat(companies): admin can list all companies for verification |
| `ac327f7` | 2026-09-14 | Fix: remove duplicate router registration, add UTC to datetimes |
| `8c32fd4` | 2026-09-12 | chore: remove dead legacy service.py placeholders |
| `ff74931` | 2026-09-12 | fix: unify Base declarative for documents and compliance models |
| `7d43531` | 2026-09-12 | fix: unify domain/infrastructure repository signatures |
| `47aa0c3` | 2026-09-01 | refactor: reconcile backend docker and repository wiring |
| `5772689` | 2026-08-26 | Add legacy compatibility bridges for module routers and services |
| `6c823ec` | 2026-08-18 | refactor(api-presentation): align routers, schemas, and responses |
| `336f090` | 2026-08-18 | refactor(api): deprecate legacy routers and tighten app wiring |
| `65c597e` | 2026-08-17 | fix: collection routes syntax; metrics localhost-only; upload file_id auth |
| `a890590` | 2026-08-15 | C2: audit on company status transition |
| `db8c9bd` | 2026-08-09 | Fix: DATABASE_URL env override teraz respektovany aj pre PostgreSQL (nielen SQLite); rozne mapper/repository opravy naprieč modulmi; pridany company status transition endpoint |
| `158094d` | 2026-08-09 | Cleanup: remove tracked .bak-* backup files, add .bak-* to .gitignore |
| `e9dc958` | 2026-08-08 | Fix: zjednotenie DB vrstvy (jeden Base/model pre SQLite dev aj PostgreSQL prod), obnovena .git historia z BROKEN zalohy po strate .git adresara |
| `c7a2164` | 2026-08-08 | Feat: kompletna implementacia zvysnych 6 modulov (inquiries, documents, compliance, notifications, analytics, admin) podla vzoru listings - vsetkych 11 domenovych modulov teraz funkcnych, 28 API ciest celkovo |
| `6a9bdca` | 2026-08-08 | Fix: mount health_router a metrics_router v api_router.py |
| `46fbc54` | 2026-08-07 | Checkpoint 2026-08-06: metrics_router fix, requirements.txt, pred dalsimi zmenami |

<details><summary>Súbory</summary>

**`b90a294`** — feat(turnstile): Cloudflare Turnstile captcha on /register
- `app/modules/users/presentation/router.py`
- `app/modules/users/presentation/schemas.py`
- `apps/web/src/components/auth/turnstile-widget.tsx`
- `apps/web/src/features/auth/components/register-form.tsx`
- `apps/web/src/features/auth/hooks/use-register.ts`

**`05f747e`** — feat(admin): user detail, activity log, and hard delete with full cleanup
- `app/modules/admin/presentation/router.py`
- `app/modules/users/application/services.py`
- `app/modules/users/presentation/router.py`

**`e380cae`** — security(memberships): prevent tenant admin privilege escalation via role change
- `app/modules/company_memberships/presentation/router.py`

**`ecac8dc`** — feat(prediction): expose PredictionService via HTTP + mount metrics router
- `app/modules/prediction/presentation/router.py`
- `app/modules/prediction/presentation/schemas.py`
- `app/shared/presentation/api_router.py`

**`04f8845`** — audit: mark best-effort except blocks, fix unused imports
- `app/modules/agent_platform/presentation/chat_router.py`
- `app/modules/agent_platform/presentation/dependencies.py`
- `app/modules/chat/presentation/router.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/lead_finder/infrastructure/persistence/repositories.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/prediction/infrastructure/database_repository.py`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/app/verify-email/page.tsx`
- `apps/web/src/components/auth/auth-shell.tsx`
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`

**`2fa113e`** — feat(companies): contact reveal on company profile
- `app/modules/companies/presentation/router.py`
- `apps/web/src/app/dashboard/companies/[id]/page.tsx`

**`12d018e`** — feat(feedback): user feedback widget + admin inbox
- `app/modules/events/presentation/router.py`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/components/layout/app-shell.tsx`
- `apps/web/src/features/feedback/components/feedback-widget.tsx`

**`99e74e6`** — Show discover errors and keep RPO lookup under Render timeout.
- `app/modules/companies/application/rpo.py`
- `app/modules/lead_finder/application/services/daily_discover.py`
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`aea4042`** — Add official RPO company search beside ICO lookup.
- `app/modules/companies/application/rpo.py`

**`5071418`** — feat(companies): admin-only subscription tier endpoint (PATCH /companies/{id}/subscription-tier)
- `app/modules/companies/application/services.py`
- `app/modules/companies/presentation/dependencies.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/companies/presentation/schemas.py`
- `app/tests/unit/companies/test_subscription_tier_service.py`

**`adf3b97`** — feat(companies): expose subscriptionTier in API responses
- `app/modules/companies/presentation/mappers.py`
- `app/modules/companies/presentation/schemas.py`

**`60fe77b`** — feat(entitlements): company tier service + DB-backed prediction gate
- `app/modules/companies/application/entitlements.py`
- `app/modules/prediction/application/entitlements.py`
- `app/modules/prediction/application/factory.py`
- `app/tests/unit/companies/test_entitlements.py`

**`8b8d954`** — feat(companies): add subscription_tier (free/pro/ai) column
- `app/modules/companies/application/dto.py`
- `app/modules/companies/application/mappers.py`
- `app/modules/companies/application/services.py`
- `app/modules/companies/domain/entities.py`
- `app/modules/companies/domain/enums.py`
- `app/modules/companies/infrastructure/mappers.py`
- `app/modules/companies/infrastructure/models.py`
- `app/modules/companies/infrastructure/repositories.py`
- `migrations/versions/a1b2c3d4e5f6_add_company_subscription_tier.py`

**`1118897`** — feat(matching): daily job + email templates + APScheduler
- `app/core/config.py`
- `app/main.py`
- `app/modules/recommendations/application/email_templates.py`
- `app/modules/recommendations/application/matching_job.py`
- `app/shared/infrastructure/scheduler.py`
- `requirements.txt`

**`04499cc`** — Phase 5: wire prediction explanation into enrichment
- `app/modules/recommendations/application/prediction_bridge.py`
- `apps/web/src/features/recommendations/components/recommendation-prediction-slot.tsx`

**`bb85098`** — Phase 3: gate prediction with service flag and entitlement env.
- `app/modules/prediction/application/entitlements.py`
- `app/modules/prediction/application/factory.py`
- `app/modules/recommendations/application/prediction_bridge.py`

**`46a714d`** — Phase 2: normalize rule score to 0..1 for prediction adapter.
- `app/modules/recommendations/application/prediction_bridge.py`

**`334a95a`** — Phase 2: make rule scorer callable for adapter.score.
- `app/modules/recommendations/application/prediction_bridge.py`

**`e562eb8`** — Phase 2: await adapter.score when attaching prediction.
- `app/modules/recommendations/application/prediction_bridge.py`

**`4974172`** — Phase 2: attach prediction_score beside score_company without replacing it.
- `app/modules/recommendations/application/prediction_bridge.py`
- `app/modules/recommendations/presentation/schemas.py`

**`7a2221d`** — Expose prediction status on recommendations without changing rule scores.
- `app/modules/recommendations/application/prediction_bridge.py`
- `apps/web/src/features/prediction/components/prediction-status-badge.tsx`

**`858ede1`** — Add prediction module and attach disabled metadata to recommendations.
- `app/modules/prediction/__init__.py`
- `app/modules/prediction/application/__init__.py`
- `app/modules/prediction/application/baseline_config.py`
- `app/modules/prediction/application/baseline_evaluation.py`
- `app/modules/prediction/application/baseline_extractor.py`
- `app/modules/prediction/application/baseline_pipeline_provider.py`
- `app/modules/prediction/application/baseline_predictor.py`
- `app/modules/prediction/application/baseline_provider.py`
- `app/modules/prediction/application/config.py`
- `app/modules/prediction/application/database_extractor.py`
- `app/modules/prediction/application/database_factory.py`
- `app/modules/prediction/application/disabled_provider.py`
- `app/modules/prediction/application/entitlements.py`
- `app/modules/prediction/application/factory.py`
- `app/modules/prediction/application/feature_builder.py`
- `app/modules/prediction/application/features.py`
- `app/modules/prediction/application/model_exports.py`
- `app/modules/prediction/application/null_provider.py`
- `app/modules/prediction/application/pipeline.py`
- `app/modules/prediction/application/providers.py`
- `app/modules/prediction/application/recommendation_adapter.py`
- `app/modules/prediction/application/recommendation_composer.py`
- `app/modules/prediction/application/recommendation_config.py`
- `app/modules/prediction/application/recommendation_exports.py`
- `app/modules/prediction/application/recommendation_provider.py`
- `app/modules/prediction/application/service.py`
- `app/modules/prediction/application/source_inspection.py`
- `app/modules/prediction/application/target_builder.py`
- `app/modules/prediction/domain/__init__.py`
- `app/modules/prediction/domain/entitlement.py`
- … +37 ďalších

**`393ab85`** — fix: align models and runtime schema behavior
- `.env.example`
- `.husky/pre-commit`
- `app/modules/companies/infrastructure/models.py`
- `app/modules/compliance/infrastructure/models.py`
- `app/modules/events/infrastructure/models.py`
- `app/modules/listings/infrastructure/models.py`
- `app/shared/infrastructure/db/register_models.py`
- `apps/web/package.json`
- `migrations/versions/e7f4a1c2b9d0_add_company_vat_identifier.py`
- `pyproject.toml`
- `tests/conftest.py`
- `tests/unit/test_company_services.py`

**`66874bd`** — Add user report button and admin report list.
- `app/modules/events/presentation/router.py`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/features/recommendations/components/report-button.tsx`

**`afe4645`** — Require valid RPO ICO on company create and split VAT field.
- `app/modules/companies/application/dto.py`
- `app/modules/companies/application/mappers.py`
- `app/modules/companies/application/services.py`
- `app/modules/companies/domain/entities.py`
- `app/modules/companies/infrastructure/mappers.py`
- `app/modules/companies/infrastructure/models.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/companies/presentation/schemas.py`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/companies/schemas.ts`

**`3c2b7c0`** — Add official RPO ICO lookup for company verification.
- `app/modules/companies/application/rpo.py`
- `app/modules/companies/presentation/router.py`

**`a41e02f`** — Block self-inquiries and load admin audit from /admin/all.
- `app/modules/inquiries/presentation/router.py`
- `apps/web/src/features/admin/api.ts`

**`48a50ee`** — Skip recommendation candidates missing city or accepted materials.
- `app/modules/recommendations/application/service.py`

**`a04c1a8`** — Attach actor company to listing_viewed events.
- `app/modules/events/presentation/router.py`

**`e8d1687`** — Score listing interest and list logistics companies instead of OSM.
- `app/modules/recommendations/application/scoring.py`
- `app/modules/recommendations/application/service.py`
- `app/modules/recommendations/presentation/router.py`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`

**`bb03b6f`** — Stop dumping Nominatim HTML on 429 and throttle geocode.
- `app/modules/recommendations/application/routing.py`

**`248f645`** — Add activity event ingest endpoint for match memory.
- `app/modules/events/__init__.py`
- `app/modules/events/infrastructure/__init__.py`
- `app/modules/events/infrastructure/models.py`
- `app/modules/events/presentation/__init__.py`
- `app/modules/events/presentation/router.py`
- `app/modules/events/presentation/schemas.py`
- `app/shared/presentation/api_router.py`

**`e854601`** — Mark hazardous EWC prefixes and cover bio waste codes.
- `app/modules/recommendations/application/material_taxonomy.py`
- `tests/test_material_matching.py`

**`a622882`** — Add glass textile oil WEEE families and fuzzy EWC edge cases.
- `app/modules/recommendations/application/material_taxonomy.py`
- `tests/test_material_matching.py`

**`e6ba689`** — Normalize compact EWC codes like 170405 before family matching.
- `app/modules/recommendations/application/material_taxonomy.py`

**`58b3ef2`** — Match EWC codes by longest prefix so metal 17 04 is not construction.
- `app/modules/recommendations/application/material_taxonomy.py`

**`db2affa`** — Use EWC-style material families in recommendation scoring.
- `app/modules/recommendations/application/material_taxonomy.py`
- `app/modules/recommendations/application/scoring.py`

**`41ac21c`** — Expand material aliases so listings match related accepted types.
- `app/modules/recommendations/application/scoring.py`

**`4f2f86f`** — Drop recommendation candidates whose accepted materials do not match the listing.
- `app/modules/recommendations/application/scoring.py`
- `app/modules/recommendations/application/service.py`

**`cabf1a4`** — Do not fail the whole route when OSRM rejects exclude=motorway.
- `app/modules/recommendations/application/routing.py`

**`1634186`** — Add accepted material types to company model and API schema.
- `app/modules/companies/infrastructure/models.py`
- `app/modules/companies/presentation/schemas.py`

**`a303377`** — Add listing geo fields and material-aware recommendation scoring.
- `app/modules/listings/infrastructure/models.py`
- `app/modules/recommendations/application/scoring.py`
- `app/modules/recommendations/application/service.py`

**`32148f1`** — Add read-only listing recommendations for verified buyers.
- `app/modules/recommendations/__init__.py`
- `app/modules/recommendations/application/__init__.py`
- `app/modules/recommendations/application/scoring.py`
- `app/modules/recommendations/application/service.py`
- `app/modules/recommendations/presentation/__init__.py`
- `app/modules/recommendations/presentation/router.py`
- `app/modules/recommendations/presentation/schemas.py`
- `app/shared/presentation/api_router.py`

**`f86948d`** — feat(notifications): notify on inquiry status change and company verification
- `app/modules/companies/presentation/router.py`
- `app/modules/inquiries/presentation/router.py`

**`a5122eb`** — fix(companies): use _is_admin helper in status transition (pydantic case)
- `app/modules/companies/presentation/router.py`

**`4509c5e`** — feat(companies): admin can list all companies for verification
- `app/modules/companies/presentation/router.py`
- `run.sh`

**`ac327f7`** — Fix: remove duplicate router registration, add UTC to datetimes
- `PRODUCTION_PROOF.txt`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/__init__.py`
- `app/core/config.py`
- `app/main.py`
- `app/modules/admin/__init__.py`
- `app/modules/admin/infrastructure/models.py`
- `app/modules/admin/router.py`
- `app/modules/admin/schemas.py`
- `app/modules/analytics/__init__.py`
- `app/modules/analytics/infrastructure/models.py`
- `app/modules/analytics/router.py`
- `app/modules/analytics/schemas.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/compliance/__init__.py`
- `app/modules/compliance/infrastructure/models.py`
- `app/modules/compliance/router.py`
- `app/modules/compliance/schemas.py`
- `app/modules/documents/__init__.py`
- `app/modules/documents/infrastructure/models.py`
- `app/modules/documents/router.py`
- `app/modules/documents/schemas.py`
- `app/modules/inquiries/__init__.py`
- `app/modules/inquiries/application/services.py`
- `app/modules/inquiries/infrastructure/models.py`
- `app/modules/inquiries/router.py`
- `app/modules/inquiries/schemas.py`
- `app/modules/listings/application/services.py`
- … +20 ďalších

**`8c32fd4`** — chore: remove dead legacy service.py placeholders
- `app/modules/admin/service.py`
- `app/modules/analytics/service.py`
- `app/modules/compliance/service.py`
- `app/modules/documents/service.py`
- `app/modules/inquiries/service.py`
- `app/modules/notifications/service.py`

**`ff74931`** — fix: unify Base declarative for documents and compliance models
- `.env.example`
- `app/modules/compliance/infrastructure/models.py`
- `app/modules/documents/infrastructure/models.py`
- `migrations/env.py`

**`7d43531`** — fix: unify domain/infrastructure repository signatures
- `.gitignore`
- `alembic/env.py`
- `app/core/config.py`
- `app/modules/admin/__init__.py`
- `app/modules/admin/application/dto.py`
- `app/modules/admin/application/services.py`
- `app/modules/admin/domain/entities.py`
- `app/modules/admin/domain/repositories.py`
- `app/modules/admin/infrastructure/models.py`
- `app/modules/admin/infrastructure/repositories.py`
- `app/modules/admin/presentation/dependencies.py`
- `app/modules/admin/presentation/mappers.py`
- `app/modules/admin/presentation/router.py`
- `app/modules/admin/schemas.py`
- `app/modules/admin/service.py`
- `app/modules/analytics/__init__.py`
- `app/modules/analytics/application/dto.py`
- `app/modules/analytics/application/services.py`
- `app/modules/analytics/domain/entities.py`
- `app/modules/analytics/domain/enums.py`
- `app/modules/analytics/domain/repositories.py`
- `app/modules/analytics/infrastructure/models.py`
- `app/modules/analytics/infrastructure/repositories.py`
- `app/modules/analytics/presentation/dependencies.py`
- `app/modules/analytics/presentation/mappers.py`
- `app/modules/analytics/presentation/router.py`
- `app/modules/analytics/schemas.py`
- `app/modules/analytics/service.py`
- `app/modules/auth/application/password_reset.py`
- `app/modules/auth/application/services.py`
- … +150 ďalších

**`47aa0c3`** — refactor: reconcile backend docker and repository wiring
- `.dockerignore`
- `app/modules/inquiries/infrastructure/repositories.py`
- `app/shared/infrastructure/db/session.py`
- `docker-compose-app-variant.yml`
- `docker-compose-original-check.yml`
- `docker-compose.monitoring.yml`
- `docker-compose.production.yml`
- `docker-compose.yml`
- `generate_modules.py`

**`5772689`** — Add legacy compatibility bridges for module routers and services
- `app/modules/analytics/__init__.py`
- `app/modules/analytics/models.py`
- `app/modules/analytics/router.py`
- `app/modules/analytics/service.py`
- `app/modules/compliance/__init__.py`
- `app/modules/compliance/models.py`
- `app/modules/compliance/router.py`
- `app/modules/compliance/service.py`
- `app/modules/documents/__init__.py`
- `app/modules/documents/models.py`
- `app/modules/documents/router.py`
- `app/modules/documents/service.py`
- `app/modules/inquiries/__init__.py`
- `app/modules/inquiries/models.py`
- `app/modules/inquiries/router.py`
- `app/modules/inquiries/service.py`
- `app/modules/notifications/__init__.py`
- `app/modules/notifications/models.py`
- `app/modules/notifications/router.py`
- `app/modules/notifications/service.py`

**`6c823ec`** — refactor(api-presentation): align routers, schemas, and responses
- `app/modules/admin/presentation/router.py`
- `app/modules/analytics/presentation/router.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/companies/presentation/schemas.py`
- `app/modules/company_memberships/presentation/router.py`
- `app/modules/company_memberships/presentation/schemas.py`
- `app/modules/compliance/presentation/router.py`
- `app/modules/documents/presentation/router.py`
- `app/modules/documents/presentation/schemas.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/inquiries/presentation/schemas.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/listings/presentation/schemas.py`
- `app/modules/notifications/application/services.py`
- `app/modules/notifications/presentation/router.py`
- `app/modules/notifications/presentation/schemas.py`
- `app/modules/uploads/presentation/router.py`
- `app/modules/uploads/presentation/schemas.py`
- `app/modules/users/presentation/router.py`
- `app/modules/users/presentation/schemas.py`

**`336f090`** — refactor(api): deprecate legacy routers and tighten app wiring
- `.gitignore`
- `app/main.py`
- `app/modules/admin/router.py`
- `app/modules/analytics/router.py`
- `app/modules/compliance/router.py`
- `app/modules/documents/router.py`
- `app/modules/inquiries/router.py`
- `app/modules/notifications/router.py`
- `app/shared/presentation/metrics_router.py`

**`65c597e`** — fix: collection routes syntax; metrics localhost-only; upload file_id auth
- `app/modules/admin/presentation/router.py`
- `app/modules/analytics/presentation/router.py`
- `app/modules/compliance/presentation/router.py`
- `app/modules/documents/presentation/router.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/notifications/presentation/router.py`
- `app/modules/uploads/presentation/router.py`

**`a890590`** — C2: audit on company status transition
- `app/modules/companies/presentation/router.py`

**`db8c9bd`** — Fix: DATABASE_URL env override teraz respektovany aj pre PostgreSQL (nielen SQLite); rozne mapper/repository opravy naprieč modulmi; pridany company status transition endpoint
- `app/modules/admin/infrastructure/repositories.py`
- `app/modules/admin/presentation/mappers.py`
- `app/modules/analytics/infrastructure/repositories.py`
- `app/modules/analytics/presentation/mappers.py`
- `app/modules/companies/application/services.py`
- `app/modules/companies/infrastructure/repositories.py`
- `app/modules/companies/presentation/dependencies.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/companies/presentation/schemas.py`
- `app/modules/compliance/infrastructure/repositories.py`
- `app/modules/compliance/presentation/mappers.py`
- `app/modules/documents/infrastructure/repositories.py`
- `app/modules/documents/presentation/mappers.py`
- `app/modules/inquiries/infrastructure/repositories.py`
- `app/modules/inquiries/presentation/mappers.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/application/dto.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/mappers.py`
- `app/modules/notifications/infrastructure/repositories.py`
- `app/modules/notifications/presentation/mappers.py`
- `app/shared/infrastructure/db/session.py`
- `scripts/grok-audit/create_admin_user.py`
- `scripts/grok-audit/pending_changes_full.diff`
- `scripts/grok-audit/status_check.sh`

**`158094d`** — Cleanup: remove tracked .bak-* backup files, add .bak-* to .gitignore
- `.env.production.bak-20260808-004338`
- `.gitignore`
- `app/Dockerfile.bak-20260808-062720`
- `app/main.py`
- `app/main.py.bak-20260808-221256`
- `app/modules/admin.bak-20260808-114129/__init__.py`
- `app/modules/admin.bak-20260808-114129/application/__init__.py`
- `app/modules/admin.bak-20260808-114129/application/dto.py`
- `app/modules/admin.bak-20260808-114129/application/services.py`
- `app/modules/admin.bak-20260808-114129/domain/__init__.py`
- `app/modules/admin.bak-20260808-114129/domain/entities.py`
- `app/modules/admin.bak-20260808-114129/domain/enums.py`
- `app/modules/admin.bak-20260808-114129/domain/repositories.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/__init__.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/models.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/repositories.py`
- `app/modules/admin.bak-20260808-114129/presentation/__init__.py`
- `app/modules/admin.bak-20260808-114129/presentation/dependencies.py`
- `app/modules/admin.bak-20260808-114129/presentation/mappers.py`
- `app/modules/admin.bak-20260808-114129/presentation/router.py`
- `app/modules/admin.bak-20260808-114129/presentation/schemas.py`
- `app/modules/admin.bak-20260808-114158/__init__.py`
- `app/modules/admin.bak-20260808-114158/application/__init__.py`
- `app/modules/admin.bak-20260808-114158/application/dto.py`
- `app/modules/admin.bak-20260808-114158/application/services.py`
- `app/modules/admin.bak-20260808-114158/domain/__init__.py`
- `app/modules/admin.bak-20260808-114158/domain/entities.py`
- `app/modules/admin.bak-20260808-114158/domain/enums.py`
- `app/modules/admin.bak-20260808-114158/domain/repositories.py`
- `app/modules/admin.bak-20260808-114158/infrastructure/__init__.py`
- … +328 ďalších

**`e9dc958`** — Fix: zjednotenie DB vrstvy (jeden Base/model pre SQLite dev aj PostgreSQL prod), obnovena .git historia z BROKEN zalohy po strate .git adresara
- `add_users.py`
- `app/main.py`
- `app/main.py.bak-20260808-221256`
- `app/modules/admin/domain/service.py`
- `app/modules/analytics/domain/service.py`
- `app/modules/auth/domain/service.py`
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/auth/presentation/router.py.backup`
- `app/modules/companies/domain/service.py`
- `app/modules/companies/presentation/dependencies.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/compliance/domain/service.py`
- `app/modules/documents/domain/service.py`
- `app/modules/documents/presentation/router.py.backup`
- `app/modules/inquiries/domain/service.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/inquiries/presentation/router.py.backup`
- `app/modules/listings/domain/service.py`
- `app/modules/listings/presentation/dependencies.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/notifications/domain/service.py`
- `app/modules/users/domain/service.py`
- `app/modules/users/presentation/dependencies.py`
- `app/modules/users/presentation/router.py`
- `app/requirements.txt`
- `app/shared/config.py`
- `app/shared/database/db.py`
- `app/shared/database/migrations.py`
- `app/shared/infrastructure/db/session.py`
- … +18 ďalších

**`c7a2164`** — Feat: kompletna implementacia zvysnych 6 modulov (inquiries, documents, compliance, notifications, analytics, admin) podla vzoru listings - vsetkych 11 domenovych modulov teraz funkcnych, 28 API ciest celkovo
- `add_users.py`
- `app/main.py`
- `app/main.py.backup`
- `app/modules/admin.bak-20260808-114129/__init__.py`
- `app/modules/admin.bak-20260808-114129/application/__init__.py`
- `app/modules/admin.bak-20260808-114129/application/dto.py`
- `app/modules/admin.bak-20260808-114129/application/services.py`
- `app/modules/admin.bak-20260808-114129/domain/__init__.py`
- `app/modules/admin.bak-20260808-114129/domain/entities.py`
- `app/modules/admin.bak-20260808-114129/domain/enums.py`
- `app/modules/admin.bak-20260808-114129/domain/repositories.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/__init__.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/models.py`
- `app/modules/admin.bak-20260808-114129/infrastructure/repositories.py`
- `app/modules/admin.bak-20260808-114129/presentation/__init__.py`
- `app/modules/admin.bak-20260808-114129/presentation/dependencies.py`
- `app/modules/admin.bak-20260808-114129/presentation/mappers.py`
- `app/modules/admin.bak-20260808-114129/presentation/router.py`
- `app/modules/admin.bak-20260808-114129/presentation/schemas.py`
- `app/modules/admin.bak-20260808-114158/__init__.py`
- `app/modules/admin.bak-20260808-114158/application/__init__.py`
- `app/modules/admin.bak-20260808-114158/application/dto.py`
- `app/modules/admin.bak-20260808-114158/application/services.py`
- `app/modules/admin.bak-20260808-114158/domain/__init__.py`
- `app/modules/admin.bak-20260808-114158/domain/entities.py`
- `app/modules/admin.bak-20260808-114158/domain/enums.py`
- `app/modules/admin.bak-20260808-114158/domain/repositories.py`
- `app/modules/admin.bak-20260808-114158/infrastructure/__init__.py`
- `app/modules/admin.bak-20260808-114158/infrastructure/models.py`
- `app/modules/admin.bak-20260808-114158/infrastructure/repositories.py`
- … +435 ďalších

**`6a9bdca`** — Fix: mount health_router a metrics_router v api_router.py
- `alembic.ini`
- `alembic/env.py`
- `alembic/script.py.mako`
- `alembic/versions/__init__.py`
- `app/core/config.py`
- `app/modules/auth/application/services.py`
- `app/modules/auth/presentation/dependencies.py`
- `app/modules/companies/presentation/schemas.py`
- `app/modules/company_memberships/domain/entities.py`
- `app/modules/company_memberships/presentation/schemas.py`
- `app/modules/users/presentation/schemas.py`
- `app/requirements.txt`
- `app/shared/application/clock.py`
- `app/shared/domain/base.py`
- `app/shared/domain/ports/__init__.py`
- `app/shared/domain/ports/clock.py`
- `app/shared/infrastructure/database.py`
- `app/shared/infrastructure/db/base.py`
- `app/shared/infrastructure/db/session.py`
- `app/shared/infrastructure/security/jwt_exceptions.py`
- `app/shared/infrastructure/security/jwt_revocation_store.py`
- `app/shared/infrastructure/security/jwt_service.py`
- `app/shared/presentation/schemas.py`
- `app/tests/__init__.py`
- `app/tests/integration/__init__.py`
- `app/tests/unit/__init__.py`
- `app/tests/unit/auth/__init__.py`
- `app/tests/unit/companies/__init__.py`
- `app/tests/unit/users/__init__.py`
- `audit_report.json`
- … +10 ďalších

**`46fbc54`** — Checkpoint 2026-08-06: metrics_router fix, requirements.txt, pred dalsimi zmenami
- `.dockerignore`
- `.env.example`
- `.env.production`
- `.github/workflows/ci.yml`
- `.gitignore`
- `Makefile`
- `README.md`
- `app/.dockerignore`
- `app/Dockerfile`
- `app/__init__.py`
- `app/main.py`
- `app/modules/__init__.py`
- `app/modules/admin/__init__.py`
- `app/modules/admin/application/__init__.py`
- `app/modules/admin/application/dto.py`
- `app/modules/admin/application/services.py`
- `app/modules/admin/domain/__init__.py`
- `app/modules/admin/domain/entities.py`
- `app/modules/admin/domain/enums.py`
- `app/modules/admin/domain/repositories.py`
- `app/modules/admin/infrastructure/__init__.py`
- `app/modules/admin/infrastructure/models.py`
- `app/modules/admin/infrastructure/repositories.py`
- `app/modules/admin/presentation/__init__.py`
- `app/modules/admin/presentation/dependencies.py`
- `app/modules/admin/presentation/mappers.py`
- `app/modules/admin/presentation/router.py`
- `app/modules/admin/presentation/schemas.py`
- `app/modules/analytics/__init__.py`
- `app/modules/analytics/application/__init__.py`
- … +450 ďalších

</details>

## 10. Backend core / worker
*11 commitov · 36 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `9bad5c0` | 2026-09-30 | security(register): rate limit + fake domain filter + cleanup job + Turnstile stub |
| `f55d4b3` | 2026-09-30 | fix(exceptions): register ForbiddenDomainError + ConflictDomainError + InvalidTransitionDomainError handlers |
| `103fa81` | 2026-09-30 | security(cors): remove hardcoded dev origins, fix nested-string default |
| `50a329c` | 2026-09-29 | Default CORS to trc-cmep.sk plus local dev. |
| `801755c` | 2026-09-26 | feat(email): Resend Reply-To header (replies to trc-cmep@gmail.com) |
| `6188368` | 2026-09-16 | fix(config): add FRONTEND_URL field so env value is read by pydantic |
| `611e294` | 2026-09-09 | fix(api): bind RedisSettings from REDIS_URL, redact health, safe reset link base |
| `cdd09c3` | 2026-09-05 | fix: update config and readme - 20260905-1253 |
| `018a693` | 2026-08-24 | fix(runtime): termux settings (jwt/redis/rate_limit), memory revocation, /api/v1 mount |
| `1316428` | 2026-08-16 | P0.2: FRONTEND_URL in reset email; hide resetToken outside development |
| `5b41953` | 2026-08-16 | security: require_admin + GET /admin/all; PLATFORM_ADMIN_EMAILS |

<details><summary>Súbory</summary>

**`9bad5c0`** — security(register): rate limit + fake domain filter + cleanup job + Turnstile stub
- `app/core/config.py`
- `app/modules/users/presentation/schemas.py`
- `app/shared/application/email_domain_validator.py`
- `app/shared/infrastructure/scheduler.py`
- `app/shared/infrastructure/turnstile.py`
- `app/shared/presentation/rate_limit_middleware.py`

**`f55d4b3`** — fix(exceptions): register ForbiddenDomainError + ConflictDomainError + InvalidTransitionDomainError handlers
- `app/core/http_exception_handlers.py`

**`103fa81`** — security(cors): remove hardcoded dev origins, fix nested-string default
- `app/core/config.py`
- `app/main.py`

**`50a329c`** — Default CORS to trc-cmep.sk plus local dev.
- `app/core/config.py`

**`801755c`** — feat(email): Resend Reply-To header (replies to trc-cmep@gmail.com)
- `app/core/config.py`
- `app/shared/infrastructure/email/resend_sender.py`

**`6188368`** — fix(config): add FRONTEND_URL field so env value is read by pydantic
- `app/core/config.py`

**`611e294`** — fix(api): bind RedisSettings from REDIS_URL, redact health, safe reset link base
- `app/core/config.py`
- `app/main.py`
- `app/modules/auth/application/password_reset.py`

**`cdd09c3`** — fix: update config and readme - 20260905-1253
- `README.md`
- `app/core/config.py`
- `apps/web/src/lib/config.ts`

**`018a693`** — fix(runtime): termux settings (jwt/redis/rate_limit), memory revocation, /api/v1 mount
- `.gitignore`
- `alembic.ini`
- `alembic/env.py`
- `app/core/config.py`
- `app/main.py`
- `app/shared/infrastructure/db/__init__.py`
- `app/shared/infrastructure/db/base.py`
- `app/shared/infrastructure/db/session.py`
- `app/shared/infrastructure/security/jwt_revocation_store.py`
- `apps/web/src/features/auth/hooks/use-register.ts`
- `apps/web/src/lib/config.ts`
- `requirements.txt`

**`1316428`** — P0.2: FRONTEND_URL in reset email; hide resetToken outside development
- `app/core/config.py`
- `app/modules/auth/application/password_reset.py`

**`5b41953`** — security: require_admin + GET /admin/all; PLATFORM_ADMIN_EMAILS
- `app/core/config.py`
- `app/modules/admin/presentation/router.py`
- `app/shared/presentation/auth_dependencies.py`

</details>

## 11. Admin UI
*20 commitov · 25 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `b05a91c` | 2026-10-05 | fix(web): wire auto-approve & auto-send-batch buttons into toolbar |
| `bc6cedb` | 2026-10-02 | fix(admin-ui): restore lead-outreach page structure |
| `0a37b23` | 2026-10-02 | Fix lead outreach dashboard UI |
| `86e621f` | 2026-10-02 | Fix lead outreach JSX structure |
| `a7c2bdc` | 2026-10-02 | Fix lead outreach page JSX |
| `f4d324f` | 2026-09-30 | refactor(admin-ui): unify admin pages with shared layout and constants |
| `ad6db80` | 2026-09-30 | feat(lead-outreach): batch send, checkboxes, auto-select with valid email |
| `7974806` | 2026-09-30 | refactor(lead-outreach): simplify UI, collapsible sections, remove duplication |
| `299cfb3` | 2026-09-30 | feat(web): pending outreach section (AI-ready emails) |
| `cce4e67` | 2026-09-30 | fix(web): admin StatCard label - remove string quotes around t() call |
| `00bc20a` | 2026-09-30 | feat(web): AI Control admin page |
| `1fa30a1` | 2026-09-29 | Wire CSV box to existing draft-batch outreach endpoint. |
| `9afb93c` | 2026-09-29 | Add CSV import box for batch outreach without touching reason field. |
| `b20c621` | 2026-09-29 | Draft outreach email automatically when a found company is selected. |
| `922d9c5` | 2026-09-26 | feat(admin): add batch outreach link to lead-outreach page |
| `138e343` | 2026-09-26 | feat(admin): batch outreach UI (paste list, generate drafts, send selected) |
| `39c2534` | 2026-09-26 | feat(admin): lead outreach UI (draft + send one email at a time) |
| `bb598e1` | 2026-09-20 | Fix admin recommendations import path so the web build can pass. |
| `34ff7be` | 2026-09-19 | feat admin: audit history table with dark gold styling |
| `7439607` | 2026-09-16 | chore: single platform admin email |

<details><summary>Súbory</summary>

**`b05a91c`** — fix(web): wire auto-approve & auto-send-batch buttons into toolbar
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`bc6cedb`** — fix(admin-ui): restore lead-outreach page structure
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`0a37b23`** — Fix lead outreach dashboard UI
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`86e621f`** — Fix lead outreach JSX structure
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`a7c2bdc`** — Fix lead outreach page JSX
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`f4d324f`** — refactor(admin-ui): unify admin pages with shared layout and constants
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`
- `apps/web/src/app/dashboard/admin/users/[id]/page.tsx`

**`ad6db80`** — feat(lead-outreach): batch send, checkboxes, auto-select with valid email
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`7974806`** — refactor(lead-outreach): simplify UI, collapsible sections, remove duplication
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`299cfb3`** — feat(web): pending outreach section (AI-ready emails)
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`cce4e67`** — fix(web): admin StatCard label - remove string quotes around t() call
- `apps/web/src/app/dashboard/admin/page.tsx`

**`00bc20a`** — feat(web): AI Control admin page
- `apps/web/src/app/dashboard/admin/ai-control/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`

**`1fa30a1`** — Wire CSV box to existing draft-batch outreach endpoint.
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`9afb93c`** — Add CSV import box for batch outreach without touching reason field.
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`b20c621`** — Draft outreach email automatically when a found company is selected.
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`922d9c5`** — feat(admin): add batch outreach link to lead-outreach page
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`

**`138e343`** — feat(admin): batch outreach UI (paste list, generate drafts, send selected)
- `apps/web/src/app/dashboard/admin/lead-outreach/batch/page.tsx`

**`39c2534`** — feat(admin): lead outreach UI (draft + send one email at a time)
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`

**`bb598e1`** — Fix admin recommendations import path so the web build can pass.
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`

**`34ff7be`** — feat admin: audit history table with dark gold styling
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/features/admin/components/audit-table.tsx`

**`7439607`** — chore: single platform admin email
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/features/companies/index.ts`

</details>

## 12. Dashboard UI
*38 commitov · 118 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `6bd21ed` | 2026-10-05 | fix(listings): show thumbnail on mobile too (was hidden below sm breakpoint) |
| `51c9520` | 2026-10-05 | feat(uploads): frontend SignedImage + auth-only sign endpoint |
| `556deb1` | 2026-09-30 | ui(chat): messenger layout with sidebar + conversation |
| `0a5e9e6` | 2026-09-30 | i18n(listings): translate listings page |
| `bbdf6aa` | 2026-09-30 | feat(companies): detail profile page at /dashboard/companies/[id] |
| `8bb01f4` | 2026-09-30 | feat(listings): owner-only stats panel on listing detail |
| `cb2c35d` | 2026-09-29 | Default listing route destination to the signed-in company city. |
| `3543804` | 2026-09-26 | debug: listing owner check + fix isOwner to check all memberships |
| `7d982f5` | 2026-09-26 | feat(listings): delete button with confirmation (owner only) |
| `0a59b78` | 2026-09-26 | feat(inquiries): dark theme table + section boxes matching CMEP style |
| `f1295f0` | 2026-09-26 | feat(web): switch Fraunces -> DM Serif Display (headers) |
| `5ddc050` | 2026-09-26 | feat(dashboard): merge welcome+motto into one box + stacked category cards |
| `a52071f` | 2026-09-25 | feat(web): move AI chat widget to AppShell (all dashboard pages) |
| `79a2715` | 2026-09-25 | feat(web): floating AI chat widget on listing detail |
| `9831f05` | 2026-09-25 | Web: refactor web shell + theme tokens; align dashboard pages with AppShell; add missing i18n keys |
| `4190475` | 2026-09-22 | Add inquiries page and dashboard nav link. |
| `e1eb7bc` | 2026-09-22 | Add listing inquiry button on listing detail. |
| `f065bc7` | 2026-09-22 | Record listing_viewed when opening a listing detail. |
| `4a55cb6` | 2026-09-20 | Stack dashboard nav under logo and add CMEP slogan frame. |
| `bbc81b8` | 2026-09-20 | Place chat draft banner under header and sync transport destination. |
| `6440825` | 2026-09-20 | Show recommendation draft on chat and list logistics partners on listing detail. |
| `b7b8885` | 2026-09-19 | feat listings: company verification warning + status badges |
| `b8c1ae6` | 2026-09-19 | feat chat: breadcrumb back to dashboard + chat nav |
| `d0c41e3` | 2026-09-19 | chore: remove backup files and ignore them |
| `6b03982` | 2026-09-19 | feat DashboardFooter na vsetkych dashboard strankach |
| `14692c5` | 2026-09-19 | feat dashboard vacsie pismo + pravne odkazy |
| `ccbe815` | 2026-09-19 | fix landing dashboard dedup sections + uvitanie |
| `cb044a9` | 2026-09-19 | feat web dark gold admin chat listings documents legal pages |
| `44a75a9` | 2026-09-18 | feat dashboard redesign do CMEP TRC stylu |
| `64b7ce8` | 2026-09-17 | fix(web): add missing useUnreadNotifications import |
| `54fd1ba` | 2026-09-16 | feat(web): admin panel button in header (visible only to admins) |
| `3632d61` | 2026-09-16 | fix(web): add missing useCurrentUser import in dashboard |
| `7cf5bf1` | 2026-09-16 | fix(web): header shows logged-in user email, not hardcoded admin |
| `f2d97b0` | 2026-09-14 | fix(web): wire dashboard buttons to routes |
| `2d920c7` | 2026-09-09 | fix(web): compact dashboard sections, drop card chrome |
| `7e88b4b` | 2026-09-09 | fix(web): drop funeral dark overlay; compact notification row |
| `a5c191f` | 2026-09-09 | feat(web): dashboard shell with grant bar and sponsor/ad rails |
| `d1c4f3b` | 2026-08-16 | FE: document file upload fills fileUrl; dashboard section nav menu |

<details><summary>Súbory</summary>

**`6bd21ed`** — fix(listings): show thumbnail on mobile too (was hidden below sm breakpoint)
- `apps/web/src/app/dashboard/listings/page.tsx`

**`51c9520`** — feat(uploads): frontend SignedImage + auth-only sign endpoint
- `app/modules/uploads/presentation/router.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/uploads/api.ts`
- `apps/web/src/features/uploads/components/signed-image.tsx`

**`556deb1`** — ui(chat): messenger layout with sidebar + conversation
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/features/chat/components/chat-shell.tsx`

**`0a5e9e6`** — i18n(listings): translate listings page
- `apps/web/src/app/dashboard/listings/page.tsx`

**`bbdf6aa`** — feat(companies): detail profile page at /dashboard/companies/[id]
- `apps/web/src/app/dashboard/companies/[id]/page.tsx`
- `apps/web/src/app/dashboard/companies/page.tsx`

**`8bb01f4`** — feat(listings): owner-only stats panel on listing detail
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`

**`cb2c35d`** — Default listing route destination to the signed-in company city.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`

**`3543804`** — debug: listing owner check + fix isOwner to check all memberships
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`

**`7d982f5`** — feat(listings): delete button with confirmation (owner only)
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/listings/components/delete-listing-button.tsx`

**`0a59b78`** — feat(inquiries): dark theme table + section boxes matching CMEP style
- `apps/web/src/app/dashboard/inquiries/page.tsx`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`

**`f1295f0`** — feat(web): switch Fraunces -> DM Serif Display (headers)
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/companies/new/page.tsx`
- `apps/web/src/app/dashboard/documents/new/page.tsx`
- `apps/web/src/app/dashboard/listings/new/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/o-nas/page.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/components/auth/auth-shell.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`

**`5ddc050`** — feat(dashboard): merge welcome+motto into one box + stacked category cards
- `apps/web/src/app/dashboard/page.tsx`

**`a52071f`** — feat(web): move AI chat widget to AppShell (all dashboard pages)
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/components/layout/app-shell.tsx`

**`79a2715`** — feat(web): floating AI chat widget on listing detail
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`

**`9831f05`** — Web: refactor web shell + theme tokens; align dashboard pages with AppShell; add missing i18n keys
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/dashboard/companies/page.tsx`
- `apps/web/src/app/dashboard/documents/page.tsx`
- `apps/web/src/app/dashboard/inquiries/page.tsx`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/components/layout/app-shell.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`4190475`** — Add inquiries page and dashboard nav link.
- `apps/web/src/app/dashboard/inquiries/page.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`

**`e1eb7bc`** — Add listing inquiry button on listing detail.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/inquiries/components/listing-inquiry-button.tsx`

**`f065bc7`** — Record listing_viewed when opening a listing detail.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/api.ts`

**`4a55cb6`** — Stack dashboard nav under logo and add CMEP slogan frame.
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`

**`bbc81b8`** — Place chat draft banner under header and sync transport destination.
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`6440825`** — Show recommendation draft on chat and list logistics partners on listing detail.
- `apps/web/src/app/dashboard/chat/page.tsx`

**`b7b8885`** — feat listings: company verification warning + status badges
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`

**`b8c1ae6`** — feat chat: breadcrumb back to dashboard + chat nav
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`

**`d0c41e3`** — chore: remove backup files and ignore them
- `apps/web/src/app/dashboard/chat/[id]/page.tsx.bak2`
- `apps/web/src/app/dashboard/chat/page.tsx.bak2`
- `apps/web/src/components/layout/dashboard-header.tsx.bak2`

**`6b03982`** — feat DashboardFooter na vsetkych dashboard strankach
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/dashboard/companies/new/page.tsx`
- `apps/web/src/app/dashboard/documents/new/page.tsx`
- `apps/web/src/app/dashboard/documents/page.tsx`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/listings/new/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`

**`14692c5`** — feat dashboard vacsie pismo + pravne odkazy
- `apps/web/src/app/dashboard/page.tsx`

**`ccbe815`** — fix landing dashboard dedup sections + uvitanie
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/page.tsx`

**`cb044a9`** — feat web dark gold admin chat listings documents legal pages
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/dashboard/companies/new/page.tsx`
- `apps/web/src/app/dashboard/documents/new/page.tsx`
- `apps/web/src/app/dashboard/documents/page.tsx`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/listings/new/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/o-nas/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`

**`44a75a9`** — feat dashboard redesign do CMEP TRC stylu
- `apps/web/src/app/dashboard/page.tsx`

**`64b7ce8`** — fix(web): add missing useUnreadNotifications import
- `apps/web/src/app/dashboard/page.tsx`

**`54fd1ba`** — feat(web): admin panel button in header (visible only to admins)
- `apps/web/src/app/dashboard/page.tsx`

**`3632d61`** — fix(web): add missing useCurrentUser import in dashboard
- `apps/web/src/app/dashboard/page.tsx`

**`7cf5bf1`** — fix(web): header shows logged-in user email, not hardcoded admin
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`

**`f2d97b0`** — fix(web): wire dashboard buttons to routes
- `apps/web/src/app/dashboard/page.tsx`

**`2d920c7`** — fix(web): compact dashboard sections, drop card chrome
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/components/layout/app-shell.tsx`

**`7e88b4b`** — fix(web): drop funeral dark overlay; compact notification row
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/cmep-dark.css`

**`a5c191f`** — feat(web): dashboard shell with grant bar and sponsor/ad rails
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/components/layout/app-shell.tsx`

**`d1c4f3b`** — FE: document file upload fills fileUrl; dashboard section nav menu
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/documents/components/document-form.tsx`

</details>

## 13. Landing / auth UI
*16 commitov · 36 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `5e49625` | 2026-09-30 | Update CMEP landing page styling |
| `f7a9f05` | 2026-09-30 | i18n(legal): translate license, privacy, terms pages |
| `1aaec89` | 2026-09-30 | i18n(landing): fix remaining hero/now/why titles |
| `24ba357` | 2026-09-30 | i18n(landing): translate full landing page hero + sections + footer |
| `23830c8` | 2026-09-30 | fix(i18n): add useT hook to inner VerifyEmailContent functions\n\n- t() was used inside inner Content functions, not the page function\n- fixes TS2304: Cannot find name 't' |
| `b9dd242` | 2026-09-26 | feat(web): hero box with full text + stacked category cards |
| `d4add85` | 2026-09-26 | test: button text change to verify deploy pipeline |
| `a2b2793` | 2026-09-26 | feat(web): merge hero into single box + category cards stacked vertically |
| `0ee51f8` | 2026-09-25 | fix(web): remove personal address and phone |
| `292ef8d` | 2026-09-19 | feat auth: email verification UI (sent page, verify page, register redirect) |
| `5859eda` | 2026-09-19 | feat landing footer tagline + copyright |
| `92313ed` | 2026-09-19 | feat landing strata + email trc-cmep everywhere + cleanup backups |
| `34d943e` | 2026-09-19 | feat landing hero prave-teraz preco-cmep nove texty |
| `e111d5e` | 2026-09-18 | feat(landing): tmava zlata landing page v CMEP style |
| `6f6df6b` | 2026-09-18 | feat(auth): dark gold login/register UI + password eye toggle |
| `23e53a4` | 2026-09-18 | fix(web): bind useT() in components that call t() |

<details><summary>Súbory</summary>

**`5e49625`** — Update CMEP landing page styling
- `apps/web/src/app/page.tsx`

**`f7a9f05`** — i18n(legal): translate license, privacy, terms pages
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`

**`1aaec89`** — i18n(landing): fix remaining hero/now/why titles
- `apps/web/src/app/page.tsx`

**`24ba357`** — i18n(landing): translate full landing page hero + sections + footer
- `apps/web/src/app/page.tsx`

**`23830c8`** — fix(i18n): add useT hook to inner VerifyEmailContent functions\n\n- t() was used inside inner Content functions, not the page function\n- fixes TS2304: Cannot find name 't'
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/app/verify-email/page.tsx`

**`b9dd242`** — feat(web): hero box with full text + stacked category cards
- `apps/web/src/app/page.tsx`

**`d4add85`** — test: button text change to verify deploy pipeline
- `apps/web/src/app/page.tsx`

**`a2b2793`** — feat(web): merge hero into single box + category cards stacked vertically
- `apps/web/src/app/page.tsx`

**`0ee51f8`** — fix(web): remove personal address and phone
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`

**`292ef8d`** — feat auth: email verification UI (sent page, verify page, register redirect)
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/app/verify-email/page.tsx`
- `apps/web/src/features/auth/components/register-form.tsx`

**`5859eda`** — feat landing footer tagline + copyright
- `apps/web/src/app/page.tsx`

**`92313ed`** — feat landing strata + email trc-cmep everywhere + cleanup backups
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/o-nas/page.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`

**`34d943e`** — feat landing hero prave-teraz preco-cmep nove texty
- `apps/web/src/app/page.tsx`

**`e111d5e`** — feat(landing): tmava zlata landing page v CMEP style
- `apps/web/src/app/page.tsx`

**`6f6df6b`** — feat(auth): dark gold login/register UI + password eye toggle
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/register/page.tsx`
- `apps/web/src/components/auth/auth-shell.tsx`
- `apps/web/src/components/auth/password-input.tsx`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/components/register-form.tsx`

**`23e53a4`** — fix(web): bind useT() in components that call t()
- `apps/web/src/app/forgot-password/page.tsx`
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`

</details>

## 14. Frontend features
*50 commitov · 355 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `c31f6f8` | 2026-10-05 | feat(listings): edit mode + thumbnails in list |
| `506c01c` | 2026-09-30 | ui: unify company form, listing form, chat with gold/dark theme |
| `f353577` | 2026-09-30 | feat(admin-ui): user detail page with activity timeline + delete button |
| `87f0b25` | 2026-09-30 | i18n: extract hardcoded texts across the platform |
| `14a8104` | 2026-09-30 | Revert "i18n: extract all hardcoded texts across the platform\n\n- new sections in sk/en/de/fr/ru.json:\n  tables, admin, legal, recommendations, freight,\n  chatDraftBanner, notifications, companyForm, listingForm,\n  documentForm, chatWidget, aiAssistant, pagination,\n  languageSwitcher\n- all hardcoded Slovak strings replaced with t('key') calls\n- useT hook added to all components that use t()\n- entire platform now translatable via language switcher" |
| `11f1873` | 2026-09-30 | i18n: extract all hardcoded texts across the platform\n\n- new sections in sk/en/de/fr/ru.json:\n  tables, admin, legal, recommendations, freight,\n  chatDraftBanner, notifications, companyForm, listingForm,\n  documentForm, chatWidget, aiAssistant, pagination,\n  languageSwitcher\n- all hardcoded Slovak strings replaced with t('key') calls\n- useT hook added to all components that use t()\n- entire platform now translatable via language switcher |
| `68e84a4` | 2026-09-30 | fix(web): smaller AI chat widget (520x360 -> 440x330)\n\n- panel is now less dominant on the page\n- mobile max-w still applied via calc(100vw-2rem) |
| `18bd502` | 2026-09-30 | feat(web): 2FA UI - two-step login + security settings page |
| `8a4d143` | 2026-09-29 | Hide AI widget composer while minimized. |
| `7b3c6ec` | 2026-09-29 | Add minimize control to floating AI assistant widget. |
| `310093a` | 2026-09-29 | Show route options by vehicle class on listing transport panel. |
| `5d2c928` | 2026-09-29 | Add minimize and reply tone controls to the listing AI assistant. |
| `7ab0042` | 2026-09-26 | feat(agent): persona picker (bystry/drzy/lenivy/op) + strict anti-leak rules |
| `0e9f965` | 2026-09-26 | feat(agent-memory): frontend sends session_id and resets on logout |
| `37c9989` | 2026-09-26 | feat(agent): gate AI chat by company tier (FREE sees upgrade panel) |
| `b274f06` | 2026-09-26 | feat(admin): subscription tiers panel (FREE/PRO/AI) on admin dashboard |
| `c45598d` | 2026-09-25 | feat(web): AI assistant panel on listing detail + type fixes |
| `cc4909b` | 2026-09-25 | Phase 5: attach prediction explanation beside rule score. |
| `3bad4ef` | 2026-09-23 | Phase 4: show prediction status states in recommendations panel. |
| `f71bc5d` | 2026-09-23 | Pass prediction status fields through recommendations API types. |
| `58d9ba3` | 2026-09-23 | Show prediction status slot inside recommendations panel. |
| `1f0cdb2` | 2026-09-23 | Add prediction UI slot without rewriting recommendations panel. |
| `d80c6a4` | 2026-09-22 | Pass tax identifier into RPO check on verify. |
| `3ce5f61` | 2026-09-22 | Show RPO ICO check before company verify. |
| `9117534` | 2026-09-22 | Map register name into firstName lastName for users API. |
| `3eb970f` | 2026-09-20 | Allow admins to set accepted material types on a company. |
| `ea2ff12` | 2026-09-20 | Fix transport panel type error so Next production build can pass. |
| `115c26b` | 2026-09-20 | Wrap chat draft banner in Suspense so Next production build can pass. |
| `961a7e1` | 2026-09-20 | Auto-calculate OSRM routes with highway option and search nearby carriers. |
| `1fcd8fb` | 2026-09-20 | Add freight carriers panel, transport destination link, and admin recommendations page. |
| `9b1ef3a` | 2026-09-20 | Link buyer city to transport map and add admin recommendations page. |
| `21658af` | 2026-09-20 | Match listing recommendations UI to site theme and add chat draft plus transport estimate. |
| `ce9e399` | 2026-09-20 | Show verified-buyer recommendations on listing detail. |
| `ef65c6f` | 2026-09-19 | feat admin: company actions (verify, reject, suspend, reactivate) with status badges |
| `bc331c6` | 2026-09-19 | feat chat: composer, mark_read, unread badge from chat, detailed thread data |
| `aefedfa` | 2026-09-18 | fix(web): bind useT() in remaining form/table components |
| `ad7452e` | 2026-09-16 | fix(companies): admin check uses env variable (not hardcoded email) |
| `23c37cb` | 2026-09-09 | fix(web): stop alerting JWT tokens after login |
| `034826c` | 2026-09-01 | feat(web): add frontend feature barrel exports and cmep styles |
| `3682b0c` | 2026-08-26 | refactor(web): normalize API client and auth configuration |
| `43637f6` | 2026-08-18 | feat(web-auth): support refresh token flow and Google login |
| `f66af3a` | 2026-08-17 | phase-A: rename paginated schemas; normalize collection routes; protect metrics |
| `25e2130` | 2026-08-16 | P3.1b: listing form file upload fills imageUrl |
| `a909318` | 2026-08-15 | security: tenant filters; compliance list/create + FE table |
| `2a8c377` | 2026-08-15 | FE: add document form; admin audit table on dashboard |
| `a759572` | 2026-08-15 | D: documents list on dashboard + sample API create; C2 company status audit |
| `f5ff866` | 2026-08-14 | C2/C3: audit + notifications on inquiry/publish; FE notifications panel; production checklist |
| `cacea7b` | 2026-08-12 | phase-C: publish only for verified companies; block PUT status=published; FE disable publish |
| `c9f4073` | 2026-08-11 | checkpoint: image_url pole na listings (model/entity/mapper), companies status transition FE, inquiries badge - priebezny stav pred dokoncenim FE prepojenia |
| `9300946` | 2026-08-10 | checkpoint: marketplace MVP – publish, detail, dopyty received/sent, multi-tenant |

<details><summary>Súbory</summary>

**`c31f6f8`** — feat(listings): edit mode + thumbnails in list
- `apps/web/src/app/dashboard/listings/[id]/edit/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/listings/hooks/use-update-listing.ts`
- `apps/web/src/features/listings/index.ts`

**`506c01c`** — ui: unify company form, listing form, chat with gold/dark theme
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`

**`f353577`** — feat(admin-ui): user detail page with activity timeline + delete button
- `apps/web/src/app/dashboard/admin/users/[id]/page.tsx`
- `apps/web/src/features/admin/api.ts`
- `apps/web/src/features/admin/components/admin-users-table.tsx`
- `apps/web/src/features/admin/hooks/use-admin-user.ts`
- `apps/web/src/features/admin/index.ts`
- `apps/web/src/features/admin/types.ts`

**`87f0b25`** — i18n: extract hardcoded texts across the platform
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`
- `apps/web/src/app/dashboard/companies/[id]/page.tsx`
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/features/admin/components/admin-users-table.tsx`
- `apps/web/src/features/admin/components/audit-table.tsx`
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/compliance/components/compliance-table.tsx`
- `apps/web/src/features/documents/components/document-form.tsx`
- `apps/web/src/features/documents/components/documents-table.tsx`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/features/listings/components/marketplace-table.tsx`
- `apps/web/src/features/listings/components/matches-panel.tsx`
- `apps/web/src/features/notifications/components/notifications-panel.tsx`
- `apps/web/src/features/recommendations/components/chat-draft-banner.tsx`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`14a8104`** — Revert "i18n: extract all hardcoded texts across the platform\n\n- new sections in sk/en/de/fr/ru.json:\n  tables, admin, legal, recommendations, freight,\n  chatDraftBanner, notifications, companyForm, listingForm,\n  documentForm, chatWidget, aiAssistant, pagination,\n  languageSwitcher\n- all hardcoded Slovak strings replaced with t('key') calls\n- useT hook added to all components that use t()\n- entire platform now translatable via language switcher"
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`
- `apps/web/src/app/dashboard/companies/[id]/page.tsx`
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/features/admin/components/admin-users-table.tsx`
- `apps/web/src/features/admin/components/audit-table.tsx`
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/compliance/components/compliance-table.tsx`
- `apps/web/src/features/documents/components/document-form.tsx`
- `apps/web/src/features/documents/components/documents-table.tsx`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/features/listings/components/marketplace-table.tsx`
- `apps/web/src/features/listings/components/matches-panel.tsx`
- `apps/web/src/features/notifications/components/notifications-panel.tsx`
- `apps/web/src/features/recommendations/components/chat-draft-banner.tsx`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- … +1 ďalších

**`11f1873`** — i18n: extract all hardcoded texts across the platform\n\n- new sections in sk/en/de/fr/ru.json:\n  tables, admin, legal, recommendations, freight,\n  chatDraftBanner, notifications, companyForm, listingForm,\n  documentForm, chatWidget, aiAssistant, pagination,\n  languageSwitcher\n- all hardcoded Slovak strings replaced with t('key') calls\n- useT hook added to all components that use t()\n- entire platform now translatable via language switcher
- `apps/web/src/app/dashboard/admin/lead-outreach/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`
- `apps/web/src/app/dashboard/companies/[id]/page.tsx`
- `apps/web/src/app/license/page.tsx`
- `apps/web/src/app/privacy/page.tsx`
- `apps/web/src/app/terms/page.tsx`
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/features/admin/components/admin-users-table.tsx`
- `apps/web/src/features/admin/components/audit-table.tsx`
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/compliance/components/compliance-table.tsx`
- `apps/web/src/features/documents/components/document-form.tsx`
- `apps/web/src/features/documents/components/documents-table.tsx`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/features/listings/components/marketplace-table.tsx`
- `apps/web/src/features/listings/components/matches-panel.tsx`
- `apps/web/src/features/notifications/components/notifications-panel.tsx`
- `apps/web/src/features/recommendations/components/chat-draft-banner.tsx`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- … +1 ďalších

**`68e84a4`** — fix(web): smaller AI chat widget (520x360 -> 440x330)\n\n- panel is now less dominant on the page\n- mobile max-w still applied via calc(100vw-2rem)
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`

**`18bd502`** — feat(web): 2FA UI - two-step login + security settings page
- `apps/web/src/app/dashboard/settings/security/page.tsx`
- `apps/web/src/features/auth/api.ts`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/hooks/use-login.ts`
- `apps/web/src/features/auth/types.ts`

**`8a4d143`** — Hide AI widget composer while minimized.
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`

**`7b3c6ec`** — Add minimize control to floating AI assistant widget.
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`

**`310093a`** — Show route options by vehicle class on listing transport panel.
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`5d2c928`** — Add minimize and reply tone controls to the listing AI assistant.
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`

**`7ab0042`** — feat(agent): persona picker (bystry/drzy/lenivy/op) + strict anti-leak rules
- `app/modules/agent_platform/presentation/chat_router.py`
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/agent-platform/components/persona-picker.tsx`
- `apps/web/src/features/agent-platform/lib/persona-store.ts`

**`0e9f965`** — feat(agent-memory): frontend sends session_id and resets on logout
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/agent-platform/lib/session-store.ts`
- `apps/web/src/features/auth/hooks/use-logout.ts`

**`37c9989`** — feat(agent): gate AI chat by company tier (FREE sees upgrade panel)
- `apps/web/src/features/agent-platform/components/ai-chat-widget.tsx`
- `apps/web/src/features/agent-platform/components/ai-upgrade-panel.tsx`
- `apps/web/src/features/companies/hooks/use-my-tier.ts`

**`b274f06`** — feat(admin): subscription tiers panel (FREE/PRO/AI) on admin dashboard
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/features/admin/components/subscription-tiers-panel.tsx`
- `apps/web/src/features/companies/api.ts`
- `apps/web/src/features/companies/types.ts`

**`c45598d`** — feat(web): AI assistant panel on listing detail + type fixes
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/agent-platform/components/ai-assistant-panel.tsx`
- `apps/web/src/features/prediction/types.ts`
- `apps/web/src/features/recommendations/components/report-button.tsx`

**`cc4909b`** — Phase 5: attach prediction explanation beside rule score.
- `app/modules/recommendations/application/prediction_bridge.py`
- `app/modules/recommendations/presentation/schemas.py`
- `apps/web/src/features/prediction/components/prediction-status-badge.tsx`
- `apps/web/src/features/recommendations/api.ts`
- `apps/web/src/features/recommendations/components/recommendation-prediction-slot.tsx`

**`3bad4ef`** — Phase 4: show prediction status states in recommendations panel.
- `apps/web/src/features/prediction/components/prediction-status-badge.tsx`
- `apps/web/src/features/recommendations/api.ts`

**`f71bc5d`** — Pass prediction status fields through recommendations API types.
- `apps/web/src/features/recommendations/api.ts`

**`58d9ba3`** — Show prediction status slot inside recommendations panel.
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`

**`1f0cdb2`** — Add prediction UI slot without rewriting recommendations panel.
- `apps/web/src/features/prediction/index.ts`
- `apps/web/src/features/prediction/types.ts`
- `apps/web/src/features/recommendations/components/recommendation-prediction-slot.tsx`

**`d80c6a4`** — Pass tax identifier into RPO check on verify.
- `apps/web/src/features/companies/components/companies-table.tsx`

**`3ce5f61`** — Show RPO ICO check before company verify.
- `apps/web/src/features/companies/api.ts`
- `apps/web/src/features/companies/components/companies-table.tsx`

**`9117534`** — Map register name into firstName lastName for users API.
- `apps/web/src/features/auth/components/register-form.tsx`
- `apps/web/src/features/auth/hooks/use-register.ts`

**`3eb970f`** — Allow admins to set accepted material types on a company.
- `apps/web/src/features/companies/components/accepted-materials-cell.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`

**`ea2ff12`** — Fix transport panel type error so Next production build can pass.
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`115c26b`** — Wrap chat draft banner in Suspense so Next production build can pass.
- `apps/web/src/features/recommendations/components/chat-draft-banner.tsx`

**`961a7e1`** — Auto-calculate OSRM routes with highway option and search nearby carriers.
- `app/modules/recommendations/application/routing.py`
- `app/modules/recommendations/presentation/router.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`1fcd8fb`** — Add freight carriers panel, transport destination link, and admin recommendations page.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/components/chat-draft-banner.tsx`
- `apps/web/src/features/recommendations/components/freight-panel.tsx`

**`9b1ef3a`** — Link buyer city to transport map and add admin recommendations page.
- `apps/web/src/app/dashboard/admin/recommendations/page.tsx`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`21658af`** — Match listing recommendations UI to site theme and add chat draft plus transport estimate.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/api.ts`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/features/recommendations/components/transport-panel.tsx`

**`ce9e399`** — Show verified-buyer recommendations on listing detail.
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/recommendations/api.ts`
- `apps/web/src/features/recommendations/components/recommendations-panel.tsx`
- `apps/web/src/features/recommendations/hooks/use-recommendations.ts`

**`ef65c6f`** — feat admin: company actions (verify, reject, suspend, reactivate) with status badges
- `apps/web/src/features/companies/components/companies-table.tsx`

**`bc331c6`** — feat chat: composer, mark_read, unread badge from chat, detailed thread data
- `app/modules/chat/application/services.py`
- `app/modules/chat/infrastructure/repositories.py`
- `app/modules/chat/presentation/router.py`
- `app/modules/chat/presentation/schemas.py`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx.bak2`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx.bak2`
- `apps/web/src/components/layout/dashboard-header.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx.bak2`
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/chat/components/thread-list.tsx`
- `apps/web/src/features/chat/hooks/use-chat-queries.ts`
- `apps/web/src/features/chat/hooks/use-mark-read.ts`
- `apps/web/src/features/chat/hooks/use-send-message.ts`
- `apps/web/src/features/chat/index.ts`

**`aefedfa`** — fix(web): bind useT() in remaining form/table components
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`

**`ad7452e`** — fix(companies): admin check uses env variable (not hardcoded email)
- `apps/web/src/features/companies/components/companies-table.tsx`

**`23c37cb`** — fix(web): stop alerting JWT tokens after login
- `apps/web/src/features/auth/components/login-form.tsx`

**`034826c`** — feat(web): add frontend feature barrel exports and cmep styles
- `apps/web/src/cmep-dark.css`
- `apps/web/src/features/admin/index.ts`
- `apps/web/src/features/auth/index.ts`
- `apps/web/src/features/companies/index.ts`
- `apps/web/src/features/compliance/index.ts`
- `apps/web/src/features/documents/index.ts`
- `apps/web/src/features/inquiries/index.ts`
- `apps/web/src/features/listings/index.ts`
- `apps/web/src/features/notifications/index.ts`
- `apps/web/src/features/uploads/index.ts`

**`3682b0c`** — refactor(web): normalize API client and auth configuration
- `apps/web/next.config.mjs`
- `apps/web/package.json`
- `apps/web/src/features/admin/api.ts`
- `apps/web/src/features/auth/api.ts`
- `apps/web/src/features/companies/api.ts`
- `apps/web/src/features/compliance/api.ts`
- `apps/web/src/features/documents/api.ts`
- `apps/web/src/features/inquiries/api.ts`
- `apps/web/src/features/listings/api.ts`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/notifications/api.ts`
- `apps/web/src/features/uploads/api.ts`
- `apps/web/src/lib/api/http.ts`
- `apps/web/src/lib/auth/token-store.ts`
- `apps/web/src/lib/config.ts`

**`43637f6`** — feat(web-auth): support refresh token flow and Google login
- `apps/web/src/features/auth/api.ts`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/hooks/use-login.ts`
- `apps/web/src/features/auth/hooks/use-logout.ts`
- `apps/web/src/lib/auth/token-store.ts`

**`f66af3a`** — phase-A: rename paginated schemas; normalize collection routes; protect metrics
- `.backup-eslint/.eslintrc.json.bak`
- `.backup-eslint/package.json.bak`
- `.backup/pre-admin-user-type.diff`
- `.backup/pre-change.diff`
- `.backup/pre-next-ts-fixes.diff`
- `.env.bak.20260817-115539`
- `.env.bak.20260817-115628`
- `.env.before-newline-fix.20260817-120730`
- `.env.dedup.20260817-120833`
- `.env.finalbak.20260817-131129`
- `.env.fixbak.20260817-115715`
- `app/modules/admin/presentation/router.py`
- `app/modules/admin/presentation/schemas.py`
- `app/modules/analytics/presentation/router.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/compliance/presentation/router.py`
- `app/modules/documents/presentation/router.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/inquiries/presentation/schemas.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/notifications/presentation/router.py`
- `app/shared/infrastructure/security/jwt_revocation_store.py`
- `app/shared/presentation/metrics_router.py`
- `apps/web/.eslintrc.json.legacy`
- `apps/web/.lint-output.txt`
- `apps/web/eslint.config.mjs`
- `apps/web/package-lock.json`
- `apps/web/package.json`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- … +23 ďalších

**`25e2130`** — P3.1b: listing form file upload fills imageUrl
- `apps/web/src/features/listings/components/listing-form.tsx`

**`a909318`** — security: tenant filters; compliance list/create + FE table
- `app/modules/compliance/application/services.py`
- `app/modules/compliance/infrastructure/repositories.py`
- `app/modules/compliance/presentation/router.py`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/compliance/api.ts`
- `apps/web/src/features/compliance/components/compliance-table.tsx`
- `apps/web/src/features/compliance/hooks/use-compliance.ts`
- `apps/web/src/features/compliance/hooks/use-create-compliance.ts`

**`2a8c377`** — FE: add document form; admin audit table on dashboard
- `apps/web/src/app/dashboard/documents/new/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/admin/api.ts`
- `apps/web/src/features/admin/components/audit-table.tsx`
- `apps/web/src/features/admin/hooks/use-audit.ts`
- `apps/web/src/features/documents/components/document-form.tsx`
- `apps/web/src/features/documents/hooks/use-create-document.ts`

**`a759572`** — D: documents list on dashboard + sample API create; C2 company status audit
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/documents/api.ts`
- `apps/web/src/features/documents/components/documents-table.tsx`
- `apps/web/src/features/documents/hooks/use-documents.ts`

**`f5ff866`** — C2/C3: audit + notifications on inquiry/publish; FE notifications panel; production checklist
- `.env.production.example`
- `app/modules/companies/presentation/router.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/presentation/router.py`
- `app/shared/application/side_effects.py`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/notifications/api.ts`
- `apps/web/src/features/notifications/components/notifications-panel.tsx`
- `apps/web/src/features/notifications/hooks/use-notifications.ts`
- `docs/PRODUCTION-CHECKLIST.md`

**`cacea7b`** — phase-C: publish only for verified companies; block PUT status=published; FE disable publish
- `app/modules/listings/application/services.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/router.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/features/listings/api.ts`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/features/listings/schemas.ts`

**`c9f4073`** — checkpoint: image_url pole na listings (model/entity/mapper), companies status transition FE, inquiries badge - priebezny stav pred dokoncenim FE prepojenia
- `app/modules/inquiries/application/services.py`
- `app/modules/inquiries/infrastructure/repositories.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/inquiries/presentation/schemas.py`
- `app/modules/listings/domain/entities.py`
- `app/modules/listings/infrastructure/mappers.py`
- `app/modules/listings/infrastructure/models.py`
- `app/modules/listings/presentation/schemas.py`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/companies/api.ts`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/features/inquiries/api.ts`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`
- `apps/web/src/features/inquiries/components/open-inquiries-badge.tsx`

**`9300946`** — checkpoint: marketplace MVP – publish, detail, dopyty received/sent, multi-tenant
- `app/modules/companies/application/services.py`
- `app/modules/companies/infrastructure/repositories.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/inquiries/application/services.py`
- `app/modules/inquiries/infrastructure/repositories.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/application/services.py`
- `app/modules/listings/infrastructure/repositories.py`
- `app/modules/listings/presentation/router.py`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/auth/api.ts`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/hooks/use-current-user.ts`
- `apps/web/src/features/auth/types.ts`
- `apps/web/src/features/inquiries/api.ts`
- `apps/web/src/features/inquiries/components/inquiries-table.tsx`
- `apps/web/src/features/inquiries/hooks/use-inquiries.ts`
- `apps/web/src/features/listings/api.ts`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/features/listings/components/marketplace-table.tsx`
- `apps/web/src/features/listings/hooks/use-marketplace.ts`

</details>

## 15. Frontend (build, config)
*39 commitov · 252 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `d8c4c33` | 2026-09-30 | i18n(landing): add stepsTitle + contactTitle to all locales |
| `c44f7a9` | 2026-09-30 | fix(turnstile): prevent widget re-render loop |
| `74506db` | 2026-09-30 | security(headers): add security headers to Next.js frontend |
| `330d3eb` | 2026-09-30 | feat(chat): redesign ChatWindow in CMEP theme + full i18n |
| `ed528aa` | 2026-09-30 | i18n: add useT hook to reset-password page and ai-upgrade-panel |
| `ceb3c95` | 2026-09-30 | i18n(context): t() never returns raw dotted key |
| `91f4916` | 2026-09-30 | i18n(legal): add all keys for license, privacy, terms |
| `9b40709` | 2026-09-30 | i18n: translate report button + admin verification hint |
| `c74caca` | 2026-09-30 | i18n(header): translate dashboard nav tabs and header text |
| `f28c920` | 2026-09-30 | i18n(auth): extract hardcoded texts (verify-email, reset-password)\n\n- new 'auth' section in sk/en/de/fr/ru.json (12 keys)\n- verify-email, verify-email-sent, reset-password now use t('auth.*')\n- all auth flow pages are now translatable |
| `84fe9b9` | 2026-09-30 | i18n(landing): extract hardcoded texts to i18n keys\n\n- new 'landing' section in sk/en/de/fr/ru.json (17 keys)\n- page.tsx now uses t('landing.*') for all visible texts\n- replaces hardcoded Slovak strings with i18n keys\n- landing page now fully translatable via locale switcher |
| `fe52ed0` | 2026-09-30 | fix(web): login page - clearer sign-in/sign-up copy\n\n- title: 'Prihláste sa'\n- subtitle: 'Prihláste sa alebo sa zaregistrujte na B2B platforme obehových materiálov.' |
| `408b8c1` | 2026-09-30 | fix(web): cleaner login page copy\n\n- 'Vstup na burzu' -> 'Vstúpte na B2B platformu obehových materiálov'\n- 'E-mailom. Žiadny zelený lístok.' -> professional tone\n- more serious, business-oriented language |
| `648df67` | 2026-09-30 | fix(web): http.ts HttpOptions type; feat(web): AI Control admin page |
| `9ae178a` | 2026-09-26 | fix(web): restore PREČO CMEP block, remove duplicate action buttons |
| `76e6359` | 2026-09-26 | feat(web): new slogan (Menej odpadu. Viac obchodu.) + smaller font size |
| `1c8740e` | 2026-09-26 | feat(web): header nav as horizontal pill buttons + cleaner logo block |
| `239011c` | 2026-09-25 | fix(web): remove standalone output (incompatible with next start) |
| `1833c6e` | 2026-09-25 | fix(web): make husky prepare script non-fatal for CI builds |
| `e9c5642` | 2026-09-22 | Fix PasswordInput syntax that blocked web builds. |
| `7cadd70` | 2026-09-22 | Abort hanging API fetches after 20 seconds. |
| `57f1acc` | 2026-09-22 | Translate leftover login form labels. |
| `fad46c1` | 2026-09-22 | Translate login and register chrome into five languages. |
| `773b783` | 2026-09-20 | Stack add-company add-listing add-document actions on dashboard. |
| `16b43b4` | 2026-09-20 | Translate admin chrome and add company material editor. |
| `bdd257f` | 2026-09-20 | Add companies list with pagination and translate header chrome. |
| `c895bc8` | 2026-09-19 | feat: clean up footer and legal links |
| `d27d954` | 2026-09-19 | chore remove accidentally committed SonicForge |
| `eafec12` | 2026-09-19 | feat dashboard motto + 5 dlazdic materialov + Trhovisko |
| `654e9b3` | 2026-09-19 | feat i18n admin chat listings documents about footer all languages |
| `d1c1065` | 2026-09-18 | feat(brand): nahradenie RC loga za TRC (mark + glow logo) |
| `babe979` | 2026-09-17 | feat(i18n): translate listings and companies tables, remove helper script |
| `a728f3d` | 2026-09-14 | feat(web): i18n SK/EN/RU/FR/DE with language switcher |
| `cd75e7e` | 2026-09-12 | chore: remove AI Docker stack and frontend balast |
| `076f132` | 2026-09-12 | chore: remove skeleton tests and placeholder files |
| `16a857b` | 2026-09-09 | feat(web): full-bleed CMEP/RČ background mark |
| `1bfc7b4` | 2026-09-09 | feat(web): faint RČ emblem watermark on dashboard shell |
| `a24dffb` | 2026-09-08 | release: finalize GHCR image publishing |
| `9f7da29` | 2026-09-01 | refactor(web): consolidate tracked frontend application updates |

<details><summary>Súbory</summary>

**`d8c4c33`** — i18n(landing): add stepsTitle + contactTitle to all locales
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`c44f7a9`** — fix(turnstile): prevent widget re-render loop
- `apps/web/src/components/auth/turnstile-widget.tsx`

**`74506db`** — security(headers): add security headers to Next.js frontend
- `apps/web/next.config.js`

**`330d3eb`** — feat(chat): redesign ChatWindow in CMEP theme + full i18n
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`ed528aa`** — i18n: add useT hook to reset-password page and ai-upgrade-panel
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`
- `apps/web/src/features/agent-platform/components/ai-upgrade-panel.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/prediction/components/prediction-status-badge.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`ceb3c95`** — i18n(context): t() never returns raw dotted key
- `apps/web/src/lib/i18n/context.tsx`

**`91f4916`** — i18n(legal): add all keys for license, privacy, terms
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`9b40709`** — i18n: translate report button + admin verification hint
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/features/recommendations/components/report-button.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`c74caca`** — i18n(header): translate dashboard nav tabs and header text
- `apps/web/src/components/layout/dashboard-header.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`f28c920`** — i18n(auth): extract hardcoded texts (verify-email, reset-password)\n\n- new 'auth' section in sk/en/de/fr/ru.json (12 keys)\n- verify-email, verify-email-sent, reset-password now use t('auth.*')\n- all auth flow pages are now translatable
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/app/verify-email-sent/page.tsx`
- `apps/web/src/app/verify-email/page.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`84fe9b9`** — i18n(landing): extract hardcoded texts to i18n keys\n\n- new 'landing' section in sk/en/de/fr/ru.json (17 keys)\n- page.tsx now uses t('landing.*') for all visible texts\n- replaces hardcoded Slovak strings with i18n keys\n- landing page now fully translatable via locale switcher
- `apps/web/src/app/page.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`fe52ed0`** — fix(web): login page - clearer sign-in/sign-up copy\n\n- title: 'Prihláste sa'\n- subtitle: 'Prihláste sa alebo sa zaregistrujte na B2B platforme obehových materiálov.'
- `apps/web/src/lib/i18n/messages/sk.json`

**`408b8c1`** — fix(web): cleaner login page copy\n\n- 'Vstup na burzu' -> 'Vstúpte na B2B platformu obehových materiálov'\n- 'E-mailom. Žiadny zelený lístok.' -> professional tone\n- more serious, business-oriented language
- `apps/web/src/lib/i18n/messages/sk.json`

**`648df67`** — fix(web): http.ts HttpOptions type; feat(web): AI Control admin page
- `apps/web/src/lib/api/http.ts`

**`9ae178a`** — fix(web): restore PREČO CMEP block, remove duplicate action buttons
- `apps/web/src/components/layout/dashboard-header.tsx`

**`76e6359`** — feat(web): new slogan (Menej odpadu. Viac obchodu.) + smaller font size
- `apps/web/src/app/page.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`1c8740e`** — feat(web): header nav as horizontal pill buttons + cleaner logo block
- `apps/web/src/components/layout/dashboard-header.tsx`

**`239011c`** — fix(web): remove standalone output (incompatible with next start)
- `apps/web/next.config.js`

**`1833c6e`** — fix(web): make husky prepare script non-fatal for CI builds
- `apps/web/package.json`

**`e9c5642`** — Fix PasswordInput syntax that blocked web builds.
- `apps/web/src/components/auth/password-input.tsx`

**`7cadd70`** — Abort hanging API fetches after 20 seconds.
- `apps/web/src/lib/api/http.ts`

**`57f1acc`** — Translate leftover login form labels.
- `apps/web/src/components/auth/password-input.tsx`
- `apps/web/src/features/auth/components/login-form.tsx`

**`fad46c1`** — Translate login and register chrome into five languages.
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/register/page.tsx`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/components/register-form.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`773b783`** — Stack add-company add-listing add-document actions on dashboard.
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`16b43b4`** — Translate admin chrome and add company material editor.
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/features/companies/components/accepted-materials-cell.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`bdd257f`** — Add companies list with pagination and translate header chrome.
- `apps/web/src/app/dashboard/companies/page.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`c895bc8`** — feat: clean up footer and legal links
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/o-nas/page.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`d27d954`** — chore remove accidentally committed SonicForge
- `apps/web/SonicForge/README.md`
- `apps/web/SonicForge/app/build.gradle.kts`
- `apps/web/SonicForge/app/proguard-rules.pro`
- `apps/web/SonicForge/app/src/main/AndroidManifest.xml`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/MainActivity.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/audio/AudioPlayer.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/audio/WavAudio.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/SonicForgeApp.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/SonicForgeViewModel.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/theme/Theme.kt`
- `apps/web/SonicForge/app/src/main/res/drawable/ic_launcher_foreground.xml`
- `apps/web/SonicForge/app/src/main/res/values/strings.xml`
- `apps/web/SonicForge/app/src/main/res/values/themes.xml`
- `apps/web/SonicForge/app/src/test/java/com/sonicforge/audio/WavAudioTest.kt`
- `apps/web/SonicForge/build.gradle.kts`
- `apps/web/SonicForge/gradle.properties`
- `apps/web/SonicForge/settings.gradle.kts`

**`eafec12`** — feat dashboard motto + 5 dlazdic materialov + Trhovisko
- `apps/web/SonicForge/README.md`
- `apps/web/SonicForge/app/build.gradle.kts`
- `apps/web/SonicForge/app/proguard-rules.pro`
- `apps/web/SonicForge/app/src/main/AndroidManifest.xml`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/MainActivity.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/audio/AudioPlayer.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/audio/WavAudio.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/SonicForgeApp.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/SonicForgeViewModel.kt`
- `apps/web/SonicForge/app/src/main/java/com/sonicforge/audio/ui/theme/Theme.kt`
- `apps/web/SonicForge/app/src/main/res/drawable/ic_launcher_foreground.xml`
- `apps/web/SonicForge/app/src/main/res/values/strings.xml`
- `apps/web/SonicForge/app/src/main/res/values/themes.xml`
- `apps/web/SonicForge/app/src/test/java/com/sonicforge/audio/WavAudioTest.kt`
- `apps/web/SonicForge/build.gradle.kts`
- `apps/web/SonicForge/gradle.properties`
- `apps/web/SonicForge/settings.gradle.kts`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/components/layout/dashboard-header.tsx`

**`654e9b3`** — feat i18n admin chat listings documents about footer all languages
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/o-nas/page.tsx`
- `apps/web/src/components/layout/dashboard-footer.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`d1c1065`** — feat(brand): nahradenie RC loga za TRC (mark + glow logo)
- `apps/web/public/trc-logo.jpg`
- `apps/web/public/trc-mark.jpg`
- `apps/web/src/app/page.tsx`
- `apps/web/src/components/auth/auth-shell.tsx`

**`babe979`** — feat(i18n): translate listings and companies tables, remove helper script
- `apps/web/src/app/forgot-password/page.tsx`
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/features/companies/components/company-form.tsx`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/features/listings/components/listings-table.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`
- `tests/unit/test_chat_entities.py`
- `tests/unit/test_chat_sanitize.py`
- `tests/unit/test_company_status_transitions.py`
- `tests/unit/test_listings_entity_validation.py`

**`a728f3d`** — feat(web): i18n SK/EN/RU/FR/DE with language switcher
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/components/language-switcher.tsx`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/lib/i18n/context.tsx`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`

**`cd75e7e`** — chore: remove AI Docker stack and frontend balast
- `apps/web/.eslintrc.json.legacy`
- `apps/web/.lint-output.txt`
- `apps/web/Dockerfile.backup-static-fix-20260909_005524`
- `apps/web/next.config.js.backup-before-api-proxy-20260909_015122`
- `apps/web/next.config.js.backup-before-api-proxy-20260909_015212`
- `apps/web/package.js`
- `apps/web/tsconfig.js`
- `docker/backend/Dockerfile`
- `docker/frontend/Dockerfile`
- `docker/nginx/Dockerfile`
- `docker/nginx/conf.d/cmep.conf`
- `tests/api/test_exception_handlers.py`
- `tests/api/test_metrics.py`
- `tests/unit/test_rate_limiter.py`
- `tests/unit/test_refresh_session_entity.py`

**`076f132`** — chore: remove skeleton tests and placeholder files
- `app/tests/integration/test_auth_api.py`
- `app/tests/integration/test_companies_api.py`
- `app/tests/integration/test_users_api.py`
- `app/tests/unit/auth/test_auth_services.py`
- `app/tests/unit/auth/test_refresh_session_entity.py`
- `app/tests/unit/companies/test_company_entity.py`
- `app/tests/unit/companies/test_company_services.py`
- `app/tests/unit/test_auth.py`
- `app/tests/unit/test_companies.py`
- `app/tests/unit/test_documents.py`
- `app/tests/unit/test_inquiries.py`
- `app/tests/unit/test_listings.py`
- `app/tests/unit/test_uploads.py`
- `app/tests/unit/test_users.py`
- `app/tests/unit/users/test_user_entity.py`
- `app/tests/unit/users/test_user_services.py`
- `apps/web/src/lib/config.ts.backup-before-api-proxy-20260909_015122`
- `apps/web/src/lib/config.ts.backup-before-api-proxy-20260909_015213`

**`16a857b`** — feat(web): full-bleed CMEP/RČ background mark
- `apps/web/public/rc-mark.png`
- `apps/web/src/components/layout/app-shell.tsx`

**`1bfc7b4`** — feat(web): faint RČ emblem watermark on dashboard shell
- `apps/web/public/rc-mark.png`
- `apps/web/src/components/layout/app-shell.tsx`

**`a24dffb`** — release: finalize GHCR image publishing
- `.github/workflows/release.yml`
- `.gitignore`
- `apps/web/.dockerignore`
- `apps/web/Dockerfile`
- `apps/web/next.config.js`
- `apps/web/next.config.mjs`
- `scripts/deploy.sh`

**`9f7da29`** — refactor(web): consolidate tracked frontend application updates
- `apps/web/eslint.config.mjs`
- `apps/web/package-lock.json`
- `apps/web/package.json`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/companies/new/page.tsx`
- `apps/web/src/app/dashboard/documents/new/page.tsx`
- `apps/web/src/app/dashboard/listings/[id]/page.tsx`
- `apps/web/src/app/dashboard/listings/new/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/forgot-password/page.tsx`
- `apps/web/src/app/globals.css`
- `apps/web/src/app/layout.tsx`
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/register/page.tsx`
- `apps/web/src/app/reset-password/page.tsx`
- `apps/web/src/components/providers/app-providers.tsx`
- `apps/web/src/features/auth/components/login-form.tsx`
- `apps/web/src/features/auth/hooks/use-auth-required.ts`
- `apps/web/src/features/listings/components/listing-form.tsx`
- `apps/web/src/lib/api/http.ts`
- `apps/web/src/lib/auth/token-store.ts`
- `apps/web/src/lib/config.ts`

</details>

## 16. Docs & Roadmap
*16 commitov · 23 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `50caab0` | 2026-10-05 | docs: generate PLATFORM_MAP.html (phase → commit → files tree) |
| `22c4ca9` | 2026-10-05 | docs: add session state snapshot for context recovery |
| `b647f4f` | 2026-10-04 | docs: add AI tools roadmap (návrh z CMEP asistenta) |
| `51fa400` | 2026-10-04 | docs: consolidate ROADMAP_CURRENT (fázy 1-10, tech debt, blockers, next steps) |
| `16b0177` | 2026-10-03 | docs: add roadmap snapshot and coverage measurement harness |
| `1b8f7e3` | 2026-10-02 | docs: add FORENSIC_AUDIT_2026-10-02 from full project audit |
| `e5bb2fe` | 2026-10-02 | docs: add BACKLOG.md with signed-url uploads task |
| `ae87f86` | 2026-09-30 | docs(security): close KROK 5 tech debt + add T4 finding |
| `8ee3088` | 2026-09-30 | docs(security): add SECURITY_AUDIT.md from KROK 4 (8 findings fixed) |
| `42eba1f` | 2026-09-26 | docs: add AGENT_CONTEXT.md and ROADMAP.md |
| `2adc4eb` | 2026-09-12 | docs: add production proof report |
| `eac12d7` | 2026-08-16 | P2.2: security headers middleware; checklist P2 progress |
| `e5102ad` | 2026-08-16 | P1.2: DEPLOYMENT.md + env example (domain optional for now) |
| `efccdd2` | 2026-08-16 | P1.1: docker-compose.production.yml + nginx + env example + DEPLOYMENT.md |
| `6776d68` | 2026-08-16 | P0.5: production checklist updated – P0 complete |
| `448e31a` | 2026-08-07 | Checkpoint update: auth review findings, otvorene otazky pred pauzou |

<details><summary>Súbory</summary>

**`50caab0`** — docs: generate PLATFORM_MAP.html (phase → commit → files tree)
- `docs/PLATFORM_MAP.html`

**`22c4ca9`** — docs: add session state snapshot for context recovery
- `docs/SESSION_STATE.md`

**`b647f4f`** — docs: add AI tools roadmap (návrh z CMEP asistenta)
- `docs/ROADMAP_TOOLS.md`

**`51fa400`** — docs: consolidate ROADMAP_CURRENT (fázy 1-10, tech debt, blockers, next steps)
- `docs/ROADMAP_CURRENT.md`

**`16b0177`** — docs: add roadmap snapshot and coverage measurement harness
- `docs/ROADMAP_CURRENT.md`
- `scripts/measure_coverage.py`

**`1b8f7e3`** — docs: add FORENSIC_AUDIT_2026-10-02 from full project audit
- `docs/FORENSIC_AUDIT_2026-10-02.md`

**`e5bb2fe`** — docs: add BACKLOG.md with signed-url uploads task
- `docs/BACKLOG.md`

**`ae87f86`** — docs(security): close KROK 5 tech debt + add T4 finding
- `docs/SECURITY_AUDIT.md`

**`8ee3088`** — docs(security): add SECURITY_AUDIT.md from KROK 4 (8 findings fixed)
- `docs/SECURITY_AUDIT.md`

**`42eba1f`** — docs: add AGENT_CONTEXT.md and ROADMAP.md
- `AGENT_CONTEXT.md`
- `docs/ROADMAP.md`

**`2adc4eb`** — docs: add production proof report
- `PRODUCTION_PROOF.txt`

**`eac12d7`** — P2.2: security headers middleware; checklist P2 progress
- `app/main.py`
- `docs/PRODUCTION-CHECKLIST.md`

**`e5102ad`** — P1.2: DEPLOYMENT.md + env example (domain optional for now)
- `.env.production.example`
- `docs/DEPLOYMENT.md`

**`efccdd2`** — P1.1: docker-compose.production.yml + nginx + env example + DEPLOYMENT.md
- `.env.production.example`
- `docker-compose.production.yml`
- `docker/nginx/conf.d/cmep.conf`
- `docs/DEPLOYMENT.md`

**`6776d68`** — P0.5: production checklist updated – P0 complete
- `docs/PRODUCTION-CHECKLIST.md`

**`448e31a`** — Checkpoint update: auth review findings, otvorene otazky pred pauzou
- `docs/decision-log/checkpoint-20260806.md`

</details>

## 17. Scripts & ops
*27 commitov · 2356 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `dafef58` | 2026-10-05 | fix(backup): production DB backup with validation and offsite upload |
| `b27af13` | 2026-10-03 | chore(scripts): add set -Eeuo pipefail to shell scripts |
| `5122691` | 2026-09-23 | chore: ignore local audit artifacts |
| `6ed46f6` | 2026-09-15 | chore: unify ports on 8001/3001, remove one-shot scripts and reports |
| `1dccd26` | 2026-09-14 | chore: production scaffold — JWT, nginx conf.d, backup job, maintenance scripts |
| `6f9c7e9` | 2026-09-14 | chore: move one-shot cleanup scripts to scripts/maintenance |
| `512d84b` | 2026-09-12 | fix: production-proof.sh — fixed filename and cleaner output |
| `ebb37cd` | 2026-09-12 | chore: production-proof.sh always writes PRODUCTION_PROOF.txt |
| `57c9a5f` | 2026-09-12 | chore: add production proof script |
| `9842a27` | 2026-09-12 | chore: add local CI script (scripts/ci-local.sh) |
| `41323b9` | 2026-09-12 | chore: cleanup scripts/dev — keep only useful scripts |
| `7f616e6` | 2026-09-12 | chore: remove AI-generated audit scripts and forensics |
| `69be017` | 2026-09-09 | checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania) |
| `55bc4d6` | 2026-09-07 | checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania) |
| `3baeef8` | 2026-09-02 | chore: quarantine forensic clutter and stop tracking env secrets |
| `d8c2730` | 2026-09-01 | fix: repair shell syntax in run-check helper |
| `69bbaa4` | 2026-09-01 | chore: add reusable development diagnostics |
| `6187795` | 2026-09-01 | chore: add reusable repository operations scripts |
| `bd2ce50` | 2026-08-16 | P2.1: disable /docs in production; APP_ENV in env example; cron backup note |
| `9870e62` | 2026-08-16 | P0: pre-production checkpoint – SMTP forgot-password works, admin ACL, rate limit, backup scripts |
| `71fd5f3` | 2026-08-16 | fix: backup-db.sh variable expansion |
| `ceb0698` | 2026-08-16 | ops: pg backup script + start-platform.sh; admin ACL |
| `5ccd16d` | 2026-08-10 | checkpoint: firma + ponuka fungujú na dashboarde (draft) |
| `bc12901` | 2026-08-08 | add dependency signal audit script |
| `6457ed8` | 2026-08-08 | Fix: docker-compose context pre api sluzbu zmeneny na koren (opravuje ModuleNotFoundError pre balik 'app'), Dockerfile COPY cesty prepocitane |
| `8bfb6c9` | 2026-08-08 | ROZHODNUTIE: navrat docker-compose.yml na app/+apps-web (funkcny par); backend/frontend archivovane bez mazania (chybajuca API vrstva v backend/, prazdny frontend/) |
| `5d30f47` | 2026-08-07 | Fix: mount health_router a metrics_router v api_router.py |

<details><summary>Súbory</summary>

**`dafef58`** — fix(backup): production DB backup with validation and offsite upload
- `docs/BACKUP.md`
- `scripts/backup/backup-db.sh`
- `scripts/backup/backup-prod.sh`
- `scripts/backup/healthcheck.sh`

**`b27af13`** — chore(scripts): add set -Eeuo pipefail to shell scripts
- `scripts/backup/backup-db.sh`
- `scripts/check_ci_ghost.sh`
- `scripts/check_company_schema.sh`
- `scripts/ci-local.sh`
- `scripts/deploy.sh`
- `scripts/deploy/00_production_readiness_inventory.sh`
- `scripts/deploy/01_runtime_diagnostics.sh`
- `scripts/deploy/02_runtime_gate.sh`
- `scripts/deploy/03_authority_diagnostics.sh`
- `scripts/deploy/04_release_preflight.sh`
- `scripts/deploy/05_registry_authority_check.sh`
- `scripts/deploy/06_set_registry_authority.sh`
- `scripts/deploy/07_docker_daemon_diagnostics.sh`
- `scripts/deploy/08_docker_vm_api_diagnostics.sh`
- `scripts/deploy/09_alpine_access_diagnostics.sh`
- `scripts/forensic-audit.sh`
- `scripts/production-recovery.sh`
- `scripts/run-test-agent.sh`
- `scripts/security/audit.sh`
- `scripts/security/rotate-secrets.sh`
- `scripts/validate-release-identity.sh`

**`5122691`** — chore: ignore local audit artifacts
- `.gitignore`
- `scripts/check_company_schema.sh`

**`6ed46f6`** — chore: unify ports on 8001/3001, remove one-shot scripts and reports
- `.env.example`
- `app/core/config.py`
- `scripts/maintenance/apply_production.sh`
- `scripts/maintenance/apply_production_v2.sh`
- `scripts/maintenance/audit_production.sh`
- `scripts/maintenance/cleanup.sh`
- `scripts/maintenance/diag.sh`
- `scripts/maintenance/finalize_production.sh`
- `scripts/maintenance/finish_cleanup.sh`
- `scripts/maintenance/fix_datetime.sh`
- `scripts/maintenance/fix_duplicates.sh`
- `scripts/maintenance/fix_init.sh`
- `scripts/maintenance/production_questionnaire.sh`

**`1dccd26`** — chore: production scaffold — JWT, nginx conf.d, backup job, maintenance scripts
- `.gitignore`
- `Makefile`
- `scripts/maintenance/apply_production.sh`
- `scripts/maintenance/apply_production_v2.sh`
- `scripts/maintenance/audit_production.sh`
- `scripts/maintenance/finalize_production.sh`
- `scripts/maintenance/production_questionnaire.sh`

**`6f9c7e9`** — chore: move one-shot cleanup scripts to scripts/maintenance
- `scripts/maintenance/cleanup.sh`
- `scripts/maintenance/diag.sh`
- `scripts/maintenance/finish_cleanup.sh`
- `scripts/maintenance/fix_datetime.sh`
- `scripts/maintenance/fix_duplicates.sh`
- `scripts/maintenance/fix_init.sh`

**`512d84b`** — fix: production-proof.sh — fixed filename and cleaner output
- `scripts/production-proof.sh`

**`ebb37cd`** — chore: production-proof.sh always writes PRODUCTION_PROOF.txt
- `scripts/production-proof.sh`

**`57c9a5f`** — chore: add production proof script
- `scripts/production-proof.sh`

**`9842a27`** — chore: add local CI script (scripts/ci-local.sh)
- `scripts/ci-local.sh`

**`41323b9`** — chore: cleanup scripts/dev — keep only useful scripts
- `scripts/dev/backend_test.sh`
- `scripts/dev/check-db-content.sh`
- `scripts/dev/check_backend.sh`
- `scripts/dev/complete_fix.sh`
- `scripts/dev/create_env.sh`
- `scripts/dev/final_setup.sh`
- `scripts/dev/fix_alembic_import.sh`
- `scripts/dev/fix_config_import.sh`
- `scripts/dev/fix_imports.sh`
- `scripts/dev/fix_requirements.sh`
- `scripts/dev/inspect-db-schema.sh`
- `scripts/dev/manual_migrate.sh`
- `scripts/dev/phase0-stabilize-sqlite-light.sh`
- `scripts/dev/phase0-stabilize-termux-pure.sh`
- `scripts/dev/phase0-stabilize-termux.sh`
- `scripts/dev/phase0-stabilize.sh`
- `scripts/dev/phase1_complete_fix.sh`
- `scripts/dev/phase1_setup.sh`
- `scripts/dev/platform_test.sh`
- `scripts/dev/run-check.sh`
- `scripts/dev/run_migrations.sh`
- `scripts/dev/start_backend.sh`
- `scripts/dev/start_backend_clean.sh`
- `scripts/dev/start_backend_fixed.sh`
- `scripts/dev/waste_audit_routes.sh`

**`7f616e6`** — chore: remove AI-generated audit scripts and forensics
- `scripts/fixes/check_imports.py`
- `scripts/fixes/create_health_endpoint.py`
- `scripts/forensics/archive/PHASE2_CONFIGURATION_FORENSICS.sh`
- `scripts/forensics/archive/auto_fix_audit.py`
- `scripts/forensics/archive/clean_tracked_archive_from_git.sh`
- `scripts/forensics/archive/extreme_whole_project_audit.sh`
- `scripts/forensics/archive/finalize_repo_hygiene.sh`
- `scripts/forensics/archive/waste-platform-extreme-audit.sh`
- `scripts/forensics/authority-consistency-final.sh`
- `scripts/forensics/docker-authority-final.sh`
- `scripts/forensics/r60-r65-10step-readonly.sh`
- `scripts/grok-audit/NAZOV_SUBORU.py`
- `scripts/grok-audit/_extract_imports_full.py`
- `scripts/grok-audit/admin_endpoint_source_audit.sh`
- `scripts/grok-audit/admin_endpoint_source_audit_report.txt`
- `scripts/grok-audit/admin_frontend_patch_context.sh`
- `scripts/grok-audit/admin_frontend_patch_context_report.txt`
- `scripts/grok-audit/admin_frontend_patch_prep.sh`
- `scripts/grok-audit/admin_frontend_patch_prep_report.txt`
- `scripts/grok-audit/analyze_waste_platform_filtered.sh`
- `scripts/grok-audit/analyze_waste_platform_filtered_report.txt`
- `scripts/grok-audit/analyze_waste_platform_readonly.sh`
- `scripts/grok-audit/analyze_waste_platform_report.txt`
- `scripts/grok-audit/apply_admin_frontend_patch.sh`
- `scripts/grok-audit/apply_admin_frontend_patch_report.txt`
- `scripts/grok-audit/build_project_manifest.sh`
- `scripts/grok-audit/build_project_manifest_report.txt`
- `scripts/grok-audit/check_backend_runtime_mount.sh`
- `scripts/grok-audit/check_backend_runtime_mount_report.txt`
- `scripts/grok-audit/check_current_dependency_state.sh`
- … +75 ďalších

**`69be017`** — checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania)
- `0.0.0.0:3101`
- `POST_CUTOVER_RELEASE_EVIDENCE_20260908_231334.txt`
- `R60_R65_FULL_RECONCILIATION_20260908_231821.txt`
- `RELEASE_NEXT_STAGE.txt`
- `[::]:3101`
- `app/requirements.txt`
- `app/requirements.txt.backup.20260908_140529`
- `apps/web/Dockerfile`
- `apps/web/Dockerfile.backup-static-fix-20260909_005524`
- `apps/web/next.config.js`
- `apps/web/next.config.js.backup-before-api-proxy-20260909_015122`
- `apps/web/next.config.js.backup-before-api-proxy-20260909_015212`
- `apps/web/src/lib/config.ts`
- `apps/web/src/lib/config.ts.backup-before-api-proxy-20260909_015122`
- `apps/web/src/lib/config.ts.backup-before-api-proxy-20260909_015213`
- `audit/reports/FULL_AUDIT_20260909_020741.txt`
- `cmep-web-pre-cutover-20260908_230357.inspect.json`
- `cmep-web-pre-cutover-20260908_230357.preview.inspect.json`
- `phase1_release_rc_audit.sh`
- `phase2_release_authority_check.sh`
- `phase3_secrets_runtime_audit.sh`
- `reports/authority-diagnostics-20260907-192412.txt`
- `reports/production-readiness-20260907-191720.txt`
- `reports/runtime-diagnostics-20260907-191836.txt`
- `reports/runtime-gate-20260907-192301.txt`
- `scripts/deploy/00_production_readiness_inventory.sh`
- `scripts/deploy/01_runtime_diagnostics.sh`
- `scripts/deploy/02_runtime_gate.sh`
- `scripts/deploy/03_authority_diagnostics.sh`
- `scripts/deploy/04_release_preflight.sh`
- … +26 ďalších

**`55bc4d6`** — checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania)
- `.backup/pre-admin-user-type.diff`
- `.backup/pre-change.diff`
- `.backup/pre-next-ts-fixes.diff`
- `.closure_truth_20260903_114557/all_files.null`
- `.closure_truth_20260903_114557/all_files.txt`
- `.closure_truth_20260903_114557/r1_files.txt`
- `.closure_truth_20260903_114557/report_candidates.txt`
- `.closure_truth_20260903_120101/all_files.null`
- `.closure_truth_20260903_120101/all_files.txt`
- `.closure_truth_20260903_120101/r1_files.txt`
- `.closure_truth_20260903_120101/report_candidates.txt`
- `.closure_truth_20260903_120225/all_files.null`
- `.closure_truth_20260903_120225/all_files.txt`
- `.closure_truth_20260903_120225/r10_all_text.txt`
- `.closure_truth_20260903_120225/r10_files.txt`
- `.closure_truth_20260903_120225/r10_reports.txt`
- `.closure_truth_20260903_120225/r10_signals.txt`
- `.closure_truth_20260903_120225/r10_status_lines.txt`
- `.closure_truth_20260903_120225/r11_all_text.txt`
- `.closure_truth_20260903_120225/r11_files.txt`
- `.closure_truth_20260903_120225/r11_reports.txt`
- `.closure_truth_20260903_120225/r11_signals.txt`
- `.closure_truth_20260903_120225/r11_status_lines.txt`
- `.closure_truth_20260903_120225/r12_all_text.txt`
- `.closure_truth_20260903_120225/r12_files.txt`
- `.closure_truth_20260903_120225/r12_reports.txt`
- `.closure_truth_20260903_120225/r12_signals.txt`
- `.closure_truth_20260903_120225/r12_status_lines.txt`
- `.closure_truth_20260903_120225/r13_all_text.txt`
- `.closure_truth_20260903_120225/r13_files.txt`
- … +361 ďalších

**`3baeef8`** — chore: quarantine forensic clutter and stop tracking env secrets
- `.env.example`
- `.env.production`
- `.gitignore`
- `docs/AUTHORITY.md`
- `scripts/forensics/archive/PHASE2_CONFIGURATION_FORENSICS.sh`
- `scripts/forensics/archive/auto_fix_audit.py`
- `scripts/forensics/archive/clean_tracked_archive_from_git.sh`
- `scripts/forensics/archive/extreme_whole_project_audit.sh`
- `scripts/forensics/archive/finalize_repo_hygiene.sh`
- `scripts/forensics/archive/waste-platform-extreme-audit.sh`
- `waste-platform-finale-hygiene.sh`

**`d8c2730`** — fix: repair shell syntax in run-check helper
- `scripts/dev/run-check.sh`

**`69bbaa4`** — chore: add reusable development diagnostics
- `.gitignore`
- `scripts/dev/check-db-content.sh`
- `scripts/dev/inspect-db-schema.sh`
- `scripts/dev/run-check.sh`

**`6187795`** — chore: add reusable repository operations scripts
- `.gitignore`
- `scripts/ops/check-live-auth-status.sh`
- `scripts/ops/check-postgres-reachability.sh`
- `scripts/ops/classify_git_env_secrets.sh`
- `scripts/ops/create-recyclehub-db.sh`
- `scripts/ops/init-postgres-termux.sh`
- `scripts/ops/seed_database.py`
- `scripts/ops/start-postgres-safe.sh`
- `scripts/ops/verify-db-and-login.sh`

**`bd2ce50`** — P2.1: disable /docs in production; APP_ENV in env example; cron backup note
- `.env.production.example`
- `app/main.py`
- `scripts/backup/cron-example.txt`

**`9870e62`** — P0: pre-production checkpoint – SMTP forgot-password works, admin ACL, rate limit, backup scripts
- `scripts/backup/backup-db.sh`

**`71fd5f3`** — fix: backup-db.sh variable expansion
- `scripts/backup/backup-db.sh`
- `start-platform.sh`

**`ceb0698`** — ops: pg backup script + start-platform.sh; admin ACL
- `scripts/backup/backup-db.sh`
- `start-platform.sh`

**`5ccd16d`** — checkpoint: firma + ponuka fungujú na dashboarde (draft)
- `app/shared/security.py`
- `apps/web/src/app/(protected)/admin/users/page.tsx`
- `apps/web/src/app/(protected)/companies/[companyId]/page.tsx`
- `apps/web/src/app/(protected)/companies/page.tsx`
- `apps/web/src/app/(protected)/dashboard/page.tsx`
- `apps/web/src/app/(protected)/listings/[listingId]/edit/page.tsx`
- `apps/web/src/app/(protected)/listings/[listingId]/page.tsx`
- `apps/web/src/app/(protected)/listings/new/page.tsx`
- `apps/web/src/app/(protected)/listings/page.tsx`
- `apps/web/src/app/(public)/login/page.tsx`
- `apps/web/src/app/(public)/register/page.tsx`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/companies/new/page.tsx`
- `apps/web/src/app/dashboard/listings/new/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/page.tsx`
- `apps/web/src/app/register/page.tsx`
- `apps/web/src/components/layout/app-shell.ts`
- `apps/web/src/components/providers/app-providers.ts`
- `apps/web/src/components/providers/app-providers.tsx`
- `apps/web/src/components/ui/button.ts`
- `apps/web/src/components/ui/button.tsx`
- `apps/web/src/components/ui/data-table.ts`
- `apps/web/src/components/ui/form-field.ts`
- `apps/web/src/components/ui/form-field.tsx`
- `apps/web/src/components/ui/input.ts`
- `apps/web/src/components/ui/input.tsx`
- `apps/web/src/components/ui/page-header.ts`
- `apps/web/src/components/ui/select.ts`
- … +848 ďalších

**`bc12901`** — add dependency signal audit script
- `scripts/grok-audit/check_dependency_signals.sh`

**`6457ed8`** — Fix: docker-compose context pre api sluzbu zmeneny na koren (opravuje ModuleNotFoundError pre balik 'app'), Dockerfile COPY cesty prepocitane
- `app/Dockerfile`
- `app/Dockerfile.bak-20260808-062720`
- `docker-compose.yml`
- `docker-compose.yml.bak-before-context-fix-20260808-062723`
- `docker-compose.yml.bak-wrong-restore-20260808-011754`
- `docker-compose.yml.bak-wrong-restore-20260808-062509`
- `scripts/grok-audit/docker-sim-final/app/Dockerfile`
- `scripts/grok-audit/docker-sim-final/app/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/core/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/core/config.py`
- `scripts/grok-audit/docker-sim-final/app/main.py`
- `scripts/grok-audit/docker-sim-final/app/modules/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/application/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/application/dto.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/application/services.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/domain/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/domain/entities.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/domain/enums.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/domain/repositories.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/infrastructure/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/infrastructure/models.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/infrastructure/repositories.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/presentation/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/presentation/dependencies.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/presentation/mappers.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/presentation/router.py`
- `scripts/grok-audit/docker-sim-final/app/modules/admin/presentation/schemas.py`
- `scripts/grok-audit/docker-sim-final/app/modules/analytics/__init__.py`
- `scripts/grok-audit/docker-sim-final/app/modules/analytics/application/__init__.py`
- … +696 ďalších

**`8bfb6c9`** — ROZHODNUTIE: navrat docker-compose.yml na app/+apps-web (funkcny par); backend/frontend archivovane bez mazania (chybajuca API vrstva v backend/, prazdny frontend/)
- `.env.production`
- `.env.production.bak-20260808-004338`
- `backend/requirements.txt`
- `docker-compose-app-variant.yml`
- `docker-compose-original-check.yml`
- `docker-compose.yml`
- `docker-compose.yml.backend-frontend-variant-20260808-011656`
- `docker-compose.yml.bak-20260808-011012`
- `docker-compose.yml.bak-backend-frontend-20260808-010439`
- `docs/decision-log/checkpoint-20260806.md`
- `scripts/grok-audit/removed_stub_packages_backup/logging-20260808-011448/__init__.py`
- `scripts/grok-audit/removed_stub_packages_backup/metrics-20260808-011448/__init__.py`
- `scripts/grok-audit/removed_stub_packages_backup/security-20260808-011448/__init__.py`

**`5d30f47`** — Fix: mount health_router a metrics_router v api_router.py
- `.env.example`
- `.env.local.template`
- `.gitignore`
- `Makefile`
- `app/core/__init__.py`
- `app/core/config.py`
- `app/main.py`
- `app/modules/auth/domain/entities.py.bak`
- `app/shared/infrastructure/db/session.py`
- `app/shared/infrastructure/security/jwt_service.py`
- `app/shared/presentation/api_router.py`
- `app/shared/presentation/api_router.py.bak-20260807-103634`
- `app/shared/presentation/api_router.py.bak-20260807-161621`
- `approved`
- `archived`
- `completed`
- `compliance_review`
- `docker-compose.monitoring.yml`
- `docker-compose.monitoring.yml.bak-20260807-114506`
- `docker-compose.yml`
- `docker-compose.yml.bak-20260807-114506`
- `docs/reports/phase0_fix_report.md`
- `docs/reports/phase0_report.md`
- `docs/reports/phase1_final_report.md`
- `docs/reports/phase1_fix_report.md`
- `docs/reports/phase1_report.md`
- `fix_report.txt`
- `infra/grafana/provisioning/dashboards/dashboards.yml`
- `infra/grafana/provisioning/datasources/datasources.yml`
- `inquiry_open`
- … +41 ďalších

</details>

## 18. DB migrations
*5 commitov · 17 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `a2086e3` | 2026-09-25 | fix(db): make vat_identifier migration idempotent (skip if column exists) |
| `bce2a78` | 2026-09-12 | chore: final cleanup + local pre-commit hooks |
| `35112f4` | 2026-09-12 | chore: finalize ruff config + format all files |
| `88185cb` | 2026-08-26 | refactor: consolidate backend config and database wiring |
| `793980e` | 2026-08-17 | db: scale indexes on listings/inquiries/documents/notifications |

<details><summary>Súbory</summary>

**`a2086e3`** — fix(db): make vat_identifier migration idempotent (skip if column exists)
- `migrations/versions/e7f4a1c2b9d0_add_company_vat_identifier.py`

**`bce2a78`** — chore: final cleanup + local pre-commit hooks
- `.pre-commit-config.yaml`
- `migrations/env.py`

**`35112f4`** — chore: finalize ruff config + format all files
- `migrations/env.py`
- `ruff.toml`

**`88185cb`** — refactor: consolidate backend config and database wiring
- `.dockerignore`
- `alembic.ini`
- `app/core/config.py`
- `app/core/http_exception_handlers.py`
- `app/main.py`
- `app/shared/infrastructure/database.py`
- `app/shared/infrastructure/db/__init__.py`
- `app/shared/infrastructure/db/session.py`
- `migrations/env.py`
- `migrations/versions/001_initial.py`
- `migrations/versions/1577dceccd9e_initial_schema.py`

**`793980e`** — db: scale indexes on listings/inquiries/documents/notifications
- `migrations/20260817_scale_indexes.sql`

</details>

## 20. CI / CD
*8 commitov · 8 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `c01ab36` | 2026-10-05 | ci: add minimal test workflow to diagnose startup_failure |
| `d218e1d` | 2026-10-05 | ci: add workflow_dispatch trigger |
| `8737b1d` | 2026-09-24 | ci: reclaim ghost BuildFailed workflow path. |
| `7ecf08d` | 2026-09-24 | ci: restore last known-good Release Images workflow. |
| `920e6eb` | 2026-09-24 | ci: restore release.yml web env to syntax that starts on Actions. |
| `ec0dc4e` | 2026-09-12 | ci: proper GitHub Actions workflow |
| `25cfe4e` | 2026-09-12 | ci: add GitHub Actions workflow |
| `c1014ee` | 2026-09-08 | ci: fix release workflow syntax |

<details><summary>Súbory</summary>

**`c01ab36`** — ci: add minimal test workflow to diagnose startup_failure
- `.github/workflows/test-minimal.yml`

**`d218e1d`** — ci: add workflow_dispatch trigger
- `.github/workflows/ci.yml`

**`8737b1d`** — ci: reclaim ghost BuildFailed workflow path.
- `BuildFailed`

**`7ecf08d`** — ci: restore last known-good Release Images workflow.
- `.github/workflows/release.yml`

**`920e6eb`** — ci: restore release.yml web env to syntax that starts on Actions.
- `.github/workflows/release.yml`

**`ec0dc4e`** — ci: proper GitHub Actions workflow
- `.github/workflows/ci.yml`

**`25cfe4e`** — ci: add GitHub Actions workflow
- `.github/workflows/ci.yml`

**`c1014ee`** — ci: fix release workflow syntax
- `.github/workflows/release.yml`

</details>

## 21. Tests
*26 commitov · 153 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `41ea05e` | 2026-10-03 | test(agent-platform): cover groq_gateway HTTP failure modes |
| `10f7a04` | 2026-10-03 | test(agent-platform): cover CmepCompanySearchHandler |
| `5a7d5f4` | 2026-10-03 | test(scheduler): add lifecycle, job registration, and cleanup wrapper tests |
| `b6725bf` | 2026-10-03 | test(turnstile): expand coverage to 100% |
| `9c9f886` | 2026-10-03 | feat(lead-finder): crawl company homepage for contact email |
| `6d22842` | 2026-10-03 | fix(directory-lookup): extract company homepage, not register cross-link |
| `27854af` | 2026-10-02 | fix(outreach): daily limit + write_audit UUID bug |
| `41702aa` | 2026-09-30 | test: fix ty ABC instantiate + FakeScalar.scalars() |
| `a7a293b` | 2026-09-30 | test: add 79 tests for auth, users, rate limits, email, turnstile |
| `2355897` | 2026-09-30 | test: add 63 tests for main, authorization, admin smoke |
| `061366c` | 2026-09-30 | test(rate-limit): update client_ip tests for XFF spoofing fix |
| `8905934` | 2026-09-30 | test(T3): force in-memory Redis backend for tests |
| `ca182a8` | 2026-09-30 | test: add unit tests for 2FA, contact reveal, security, email |
| `53ffe4e` | 2026-09-20 | Cover compact and spaced EWC family matching. |
| `6d4545a` | 2026-09-20 | Cache geocoding and cover distance plus logistics scoring. |
| `1c4f832` | 2026-09-18 | test(companies): add repo tests; skip unfinished auth refresh repo |
| `2679e60` | 2026-09-18 | test: commit all unit tests with coverage, fix lint (E741, SIM105) |
| `6e6f1f9` | 2026-09-14 | test: format listings and company service tests |
| `59aaa48` | 2026-09-14 | test: JWT, companies, listings unit tests and revocation close |
| `b9e9a06` | 2026-09-12 | test: add tests for users mappers |
| `70f829f` | 2026-09-12 | test: add tests for CreateUser, UpdateUser, TransitionUserStatus services |
| `9752955` | 2026-09-12 | chore: remove unused shared/presentation modules |
| `4a63cd9` | 2026-09-12 | test: add coverage for exception handlers, health router, domain exceptions |
| `4c17e45` | 2026-09-12 | test: add unit tests for PasswordService, JwtService, User entity, API health |
| `f55a050` | 2026-09-12 | test: fix testpaths and add SQLite fallback for local tests |
| `c18910f` | 2026-08-26 | test: add backend unit test coverage |

<details><summary>Súbory</summary>

**`41ea05e`** — test(agent-platform): cover groq_gateway HTTP failure modes
- `tests/unit/test_groq_gateway.py`

**`10f7a04`** — test(agent-platform): cover CmepCompanySearchHandler
- `tests/unit/test_cmep_company_search_handler.py`

**`5a7d5f4`** — test(scheduler): add lifecycle, job registration, and cleanup wrapper tests
- `tests/unit/test_scheduler.py`

**`b6725bf`** — test(turnstile): expand coverage to 100%
- `tests/unit/test_turnstile.py`

**`9c9f886`** — feat(lead-finder): crawl company homepage for contact email
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `app/modules/lead_finder/application/services/website_contact_crawler.py`
- `tests/unit/fixtures/crawler/homepage_with_mailto.html`
- `tests/unit/fixtures/crawler/json_ld_contact.html`
- `tests/unit/fixtures/crawler/kontakt_with_obfuscated.html`
- `tests/unit/fixtures/crawler/page_without_email.html`
- `tests/unit/fixtures/crawler/robots_disallow.html`
- `tests/unit/test_website_contact_crawler.py`

**`6d22842`** — fix(directory-lookup): extract company homepage, not register cross-link
- `app/modules/lead_finder/application/services/directory_lookup.py`
- `tests/unit/fixtures/directory/ekol_card.html`
- `tests/unit/fixtures/directory/register_only_card.html`
- `tests/unit/test_directory_lookup.py`

**`27854af`** — fix(outreach): daily limit + write_audit UUID bug
- `app/modules/lead_finder/presentation/router.py`
- `app/shared/application/side_effects.py`
- `app/shared/infrastructure/email/resend_sender.py`
- `tests/unit/test_resend_sender.py`
- `tests/unit/test_side_effects.py`

**`41702aa`** — test: fix ty ABC instantiate + FakeScalar.scalars()
- `tests/unit/test_agent_contracts.py`
- `tests/unit/test_backfill_service.py`
- `tests/unit/test_daily_discover_helpers.py`
- `tests/unit/test_email_finder_filters.py`
- `tests/unit/test_main_cors.py`
- `tests/unit/test_website_finder_filters.py`

**`a7a293b`** — test: add 79 tests for auth, users, rate limits, email, turnstile
- `tests/unit/test_auth_endpoints.py`
- `tests/unit/test_email_domain_validator.py`
- `tests/unit/test_rate_limit_rules.py`
- `tests/unit/test_turnstile.py`
- `tests/unit/test_users_endpoints.py`

**`2355897`** — test: add 63 tests for main, authorization, admin smoke
- `tests/unit/test_admin_smoke.py`
- `tests/unit/test_authorization.py`
- `tests/unit/test_main_smoke.py`

**`061366c`** — test(rate-limit): update client_ip tests for XFF spoofing fix
- `tests/unit/test_rate_limit.py`

**`8905934`** — test(T3): force in-memory Redis backend for tests
- `tests/conftest.py`

**`ca182a8`** — test: add unit tests for 2FA, contact reveal, security, email
- `tests/unit/test_chat_sanitize_reveal.py`
- `tests/unit/test_chat_security_patterns.py`
- `tests/unit/test_email_drafter_gdpr.py`
- `tests/unit/test_email_finder.py`
- `tests/unit/test_two_factor_service.py`

**`53ffe4e`** — Cover compact and spaced EWC family matching.
- `tests/test_material_matching.py`

**`6d4545a`** — Cache geocoding and cover distance plus logistics scoring.
- `app/modules/recommendations/application/routing.py`
- `tests/test_distance_logistics.py`
- `tests/test_material_matching.py`

**`1c4f832`** — test(companies): add repo tests; skip unfinished auth refresh repo
- `app/modules/auth/infrastructure/repositories.py`
- `apps/web/tailwind.config.js`
- `tests/conftest.py`
- `tests/unit/modules/auth/test_refresh_session_repository.py`
- `tests/unit/modules/companies/test_company_repository.py`

**`2679e60`** — test: commit all unit tests with coverage, fix lint (E741, SIM105)
- `.dockerignore`
- `.env.example`
- `.github/workflows/release.yml`
- `app/core/config.py`
- `app/modules/admin/presentation/router.py`
- `app/modules/analytics/application/services.py`
- `app/modules/analytics/domain/repositories.py`
- `app/modules/analytics/infrastructure/repositories.py`
- `app/modules/analytics/presentation/router.py`
- `app/modules/auth/presentation/router.py`
- `app/modules/auth/presentation/schemas.py`
- `app/modules/chat/infrastructure/models.py`
- `app/modules/companies/presentation/router.py`
- `app/modules/company_memberships/presentation/router.py`
- `app/modules/compliance/presentation/router.py`
- `app/modules/inquiries/application/services.py`
- `app/modules/inquiries/presentation/router.py`
- `app/modules/listings/infrastructure/models.py`
- `app/modules/listings/presentation/router.py`
- `app/modules/uploads/presentation/router.py`
- `app/modules/users/presentation/router.py`
- `app/shared/infrastructure/email/sender.py`
- `app/shared/presentation/auth_dependencies.py`
- `app/shared/presentation/authorization.py`
- `apps/web/next.config.js`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/auth/hooks/use-current-user.ts`
- `apps/web/src/features/auth/hooks/use-is-platform-admin.ts`
- `apps/web/src/features/auth/index.ts`
- … +21 ďalších

**`6e6f1f9`** — test: format listings and company service tests
- `tests/unit/test_listings_service.py`

**`59aaa48`** — test: JWT, companies, listings unit tests and revocation close
- `app/modules/admin/presentation/router.py`
- `app/shared/infrastructure/security/jwt_revocation_store.py`
- `apps/web/public/rc-logo.png`
- `apps/web/public/rc-mark-trimmed.png`
- `apps/web/src/app/dashboard/admin/page.tsx`
- `apps/web/src/app/dashboard/documents/page.tsx`
- `apps/web/src/app/dashboard/listings/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/companies/components/companies-table.tsx`
- `apps/web/src/features/listings/api.ts`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- `apps/web/src/lib/i18n/messages/sk.json`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/unit/test_company_services.py`
- `tests/unit/test_company_transition.py`
- `tests/unit/test_jwt_revocation_store.py`
- `tests/unit/test_jwt_service.py`
- `tests/unit/test_listings_service.py`
- `tests/unit/test_shared_primitives.py`

**`b9e9a06`** — test: add tests for users mappers
- `tests/unit/test_user_mappers.py`

**`70f829f`** — test: add tests for CreateUser, UpdateUser, TransitionUserStatus services
- `tests/unit/test_user_services.py`
- `tests/unit/test_user_services_extended.py`

**`9752955`** — chore: remove unused shared/presentation modules
- `app/shared/presentation/exception_handlers.py`
- `app/shared/presentation/health_router.py`
- `app/shared/presentation/schemas.py`
- `tests/api/test_metrics.py`
- `tests/unit/test_health_router.py`

**`4a63cd9`** — test: add coverage for exception handlers, health router, domain exceptions
- `tests/unit/test_domain_exceptions.py`
- `tests/unit/test_exception_handlers.py`
- `tests/unit/test_health_router.py`

**`4c17e45`** — test: add unit tests for PasswordService, JwtService, User entity, API health
- `tests/api/__init__.py`
- `tests/api/test_health.py`
- `tests/unit/__init__.py`
- `tests/unit/test_jwt_service.py`
- `tests/unit/test_passwords.py`
- `tests/unit/test_user_entity.py`

**`f55a050`** — test: fix testpaths and add SQLite fallback for local tests
- `pyproject.toml`
- `tests/conftest.py`

**`c18910f`** — test: add backend unit test coverage
- `app/tests/unit/test_auth.py`
- `app/tests/unit/test_companies.py`
- `app/tests/unit/test_documents.py`
- `app/tests/unit/test_inquiries.py`
- `app/tests/unit/test_listings.py`
- `app/tests/unit/test_uploads.py`
- `app/tests/unit/test_users.py`
- `pytest.ini`

</details>

## 96. Fixes
*9 commitov · 10 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `1e1e986` | 2026-10-02 | fix(deps): add httpx/bs4/lxml/duckduckgo-search to app/requirements |
| `0c23cbf` | 2026-09-30 | fix(rate-limit): chat-message rule was shadowed by chat-create |
| `8026177` | 2026-09-30 | fix(uploads): disable slash redirect at app level |
| `4b43f22` | 2026-09-16 | fix(cors): explicit methods to allow PATCH from browser |
| `a5636c6` | 2026-09-16 | fix: add PyJWT for jwt module import |
| `1193846` | 2026-09-12 | fix: repair Makefile clean-all target |
| `bc2f695` | 2026-09-09 | fix(api): read SMTP from Settings fields; pin passlib/bcrypt; add redis client |
| `a7abb33` | 2026-09-09 | fix(api): stop logging DATABASE_URL on startup |
| `d9e9a08` | 2026-08-16 | fix: rewrite main.py – security headers + production docs gate |

<details><summary>Súbory</summary>

**`1e1e986`** — fix(deps): add httpx/bs4/lxml/duckduckgo-search to app/requirements
- `app/requirements.txt`

**`0c23cbf`** — fix(rate-limit): chat-message rule was shadowed by chat-create
- `app/shared/presentation/rate_limit_middleware.py`

**`8026177`** — fix(uploads): disable slash redirect at app level
- `app/main.py`

**`4b43f22`** — fix(cors): explicit methods to allow PATCH from browser
- `app/main.py`

**`a5636c6`** — fix: add PyJWT for jwt module import
- `requirements.txt`

**`1193846`** — fix: repair Makefile clean-all target
- `Makefile`

**`bc2f695`** — fix(api): read SMTP from Settings fields; pin passlib/bcrypt; add redis client
- `app/requirements.txt`
- `app/shared/infrastructure/email/sender.py`

**`a7abb33`** — fix(api): stop logging DATABASE_URL on startup
- `app/main.py`

**`d9e9a08`** — fix: rewrite main.py – security headers + production docs gate
- `app/main.py`

</details>

## 97. Refactors
*1 commitov · 3 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `9e237b0` | 2026-10-04 | refactor(web): move web_search_gateway to shared infrastructure |

<details><summary>Súbory</summary>

**`9e237b0`** — refactor(web): move web_search_gateway to shared infrastructure
- `app/shared/infrastructure/web/__init__.py`
- `app/shared/infrastructure/web/web_result_normalizer.py`
- `app/shared/infrastructure/web/web_search_gateway.py`

</details>

## 98. Chore
*15 commitov · 565 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `71bb1aa` | 2026-10-05 | chore(web): force render frontend rebuild |
| `db81641` | 2026-10-03 | chore: consolidate .env* patterns in gitignore |
| `724e902` | 2026-10-02 | chore(gitignore): ignore Termux/Atuin artifacts and .bak files |
| `ec53934` | 2026-09-19 | chore gitignore: ignore local output artifacts |
| `c989d4e` | 2026-09-15 | chore: clean repo before deploy — remove debug scripts, add start.sh |
| `f974185` | 2026-09-14 | chore: ignore repair backups and local fix script |
| `5988c11` | 2026-09-12 | chore: gitignore production proof reports |
| `49d36fb` | 2026-09-12 | chore: fix Makefile test paths (app/tests → tests) |
| `5754035` | 2026-09-12 | chore: remove AI-generated backup files |
| `fad5518` | 2026-09-12 | chore: remove orphan src/ directory |
| `a89c571` | 2026-09-12 | chore: remove debug script and duplicate pytest config |
| `d84c562` | 2026-09-12 | chore: remove AI-generated root scripts and phase archives |
| `31d73e4` | 2026-09-09 | chore: drop forensic dump blobs from git (R60 full recon + closure_truth) |
| `9ca7ba3` | 2026-09-01 | chore: remove local archive artifacts from version control |
| `bbee7e1` | 2026-08-08 | Chore: .gitignore pre diagnosticke/simulacne artefakty grok-audit workflow, odstranenie z trackingu |

<details><summary>Súbory</summary>

**`db81641`** — chore: consolidate .env* patterns in gitignore
- `.gitignore`

**`724e902`** — chore(gitignore): ignore Termux/Atuin artifacts and .bak files
- `.gitignore`

**`ec53934`** — chore gitignore: ignore local output artifacts
- `.gitignore`

**`c989d4e`** — chore: clean repo before deploy — remove debug scripts, add start.sh
- `.gitignore`
- `start.sh`

**`f974185`** — chore: ignore repair backups and local fix script
- `.gitignore`

**`5988c11`** — chore: gitignore production proof reports
- `.gitignore`

**`49d36fb`** — chore: fix Makefile test paths (app/tests → tests)
- `Makefile`

**`5754035`** — chore: remove AI-generated backup files
- `alembic/env.py.backup.20260909_062611`
- `app/Dockerfile.backup.20260909_062611`
- `app/requirements.txt.backup.20260908_140529`
- `app/requirements.txt.backup.20260909_062611`

**`fad5518`** — chore: remove orphan src/ directory
- `src/utils/statusLabel.ts`

**`a89c571`** — chore: remove debug script and duplicate pytest config
- `0.0.0.0:3101`
- `2805MikysS446.txt`
- `CMEP-refresh-rotation-forensic-20260907-165436.txt`
- `FINALIZATION_ROADMAP.md`
- `GLOBAL_P0_R1_R65_STATE_20260903_110209.txt`
- `P0_R1_R65_CLOSURE_TRUTH_MAP_20260903_114557.txt`
- `P0_R1_R65_CLOSURE_TRUTH_MAP_20260903_120101.txt`
- `P0_R1_R65_CLOSURE_TRUTH_MAP_20260903_120225.txt`
- `P0_R1_R65_DECISION_MAP_20260903_105724.txt`
- `P0_R1_R65_GLOBAL_TRUTH_MAP_20260903_212053.txt`
- `P0_R1_R65_META_AUDIT_20260903_105537.txt`
- `P0_R54_R65_FRONTIER_ANALYSIS_20260903_110430.txt`
- `POST_CUTOVER_RELEASE_EVIDENCE_20260908_231334.txt`
- `R60_R65_FORENSIC_RECONCILIATION_20260904_203914.txt`
- `RELEASE_NEXT_STAGE.txt`
- `R_REQUIREMENT_COMPLIANCE_20260905_112705.txt`
- `VPS_LOCAL_DISCOVERY_20260904_205626.txt`
- `[::]:3101`
- `all_projects_list.xml`
- `audit_clean_summary_20260905_111829.txt`
- `audit_final_map_20260905_111659.txt`
- `audit_master_map_20260905_112004.txt`
- `audit_master_map_20260905_112033.txt`
- `audit_r_final_resolver_20260905_112346.txt`
- `audit_r_master_20260905_112221.txt`
- `audit_result_summary_20260905_111554.txt`
- `client_state.xml`
- `client_state_prev.xml`
- `cmep-web-pre-cutover-20260908_230357.inspect.json`
- `cmep-web-pre-cutover-20260908_230357.preview.inspect.json`
- … +29 ďalších

**`d84c562`** — chore: remove AI-generated root scripts and phase archives
- `.production-release/README.md`
- `.production-release/ci-handoff/application-image-matrix.example`
- `.production-release/ci-handoff/ci-release-identity-step.example.yml`
- `.production-release/ci-handoff/ci-release-identity.sh.example`
- `.production-release/ci-handoff/compose-release-injection.example.yml`
- `.production-release/ci-handoff/production-release-handoff.example`
- `.production-release/ci-handoff/release-manifest.example`
- `.production-release/ci-handoff/validate-production-release-handoff.sh`
- `.production-release/ci-release-identity.example.yml`
- `.production-release/r60-test/test-r60-release-aware-deploy.sh`
- `.production-release/r61-backup-20260903_104708/ci.yml`
- `.production-release/r61-backup-20260903_104708/deploy.sh`
- `.production-release/r61-backup-20260903_104708/docker-compose.yml`
- `.production-release/r61-backup-20260903_104708/production-recovery.sh`
- `.production-release/release.env.example`
- `GLOBAL_P0_R1_R65_STATE.sh`
- `analyze_p0_r54_r65_frontier.sh`
- `archived-phase-scripts/phase_p0_01_production_source_boundary.sh`
- `archived-phase-scripts/phase_p0_01_r2_production_authority_resolver.sh`
- `archived-phase-scripts/phase_p0_01_r3_authority_discriminator.sh`
- `archived-phase-scripts/phase_p0_01_r4_legacy_ttl_targeted_review.sh`
- `archived-phase-scripts/phase_p0_01_r5_legacy_ttl_authority_closure.sh`
- `archived-phase-scripts/phase_p0_01_r6_forensic_execution_proof.sh`
- `archived-phase-scripts/phase_p0_01_r7_semantic_execution_proof.sh`
- `archived-phase-scripts/phase_p0_01_r8_token_aware_execution_proof.sh`
- `archived-phase-scripts/phase_p0_02_r10_secret_cross_authority_closure.sh`
- `archived-phase-scripts/phase_p0_02_r11_secret_provenance_lineage_closure.sh`
- `archived-phase-scripts/phase_p0_02_r12_secret_provenance_analyzer_hardening.sh`
- `archived-phase-scripts/phase_p0_02_r13_compose_secret_provenance_semantic_proof.sh`
- `archived-phase-scripts/phase_p0_02_r14_secret_provenance_analyzer_consistency_closure.sh`
- … +95 ďalších

**`31d73e4`** — chore: drop forensic dump blobs from git (R60 full recon + closure_truth)
- `.closure_truth_20260903_114557/all_files.null`
- `.closure_truth_20260903_114557/all_files.txt`
- `.closure_truth_20260903_114557/r1_files.txt`
- `.closure_truth_20260903_114557/report_candidates.txt`
- `.closure_truth_20260903_120101/all_files.null`
- `.closure_truth_20260903_120101/all_files.txt`
- `.closure_truth_20260903_120101/r1_files.txt`
- `.closure_truth_20260903_120101/report_candidates.txt`
- `.closure_truth_20260903_120225/all_files.null`
- `.closure_truth_20260903_120225/all_files.txt`
- `.closure_truth_20260903_120225/r10_all_text.txt`
- `.closure_truth_20260903_120225/r10_files.txt`
- `.closure_truth_20260903_120225/r10_reports.txt`
- `.closure_truth_20260903_120225/r10_signals.txt`
- `.closure_truth_20260903_120225/r10_status_lines.txt`
- `.closure_truth_20260903_120225/r11_all_text.txt`
- `.closure_truth_20260903_120225/r11_files.txt`
- `.closure_truth_20260903_120225/r11_reports.txt`
- `.closure_truth_20260903_120225/r11_signals.txt`
- `.closure_truth_20260903_120225/r11_status_lines.txt`
- `.closure_truth_20260903_120225/r12_all_text.txt`
- `.closure_truth_20260903_120225/r12_files.txt`
- `.closure_truth_20260903_120225/r12_reports.txt`
- `.closure_truth_20260903_120225/r12_signals.txt`
- `.closure_truth_20260903_120225/r12_status_lines.txt`
- `.closure_truth_20260903_120225/r13_all_text.txt`
- `.closure_truth_20260903_120225/r13_files.txt`
- `.closure_truth_20260903_120225/r13_reports.txt`
- `.closure_truth_20260903_120225/r13_signals.txt`
- `.closure_truth_20260903_120225/r13_status_lines.txt`
- … +118 ďalších

**`9ca7ba3`** — chore: remove local archive artifacts from version control
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/alembic.ini.backup.20260824-092956`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.dockerignore`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.eslintrc.json.legacy`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.lint-output.txt`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/Dockerfile`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/eslint.config.mjs`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/next-env.d.ts`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/next.config.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package-lock.json`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package.json`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/postcss.config.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/admin/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/companies/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/documents/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/listings/[id]/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/listings/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/forgot-password/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/globals.css`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/layout.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/login/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/register/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/reset-password/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/brand/logo.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/layout/app-shell.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/providers/app-providers.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/ui/button.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/ui/data-table.tsx`
- … +189 ďalších

**`bbee7e1`** — Chore: .gitignore pre diagnosticke/simulacne artefakty grok-audit workflow, odstranenie z trackingu
- `.gitignore`

</details>

## 99. Ostatné
*13 commitov · 276 súborov*

| Hash | Dátum | Popis |
|------|-------|-------|
| `70360fe` | 2026-10-02 | index on main: 1b8f7e3 docs: add FORENSIC_AUDIT_2026-10-02 from full project audit |
| `abde26d` | 2026-09-30 | security(rate-limit): fix X-Forwarded-For spoofing bypass + hide Pydantic input |
| `60bfce6` | 2026-09-30 | security(rate-limit): global middleware + drop unused python-jose |
| `c2b6716` | 2026-09-30 | security(headers): add global SecurityHeadersMiddleware |
| `d958448` | 2026-09-30 | feat(email): transactional emails for inquiry and company events |
| `ff7154c` | 2026-09-25 | Ignore local backup scripts and leftover audit files. |
| `a2f1360` | 2026-09-22 | Allow trc-cmep.sk origin on API CORS. |
| `9060a88` | 2026-09-09 | checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania) |
| `02df337` | 2026-09-01 | checkpoint: priebezne zmeny pred dalsim krokom |
| `48031ef` | 2026-08-18 | first commit |
| `6d86243` | 2026-08-08 | add backend dependency manifest |
| `d113deb` | 2026-09-30 | fix(chat): consistent contact reveal with company profile |
| `fe1cb63` | 2026-09-16 | feat(chat): backend chat module (threads + messages) |

<details><summary>Súbory</summary>

**`abde26d`** — security(rate-limit): fix X-Forwarded-For spoofing bypass + hide Pydantic input
- `app/main.py`
- `app/shared/infrastructure/rate_limit.py`

**`60bfce6`** — security(rate-limit): global middleware + drop unused python-jose
- `app/main.py`
- `app/shared/presentation/rate_limit_middleware.py`
- `requirements.txt`

**`c2b6716`** — security(headers): add global SecurityHeadersMiddleware
- `app/main.py`
- `app/shared/presentation/security_headers.py`

**`d958448`** — feat(email): transactional emails for inquiry and company events
- `app/shared/application/side_effects.py`
- `app/shared/infrastructure/email/transactional.py`

**`ff7154c`** — Ignore local backup scripts and leftover audit files.
- `.gitignore`

**`a2f1360`** — Allow trc-cmep.sk origin on API CORS.
- `app/main.py`

**`9060a88`** — checkpoint: priebezny stav pred restartom sluzieb (117 zmien z upratovania)
- `alembic/env.py`
- `alembic/env.py.backup.20260909_062611`
- `app/Dockerfile`
- `app/Dockerfile.backup.20260909_062611`
- `app/requirements.txt`
- `app/requirements.txt.backup.20260909_062611`
- `audit/reports/FULL_AUDIT_20260909_020741.txt`
- `audit/termux-baseline/quick-audit.sh`
- `audit/termux-baseline/run-audit.sh`
- `deploy_web_production.sh`
- `safe_browser_proxy_cutover.sh`

**`02df337`** — checkpoint: priebezne zmeny pred dalsim krokom
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/alembic.ini.backup.20260824-092956`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.dockerignore`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.eslintrc.json.legacy`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/.lint-output.txt`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/Dockerfile`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/eslint.config.mjs`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/next-env.d.ts`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/next.config.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package-lock.json`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/package.json`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/postcss.config.js`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/admin/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/companies/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/documents/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/listings/[id]/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/listings/new/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/dashboard/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/forgot-password/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/globals.css`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/layout.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/login/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/register/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/app/reset-password/page.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/brand/logo.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/layout/app-shell.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/providers/app-providers.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/ui/button.tsx`
- `__triage_archive/manual-triage-20260901-095819/archived/_local_archive/cleanup_archive-20260901-095016/backups/web.backup.20260824-092935/src/components/ui/data-table.tsx`
- … +189 ďalších

**`48031ef`** — first commit
- `README.md`

**`6d86243`** — add backend dependency manifest
- `app/requirements.txt`

**`d113deb`** — fix(chat): consistent contact reveal with company profile
- `app/modules/chat/application/services.py`

**`fe1cb63`** — feat(chat): backend chat module (threads + messages)
- `app/modules/chat/__init__.py`
- `app/modules/chat/application/__init__.py`
- `app/modules/chat/application/services.py`
- `app/modules/chat/domain/__init__.py`
- `app/modules/chat/domain/entities.py`
- `app/modules/chat/domain/enums.py`
- `app/modules/chat/domain/repositories.py`
- `app/modules/chat/infrastructure/__init__.py`
- `app/modules/chat/infrastructure/mappers.py`
- `app/modules/chat/infrastructure/models.py`
- `app/modules/chat/infrastructure/repositories.py`
- `app/modules/chat/presentation/__init__.py`
- `app/modules/chat/presentation/dependencies.py`
- `app/modules/chat/presentation/router.py`
- `app/modules/chat/presentation/schemas.py`
- `app/shared/infrastructure/db/register_models.py`
- `app/shared/presentation/api_router.py`
- `apps/web/src/app/dashboard/chat/[id]/page.tsx`
- `apps/web/src/app/dashboard/chat/page.tsx`
- `apps/web/src/app/dashboard/page.tsx`
- `apps/web/src/features/chat/api.ts`
- `apps/web/src/features/chat/components/chat-window.tsx`
- `apps/web/src/features/chat/components/thread-list.tsx`
- `apps/web/src/features/chat/hooks/use-threads.ts`
- `apps/web/src/features/chat/index.ts`
- `apps/web/src/features/chat/types.ts`
- `apps/web/src/lib/i18n/messages/de.json`
- `apps/web/src/lib/i18n/messages/en.json`
- `apps/web/src/lib/i18n/messages/fr.json`
- `apps/web/src/lib/i18n/messages/ru.json`
- … +2 ďalších

</details>
