# Forenzný audit CMEP — 2026-10-02

**Audítor:** Atuin AI (session 2026-10-02)
**Režim:** READ-ONLY (žiadny súbor nebol zmenený)
**HEAD v čase auditu:** 3540996
**Branch:** main
**Metóda:** statická analýza (cat, grep, find, git log)

## Prehľad

131 endpointov, 77 test súborov, 18 modulov v `app/modules/`.
40+ nálezov v 12 kategóriách. 2×P0, 4×P1, zvyšok P2/P3.

---

## 1. Mapa systému

### 1.1 Architektúra (modul × vrstva)

| Modul | domain | app | infra | present | Stav |
|---|---|---|---|---|---|
| admin | ✅ | ✅ | ✅ | ✅ | plná |
| agent_platform | ✅ | ✅ | ✅ | ✅ | plná, obrovská |
| analytics | ✅ | ✅ | ✅ | ✅ | plná |
| auth | ✅ | ✅ | ✅ | ✅ | plná |
| chat | ✅ | ✅ | ✅ | ✅ | plná |
| companies | ✅ | ✅ | ✅ | ✅ | plná |
| company_memberships | ✅ | ✅ | ✅ | ✅ | plná |
| compliance | ✅ | ✅ | ✅ | ✅ | plná |
| documents | ✅ | ✅ | ✅ | ✅ | plná |
| events | – | – | ✅ | ✅ | len 2 vrstvy |
| inquiries | ✅ | ✅ | ✅ | ✅ | plná |
| lead_finder | ✅ | ✅ | ✅ | ✅ | plná |
| listings | ✅ | ✅ | ✅ | ✅ | plná |
| notifications | ✅ | ✅ | ✅ | ✅ | plná |
| prediction | ✅ | ✅ | ✅ | ✅ | duplicitné exports |
| recommendations | – | ✅ | – | ✅ | len 2 vrstvy |
| uploads | – | – | – | ✅ | raw FS v routeri |
| users | ✅ | ✅ | ✅ | ✅ | plná |

Nekonzistencie: events, recommendations, uploads nespĺňajú
4-vrstvový model z AGENT_CONTEXT.md.

### 1.2 Tok dát

A) POST /auth/login:
HTTP → SecurityHeaders → RateLimit → CORS → auth router →
in-handler rate limit (10/60 IP, 5/60 email) → LoginService →
user repo → DB → JWT issue → LoginResponse

B) POST /listings:
HTTP → middleware → listings router → require_current_user +
require_company_member → ListingsService → repo → DB →
ListingResponse (201). create NEMÁ write_audit (publish/promote áno).

C) POST /admin/lead-outreach/discover-daily:
HTTP → middleware (žiadne rate limit pravidlo) →
lead_finder router → require_current_user + require_admin →
run_daily_discover → RPO API → WebsiteFinder → AsyncLegalEmailFinder
→ EmailDrafter (Groq) → repo → DB.

### 1.3 Doménový model

User ─┬─ CompanyMembership ─── Company ─┬─ Listing ─── ListingView
      ├─ RefreshSession                ├─ Inquiry
      ├─ User2FA                       ├─ ComplianceRecord
      ├─ ChatThread ── ChatMessage     ├─ Document
      ├─ Notification                  ├─ AnalyticsEvent
      └─ AiConversation ── AiMessage   └─ ActivityEvent

Status enums:
- CompanyStatus: draft → verification_submitted → verified/rejected → suspended/inactive
- ListingsStatus: draft → published → reserved → completed → archived
- InquiryStatus: open → answered → closed
- UserStatus: invited → pending_verification → active → suspended → deactivated
- CompanyMembershipRole: owner/admin/member/compliance_contact/sales_contact/logistics_contact/viewer
- SubscriptionTier: free < pro < ai

FK constraints:
✅ Majú FK: ai_messages, chat_messages, listing_views
❌ NEMAJÚ FK (len holé String/UUID):
   listings.company_id, company_memberships.company_id/user_id,
   inquiries.company_id/listing_id, documents.company_id,
   compliance_records.company_id, notifications.user_id,
   analytics_events.*, activity_events.*, agent_* tabuľky

### 1.4 Integrácie

| Služba | Klient | Timeout | Retry | Fallback |
|---|---|---|---|---|
| RPO | companies/application/rpo.py | 12s/8s | ❌ | ❌ |
| Groq | agent_platform/.../groq_gateway.py | 45s | ❌ | ❌ |
| Resend | email/resend_sender.py | 30s | ❌ | SMTP |
| DuckDuckGo | lead_finder/.../website_finder.py | 20s | ❌ | ❌ |
| Google CSE | agent_platform/.../web_search_gateway.py | 10s | ❌ | ❌ |
| zlatestranky.sk | lead_finder/.../directory_lookup.py | 12s | ❌ | ❌ |
| Turnstile | shared/infrastructure/turnstile.py | 5s | ❌ | skip |
| Nominatim+OSRM | recommendations/.../routing.py | 12s | ❌ | Maps link |
| SMTP | email/sender.py | 20s | ❌ | – |

Žiadny retry. Viacero synchrónnych (urlopen) v async → blokuje loop.

### 1.5 Bezpečnostný model

Guards: require_current_user, require_admin, require_company_member,
require_company_admin, is_platform_admin.

Endpoints bez auth:
- zámerne: /health, /agent-platform/control/status
- 🔴 BUG-01: GET /api/v1/uploads/{file_id}

Rate limit: middleware 15 pravidiel + in-handler.
Medzery: /admin/lead-outreach/*, /agent-platform/chat, /documents,
/notifications.

JWT: PyJWT, HS256, family_id pri refresh, revocation store
(Redis/memory).

CSRF: žiadna ochrana (tokeny v localStorage, Bearer → nižšie riziko).

XSS: backend CSP má, frontend CSP NEMÁ (BUG-03).

SQL injection: ORM + parametrizované text(). OK.

---

## 2. Nálezy

### 2.1 Bezpečnostné diery

P0:
BUG-01: Uploady čitateľné bez autentifikácie
- Dôkaz: uploads/presentation/router.py:111-115
- Dopad: URL leak → dokument stiahnuteľný
- Fix: signed URL s HMAC + expirácia (P1, väčšia zmena)
- Poznámka: verejnosť bola zámerná (a5867b6 — img src)
- Status: BACKLOG (e5bb2fe)

P1:
BUG-02: Denný limit outreach (2 podbugy)
- Bug A: count_sent_today čítal activity_events.action (stĺpec je event_type)
- Bug B: write_audit s target_id='x@y.sk' padal na UUID validáciu
- Fix: _uuid_safe() + write_activity_event() + query na event_type
- Status: ✅ OPRAVENÉ (27854af)

BUG-03: Frontend bez CSP + JWT v localStorage
- Dôkaz: token-store.ts, next.config.js bez CSP
- Dopad: XSS → exfiltrácia JWT (refresh = 14 dní)
- Fix: CSP do next.config.js (nonce/hash)
- Status: P1 todo

P2:
BUG-04: Hardcoded *.onrender.com fallbacky
- Dôkaz: dashboard/page.tsx:89, password_reset.py:106,110,
  email_verification.py:109,112

BUG-05: Diagnostický write endpoint v produkcii
- Dôkaz: security_router.py:216 POST /security/test-write

P3:
BUG-06: /admin/lead-outreach/* bez rate limitu.

### 2.2 Mŕtvy kód

DEAD-01: app/shared/infrastructure/database.py — stub, 0 importov
DEAD-02: app/shared/infrastructure/rate_limiter.py — len testy
DEAD-03: paralelný phase4/5 tool stack v agent_platform/infrastructure/tools/ (10+ súborov)
DEAD-04: cmep_company_search.py — len 1 test
DEAD-05: duplicitné model_exports.py / recommendation_exports.py
DEAD-06: nepoužité závislosti v pyproject.toml (14 balíkov)

### 2.3 Architektúra nekonzistencie

ARCH-01: events, recommendations, uploads nemajú 4 vrstvy
ARCH-02: presentation importuje infrastructure (30 súborov)
ARCH-03: cross-module model import
ARCH-04: raw SQL v presentation (companies/router.py:329-390)
ARCH-05: duplicitné Resend sendery
ARCH-06: duplicitné analytics vs events

### 2.4 Chýbajúce testy

| Modul | Endpointov | Test súborov | Priorita |
|---|---|---|---|
| auth | 14 | 6 | P0 |
| users | 5 | 4 | P0 |
| admin | 8 | 1 | P0 |
| lead_finder | 7 | 5 | P0 |
| company_memberships | 4 | 0 | P0 |
| uploads | 3 | 0 | P0 |
| companies | 8 | 4 | P1 |
| listings | 12 | 3 | P1 |
| inquiries | 8 | 1 | P1 |
| documents | 5 | 0 | P1 |
| compliance | 5 | 0 | P1 |
| notifications | 7 | 4 | P1 |
| chat | 7 | 5 | P1 |
| agent_platform | 23 | 11 | P1 |
| prediction | 2 | 22 | P2 |
| analytics | 5 | 0 | P2 |
| recommendations | 3 | 0 | P2 |
| events | 2 | 0 | P2 |

Navrhnuté testy:
- test_uploads_requires_auth_get
- test_lead_outreach_daily_limit_enforced (✅ hotové)
- test_memberships_guard_viewer_cannot_write
- test_admin_delete_user_requires_platform_admin
- test_listings_promote_owner_only
- test_companies_suspend_platform_admin_only
- test_documents_company_scope

### 2.5 Chýbajúca funkcionalita

- NotImplementedError v ABC portoch (očakávané)
- GoPay: ai-upgrade-panel.tsx:116 "pripravujeme"
- @pytest.mark.xfail: test_notifications_repository.py:194
- Žiadne TODO/FIXME/XXX v produkčnom kóde

### 2.6 UI nedostatky

Orphan komponenty (13): select.tsx, textarea.tsx, page-header.tsx,
data-table.tsx, logo.tsx, listing-filters.tsx, promote-badge.tsx,
notifications-panel.tsx, thread-list.tsx, chat-window.tsx,
chat-draft-banner.tsx, report-button.tsx, ai-assistant-panel.tsx

Backup súbory v source tree
vitest chýba v devDependencies
Frontend CSP chýba (BUG-03)

### 2.7 API nedostatky

Chýbajúce rate limits: /admin/lead-outreach/*, /agent-platform/chat,
/uploads/{id} GET, /documents, /notifications
POST /listings (create) nemá write_audit
POST /events vracia 200 (nie 201)

### 2.8 DB model

- Chýbajúce FK pre prakticky celý core B2B model
- Chýbajúce indexy: listings.company_id/status,
  company_memberships.user_id, inquiries.company_id,
  notifications.user_id
- Nekonzistencia: companies Mapped[str] PK, listings UUID
- Nekonzistentné timestampy (tz-aware vs naive)
- Žiadny soft delete
- Migrácie v migrations/, docs/AUTHORITY.md hovorí alembic/

### 2.9 Performance

- Synchrónne blokovanie: rpo.py:32,140, routing.py:21
  (+ time.sleep(1.1)), groq_gateway.py:60
- Chýbajúce eager loading → N+1 riziko
- Chýbajúce retry
- Chýbajúca cache
- admin/router.py:252 .all() bez paginácie

### 2.10 Konfigurácia

.env.example má GROQ, GOOGLE_CSE, RESEND, BRAVE, PREDICTION
Chýba: SMTP_*, TURNSTILE_*, NEXT_PUBLIC_TURNSTILE_SITE_KEY,
GOOGLE_CLIENT_*, LEAD_OUTREACH_*, MATCHING_*, APP_DATA_DIR,
ENABLE_METRICS, METRICS_ALLOWED_IPS
BRAVE_SEARCH_API_KEY je v .env.example, ale kód prešel na DDG
.env.compose s plaintext heslom (rotovať)

### 2.11 Git / Workflow

- Untracked: =6.0.0, dump.sh, .atuin/ (✅ vyriešené v 724e902)
- Tracknutý junk: BuildFailed v roote
- Remote branches: origin/fix/security-config-improvements
- .gitignore duplicitné sekcie

### 2.12 Dokumentácia

- README odkazuje bez prefixu
- docs/PLATFORM_STATUS.md zastarané (uvádza ecac8dc)
- docs/AUTHORITY.md deklaruje neexistujúce cesty
- docs/api-contracts.md spomína materials-taxonomy (neexistuje)
- Chýbajúci CHANGELOG.md a LICENSE

---

## 3. Návrhy

### 3.1 Krátkodobé (dni) — P0/P1

| # | Nález | Krok | Súbor | Čas | Riziko |
|---|---|---|---|---|---|
| 1 | BUG-01 | signed URL | uploads/router.py | S | nízke |
| 2 | BUG-02 | ✅ hotové | resend_sender.py | S | nízke |
| 3 | BUG-03 | CSP do next.config.js | next.config.js | M | stredné |
| 4 | BUG-04 | odstrániť onrender.com fallbacky | viac | S | nízke |
| 5 | BUG-05 | vypnúť test-write v prod | security_router.py | S | nízke |
| 6 | ARCH-01/02 | zjednotiť vrstvy | AGENT_CONTEXT.md | L | stredné |
| 7 | 2.9 | urlopen → httpx.AsyncClient | rpo, routing, groq | M | stredné |
| 8 | 2.11 | ✅ vyčistené | root | S | nízke |
| 9 | 2.10 | doplniť env | .env.example | S | nízke |

### 3.2 Strednodobé (týždne)

- FK constraints + indexy cez Alembic migráciu
- Doplniť P0 testy (memberships, admin, uploads)
- Zapnúť typecheck + vitest do CI
- Konsolidovať duplicitné tool/email stacks
- Frontend CSP + httpOnly refresh cookie
- Rate limit na admin/lead-outreach/*, agent-platform/chat
- Retry/backoff na externé volania

### 3.3 Dlhodobé (mesiace)

- Migrácia file storage na S3/MinIO
- Billing (GoPay) + entitlement enforcement
- Eager loading + Redis data cache
- Zjednotiť analytics_events a activity_events
- Observability (Prometheus/Grafana/Loki — infra/, nie nasadené)

### 3.4 Alternatívne prístupy

Autentifikácia: (A) localStorage (teraz), (B) httpOnly cookie,
(C) BFF pattern
Email discovery: (A) DDG (teraz), (B) Brave, (C) Google CSE
AI mode: (A) system prompt, (B) permission engine, (C) oddelené routes
File storage: (A) disk (teraz), (B) S3 presigned, (C) DB BLOB

---

## Súhrn — Top 10 kritických

1. 🔴 BUG-01 — uploady bez auth (BACKLOG)
2. ✅ BUG-02 — denný limit (27854af)
3. 🟠 BUG-03 — frontend CSP + JWT localStorage
4. 🔴 Chýbajúce FK constraints
5. 🟠 Synchrónne urlopen/time.sleep v async
6. 🟠 BUG-04 — hardcoded onrender.com fallbacky
7. 🟠 Chýbajúce P0 testy
8. 🟡 BUG-05 — security/test-write v prod
9. 🟡 DEAD-03 — duplicitný phase4/5 tool stack
10. 🟡 Zastarané docs, .env.compose

Odhad P0+P1: 5–7 pracovných dní.

---

Poznámka: Prepis auditu od Atuin AI (session 2026-10-02).
