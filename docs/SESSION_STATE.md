# Session State

**Aktualizované:** 2026-10-07
**Posledný commit:** b6f90b5 (feat listings: publish button, AI draft)
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
- **`listings/presentation/router.py`** — docstring AI draft route hovorí „403", ale kód hádže `ConflictDomainError` (pravdepodobne 409)

## Posledná session (2026-10-07)
E2E verifikácia AI draft + publish na produkcii:
- `POST /api/v1/listings/ai-draft` → 200, `provider=groq`
- `POST /api/v1/listings/{id}/publish` → 200, `status=published`, viditeľný v marketplace
- cleanup (DELETE) OK

Predtým (2026-10-05 → 10-07): 24 commitov — Render build fix, marketplace
split, acquisition tracking, batch send fix (30/30 emailov), entity_type
firmy, dashboard tiles, header simplified, i18n ru/fr.

Detaily: `docs/HISTORY/`
