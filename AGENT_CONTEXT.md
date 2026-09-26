# AGENT_CONTEXT.md

> Trvalý kontext pre každú novú konverzáciu. Commitnutý v repe, aby sme nezačínali od nuly.

## 1. Projekt

- **Názov:** CMEP — Circular Materials Exchange Platform
- **Repo:** https://github.com/mefoku52-cmyk/waste-platform
- **Doména:** trc-cmep.sk
- **Vlastník:** Radoslav Čornanič (trc-cmep@gmail.com)
- **Účel:** Súkromná B2B burza obehových materiálov (odpad, vedľajšie produkty,
  sekundárne suroviny). Overené firmy, skryté kontakty, dopyty cez interný chat,
  dokumenty, AI asistent.

## 2. Stack

### Backend
- Python 3.11+ / FastAPI / Pydantic v2
- SQLAlchemy 2.x async + Alembic
- JWT (PyJWT) + bcrypt + Redis (voliteľne)
- APScheduler (daily matching job)
- Groq API (LLM gateway pre AI chat + lead drafting)
- pytest + pytest-asyncio

### Frontend
- Next.js 15 (App Router) / React 19 / TypeScript
- TanStack Query v5 / react-hook-form + zod
- Tailwind CSS
- Vitest (unit testy — zatiaľ minimálne pokrytie)

### Runtime
- Dev: SQLite (`sqlite+aiosqlite:///./var/cmep.db`), Redis `memory://` fallback
- Prod: PostgreSQL 16, Redis 7, MinIO (S3-compatible), Nginx
- Deploy: Docker Compose, GitHub Actions

## 3. Štruktúra modulov (backend)

app/core/ config, exception handlers, main.py
app/modules/ admin, agent_platform, analytics, auth, chat, companies,
             company_memberships, compliance, documents, events, inquiries,
             lead_finder, listings, notifications, prediction, recommendations,
             uploads, users
app/shared/ domain, application, infrastructure, presentation

Každý modul má vrstvy: domain / application / infrastructure / presentation.

## 4. Autorizácia — dôležité

Dve ODDELENÉ úrovne oprávnenia (nikdy ich nemiešať):

- **Platform admin** = email v PLATFORM_ADMIN_EMAILS ALEBO rola `platform_admin`.
  Riadí celú platformu. NIE JE to isté ako firemný `admin`.
- **Company admin** = `owner` alebo `admin` v company_memberships pre konkrétnu firmu.
  Riadí len tú jednu firmu.

Zdroj pravdy: `app/shared/presentation/authorization.py`.
Frontend dostáva serverom vypočítaný `isPlatformAdmin` z /auth/me.
NIKDY neodvodzovať z roleCodes (to je tenant-scoped).

## 5. Subscription tiers

`free / pro / ai` (v tomto poradí, ai > pro > free).

- free — bez AI chatu
- pro — AI chat, odporúčania
- ai — všetko + budúce AI funkcie

Zdroj: `app/modules/companies/application/entitlements.py`.
Zmena tieru: PATCH /api/v1/companies/{id}/subscription-tier (platform admin).

## 6. Status enums

- CompanyStatus: draft → verification_submitted → verified/rejected → suspended/inactive
- ListingStatus: draft → published → reserved → completed → archived
- UserStatus: invited → pending_verification → active → suspended → deactivated
- InquiryStatus: open → answered → closed
- MembershipRole: owner / admin / member / compliance_contact / sales_contact /
  logistics_contact / viewer

## 7. Agent platform (AI)

app/modules/agent_platform/ — kontrolovaná AI vrstva.

Princípy:
- AI != AUTHORITY. AI navrhuje, ale policy + permission + audit rozhodujú.
- Každý tool call: policy → permission → approval (ak treba) → dispatch → audit → event.
- Tools sú deny-by-default.
- Existuje forbidden_tool_names.py (shell, sql, filesystem, secrets — nikdy ako tools).

Tools registrované pre prihlásených userov:
- search_companies(q, company_type, seller_capability, buyer_capability, logistics_capability)
- search_listings(q, material_type, location)
- search_nearby_companies(near, buyer_capability, material_type, limit)
- get_listing_transport(listing_id, from_location, consumption, fuel_price, roundtrip)

Admin-only tools:
- get_platform_stats
- get_recent_activity(days, limit)
- get_companies_with_tiers(tier, limit)
- get_my_company_context

Chat: POST /api/v1/agent-platform/chat
- Gated: platform admin vždy, inak vyžaduje PRO alebo AI tier
- Session-scoped pamäť v ai_conversations + ai_messages
- Rolu-aware system prompt (architect vs customer addendum)
- Persona picker: bystry / drzy / lenivy / op

## 8. Kľúčové rozhodnutia

- SQLite v dev, PostgreSQL v prod. V prod config odmietne SQLite.
- JWT revocation cez Redis (alebo memory fallback v dev).
- Email verify + password reset cez token v Redis, jednorazový.
- RPO lookup (overenie IČO) cez api.statistics.sk — bez API kľúča, CC-BY 4.0.
- Routing cez Nominatim + OSRM — bez platených máp.
- AI gateway cez Groq (openai/gpt-oss-120b), natívne tool calls.
- Batch outreach limit 30/den, Resend primárny, SMTP fallback.
- Recommendation scoring deterministický (nie ML), prediction_bridge
  je zatiaľ neaktívny (PREDICTION_SERVICE_ENABLED=false).

## 9. Kde čo žije

- Config:              app/core/config.py
- Route mount:         app/shared/presentation/api_router.py
- Auth:                app/shared/presentation/auth_dependencies.py + authorization.py
- DB session:          app/shared/infrastructure/db/session.py
- Migrations:          migrations/versions/
- Agent tool schemas:  app/modules/agent_platform/infrastructure/tools/tool_schemas.py
- Agent DI:            app/modules/agent_platform/presentation/dependencies.py

## 10. Environment (prod)

Povinné:
- APP_ENV=production
- DATABASE_URL=postgresql+asyncpg://...
- JWT_SECRET_KEY (min 32 znakov, nie placeholder)
- PLATFORM_ADMIN_EMAILS

Odporúčané:
- GROQ_API_KEY (AI chat)
- RESEND_API_KEY + RESEND_FROM_EMAIL (lead outreach)
- REDIS_URL (rate limit, revocation)
- SMTP_* (fallback email)
- LEAD_OUTREACH_ENABLED (default false)

## 11. Known issues / pozor

- prediction/ modul je len foundation. PREDICTION_SERVICE_ENABLED=false default.
- GoPay je spomenutý v terms/page.tsx, ale NIE JE implementovaný v kóde.
- Produkčný deploy na VPS — docs a skripty existujú, deployment nie je overený.
- apps/web/.next/ a apps/web/node_modules/ reálne existujú v pracovnom strome.
- Historické .bak/.before-* súbory v _archive/ (nie v runtime).
