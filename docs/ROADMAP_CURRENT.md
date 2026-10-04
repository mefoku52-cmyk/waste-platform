# Roadmap — aktuálny stav

**Aktualizované:** 2026-10-04
**Git HEAD:** 28680a3
**Branch:** main (v synchronizácii s origin/main, ahead 0)

## Dokončené

### Fázy 1–10 (z ROADMAP.md, skrátene)
| Fáza | Rozsah | Stav |
|---|---|---|
| 1 | Core marketplace — companies, listings, inquiries, chat, documents, compliance, notifications, analytics, memberships | HOTOVO |
| 2 | Auth hardening — login/refresh/logout (JWT revocation), email verify, password reset, rate limiting | HOTOVO |
| 3 | Admin — dashboard, subscription tiers (FREE/PRO/AI), company verification | HOTOVO |
| 4 | Agent platform foundation — domain, application, infra, presentation (14 Default* impl.) | HOTOVO |
| 5 | AI chat — Groq gateway (tool calls), conversation memory, role-aware prompt, persony, anti-leak | HOTOVO |
| 6 | Admin AI tools — platform stats, recent activity, companies with tiers, my company context | HOTOVO |
| 7 | Lead finder — outreach_candidates, AI drafter, batch (max 30), Resend sender + limit, admin UI | HOTOVO |
| 8 | Recommendations — scoring, material taxonomy, routing (Nominatim/OSRM), carrier search, daily job | HOTOVO |
| 9 | Prediction — feature extractor, deterministic baseline, bridge (neaktívny), outcome repo | FOUNDATION ONLY |
| 10 | Agent tools pre userov — search_companies, search_listings, search_nearby_companies, get_listing_transport | HOTOVO |

## Aktuálny stav

- **Produkcia:** beží na Renderi (web + API).
- **Testy:** `pytest tests/unit` → **591 passed, 0 failed**.
- **Commity z dnes (2026-10-03):** 12 commitov — lead-finder fáza 1.2 + test coverage.
  - `28680a3` governance datetime UTC · `41ea05e` groq_gateway failures · `10f7a04` CmepCompanySearchHandler
  - `5a7d5f4` scheduler tests · `b6725bf` turnstile 100% · `b27af13` set -Eeuo pipefail · `db81641` gitignore
  - `16b0177` roadmap snapshot + coverage harness · `9c9f886` crawl homepage for email
  - `ec8d465` _pick mailto only · `6d22842` company homepage extraction · `e96bb58` skip hst.link

## Tech debt

Prevzaté z `docs/PLATFORM_STATUS.md` (2026-09-30). Všetko P2.

| ID | Problém | Fix |
|---|---|---|
| T1 | Upload trailing slash — `POST /api/v1/uploads/` → 308 Permanent Redirect | Dorovnať trailing slash alebo `redirect_slashes=False` |
| T2 | Flaky test `test_company_transition` — volá reálne RPO API (`api.statistics.sk`) cez `CreateCompanyService` | Mockovať `lookup_ico` v teste |
| T3 | Redis testy — 9 testov chce Redis na `127.0.0.1:6379`; CI OK, Termux fail | `fakeredis` alebo fixture |
| T4 | Mass assignment — PATCH endpointy netestované s extra poľami | Manuálny test s platným účtom |

## Kritické blokátory

1. **DDG (DuckDuckGo) mŕtve** — `website_finder.py` závisí od `ddgs` / `duckduckgo_search`.
   Pri zlyhaní importu vracia graceful fallback → tiché zlyhanie bez výsledkov.
   Viď časť C nižšie: existuje náhradný Google CSE gateway v kóde, ale **nie je zapojený**.
2. **RPO pool — 53 IČO** — chýbajúce/poolované záznamy z RPO lookupu (z reportu 30 emailov).
3. **Cache miss 30 dní** — negatívne výsledky neboli cachované dostatočne dlho / chýbajúca
   perzistencia (in-memory fallback sa stratí pri restarte).
4. **Render billing** — Payment failed, treba doplniť kartu. Blokuje deploy aj CI event.

Súvisiace (z `ROADMAP_CURRENT.md`, sekcia blokátorov): GitHub billing neoverené (ghost
workflow `BuildFailed`) a CI gate mŕtvy od 2026-09-14 (ghost workflow_id 357626350, jobs=0).

## Next steps

1. **Google CSE migrácia** — `GoogleWebSearchGateway` je hotový, ale nezapojený (viď Open decisions).
   Cieľ: oživiť CSE pre `website_finder` namiesto mŕtveho DDG.
2. **Free-mail filter** — D2 pravidlo: gmail/yahoo prijatý len ak local-part obsahuje >=3 znaky
   z názvu firmy. Rozšíriť na ďalšie providery a doladiť false-negatives.
3. **Industry zoznamy** — mapovanie IČO → odvetvie pre lepšie párovanie leadov
   (chýba pri 53 IČO z RPO poolu).
4. **Blokátory najprv:** Render billing → push + CI event → baseline meranie
   (`scripts/measure_coverage.py`, vzorka 100 leadov).
5. **Fáza 4 roadmapy:** oprava tichého zlyhania záloh (od 2026-09-25 dumpuje prázdnu DB).
6. **Prediction:** zapnúť `PREDICTION_SERVICE_ENABLED=true` v dev, overiť dáta, napojiť bridge.

## Open decisions

- **Google CSE vs. DDG:** vrátiť sa ku CSE? CSE je spoľahlivý, ale pôvodný problém bol
  mandatory hostname + site-restricted engine odmietal celý web (viď commit `6aefe2b`).
  Treba rozhodnúť: nový engine s `search the entire web` vs. iný provider.
- **`GOOGLE_CSE_API_KEY` / `GOOGLE_CSE_ID` v Render env:** nechať, alebo vyčistiť?
  V kóde ich číta len nezapojený gateway.
- **Production deploy:** kedy? (VPS + Nginx + Let's Encrypt) — blokované Render billingom.
- **GoPay:** teraz alebo po deployi?
- **Prediction:** ML model alebo zostať pri deterministickom baseline?
- **Ktoré AI funkcie sú top priorita pre PRO/AI tiery?**
- **CI gate:** opraviť, alebo obísť? (rozhodnutie z fázy 1.2: neopravovať gate pred pushom)
