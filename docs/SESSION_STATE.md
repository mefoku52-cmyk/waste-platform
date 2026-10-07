# Session State

**Aktualizované:** 2026-10-07
**Posledný commit:** 1820220 (company listings section + AI upgrade panel i18n)
**Branch:** main == origin/main
**Alembic head:** ab3fa1390046

## Produkcia
- trc-cmep.sk (Render)
- Backend: srv-dak1fp942lol73bl6ubg
- Frontend: srv-dal7p0rm8rtd73f72340
- DB: dpg-dakh3fe1egvs73bs262g-a

## Aktívne blokátory
- GitHub Actions `startup_failure` (account-level, Support ticket)
- `alembic check` padá na pre-existing drift (agent_*, activity_events) — neblokuje

## Otvorené (nedotiahnuté)
- **Meta Pixel** — acquisition backend + frontend hotový, pixel ešte nepripojený
- **GoPay** — dokončiť platby (číslo účtu, ceny)
- **AI tier (FREE/PRO/AI)** — backend hotový, UI + ceny TODO
- **Push po zverejnení ponuky** — aktívni odberatelia dostanú notifikáciu (plán)
- **Preklady** — hardcoded texty v landing krokoch, listings status, companies, admin, auth, features
- **Detail firmy — logo, "Aktívne ponuky tejto firmy"**
- **Android app** — rozrobená, nie hotová

## Posledná session (2026-10-07)

Veľký pracovný blok — 10 sessions uzavretých, 11 commitov pushnutých.

**Overené v produkcii:**
- AI draft: `POST /api/v1/listings/ai-draft` → 200, `provider=groq`
- Publish: `POST /api/v1/listings/{id}/publish` → 200, marketplace OK, cleanup OK

**Kód a fixy:**
- `aab3d72` — HISTORY/SESSION_STATE: E2E verification záznam
- `768fb19` — docstring + error_responses v AI draft route → 409 (ConflictDomainError)
- `543c7bb` — AI draft multi-company: vyberie prvú membership firmu s AI tierom
- `36c2934` — HISTORY/SESSION_STATE: zaevidovanie 768fb19 + 543c7bb
- `2146852` — unit test pre ai-draft route (4 testy: auth, tier gate, multi-company)
- `0e089d7` — Meta Pixel integrácia do `layout.tsx` + track.ts sync
- `621a43b` — .env.example placeholders (META_PIXEL + GOPAY)
- `2fbbc49` — unit test pre /billing/status (unconfigured = 200, configured=false)
- `d3d83ad` — Logo firmy: Alembic migrácia `c7d8e9f0a1b2`, entity/model/schema/mapper, form upload, detail display
- `1820220` — Company detail active listings section + public listings endpoint; AI upgrade panel i18n + GoPay company_id fix

**Nové endpointy:**
- `GET /api/v1/companies/{id}/listings` — verejné ponuky firmy (only published)

**DB:**
- Nová migrácia `c7d8e9f0a1b2_add_company_logo_url` (head)
- Alembic upgrade sa aplikuje na Renderi pri deployi


Detaily: `docs/HISTORY/`
