# Security Audit — CMEP Platform

Dátum: 2026-09-30
Audítor: Radoslav Čornanič (s asistovanou analýzou)
Rozsah: Black-box pentest + code review produkčnej platformy `trc-cmep.sk`

## Executive summary

Vyšetrených 13 oblastí. Nájdených a opravených **8 nálezov**, z toho **2 kritické**:

- **XFF spoofing bypass rate limitu** — útočník mohol obísť rate limit podvrhnutím `X-Forwarded-For` hlavičky a brute-forceovať 2FA kódy
- **Chýbajúce bezpečnostné hlavičky** na oboch vrstvách (FastAPI + Next.js) — celý frontend aj API bez HSTS, CSP, X-Frame-Options

Všetkých 8 nálezov je opravených a nasadených na produkciu (commity `c2b6716` … `abde26d`).

## Použitá metodika

- Manuálne HTTP testy (curl) na živú produkciu
- Statická analýza zdrojového kódu (grep + cat)
- Bez externých nástrojov (žiadny Burp, OWASP ZAP)
- Bez prístupu k produkčnej DB, logom alebo Render dashboardu

## Nálezy a opravy

### P0 — Kritické

#### 1. X-Forwarded-For spoofing bypass rate limitu
- **Endpoint:** `POST /api/v1/auth/2fa/login`
- **Dôkaz:** 15 requestov s fake XFF `1.1.1.1` → 10×401, 5×429. Hneď ďalšie 3 requesty s fake XFF `2.2.2.2` → **3×401** (nový bucket).
- **Príčina:** `client_ip()` bral **PRVÝ** prvok `X-Forwarded-For`. Za Cloudflare je formát `XFF: <fake>, <real>`, takže útočník mohol rotovať fake ľavý prvok.
- **Fix:** Priorita `CF-Connecting-IP` → `X-Real-IP` → **POSLEDNÝ** prvok XFF → `request.client.host`. Cloudflare `CF-Connecting-IP` nedá podvrhnúť.
- **Commit:** `abde26d`
- **Verify:** 15×401 s XFF 1.1.1.1, ale **hneď 3×429** s XFF 2.2.2.2.

#### 2. Chýbajúce bezpečnostné hlavičky
- **Dôkaz:** `curl -I https://trc-cmep.sk/` vracal len Cloudflare defaulty, žiadne HSTS/CSP/X-Frame-Options.
- **Príčina:** FastAPI bez middleware pre hlavičky, Next.js bez `headers()` v `next.config.js`.
- **Fix:**
  - FastAPI: `SecurityHeadersMiddleware` (`app/shared/presentation/security_headers.py`)
  - Next.js: `headers()` v `next.config.js` + `poweredByHeader: false`
- **Commity:** `c2b6716`, `74506db`
- **Verify:** `/`, `/login`, `/api/v1/auth/me`, `/_next/static` → všetky hlavičky OK.

### P1 — Vysoké

#### 3. Rate limit bežal po Pydantic validácii
- **Endpointy:** `/auth/2fa/login`, `/agent-platform/control/*`, `/admin/*`, `/chat/*`, `/uploads/*`, `/listings/*`, `/inquiries`
- **Príčina:** `check_rate_limit` bol v tele handlera → malformované requesty dostali 422 od Pydantic **pred** limitom.
- **Fix:** `RateLimitMiddleware` beží pred validáciou tela.
- **Commit:** `60bfce6`
- **Verify:** 2FA login → 10×401, 5×429.

#### 4. Pydantic `input` leak v 422 odpovediach
- **Dôkaz:** 5000-znakový email v tele requestu sa vrátil celý v odpovedi.
- **Fix:** `RequestValidationError` handler vracia len `loc` + `msg`, nie `input`.
- **Commit:** `abde26d`
- **Verify:** `{"detail":[{"loc":["body","email"],"msg":"Input should be a valid string"}]}`.

#### 5. Osobné meno v `/agent-platform/control/status`
- **Dôkaz:** Verejný (bez auth) endpoint vracal `{"actor":"radoslav"}`.
- **Fix:** Odstránené pole `actor`.
- **Commit:** `1e8e1b3`

#### 6. CORS hardcoded origins v kóde
- **Príčina:** `_cors_origins()` v `main.py` pridával natvrdo `127.0.0.1:3001`, `localhost:3001`, `trc-cmep.sk`, `www.trc-cmep.sk` bez ohľadu na env.
- **Fix:** Číta len `settings.cors_origin_list()`. Dev domény len ak `is_development`.
- **Bonus bug:** `default_factory` mal vnorený string s čiarkami ako jeden prvok → pri default CORS by `www.trc-cmep.sk` nefungoval.
- **Commit:** `103fa81`
- **Verify:** `localhost:3001` na produkcii → žiadny ACAO. `evil.com` → žiadny ACAO.

### P2 — Stredné

#### 7. `python-jose` zbytočný v requirements
- Kód používa PyJWT (`import jwt`). `python-jose` bol legacy s CVE-2024-33663/33664.
- **Commit:** `60bfce6`

#### 8. `x-powered-by: Next.js` info leak
- **Fix:** `poweredByHeader: false`.
- **Commit:** `74506db`

## Veci, ktoré boli OK (netreba fix)

- **SQL injection** — SQLAlchemy + validácia → 422
- **XSS v email** — email-validator → 422
- **JWT alg=none** — PyJWT reject → 401
- **JWT neplatný podpis** — 401
- **Docs/OpenAPI v produkcii** — 404
- **IDOR** — všetky cudzie resources bez auth → 401
- **Password reset user enumeration** — rovnaká odpoveď pre existujúci aj neexistujúci email
- **2FA endpointy** — všetky vyžadujú auth (401 bez tokenu)
- **SSRF** — iba whitelist `api.statistics.sk`

## Tech debt (nie security blocker)

### T1. Upload endpoint vracia 308 redirect
`POST /uploads/` → 308 Permanent Redirect (trailing slash mismatch). Browser pri cross-origin 308 nezachová POST body.
**Fix:** `redirect_slashes=False` v FastAPI alebo dorovnať trailing slash.
**Priorita:** P2

### T2. Flaky test `test_company_transition`
Test volá `CreateCompanyService` bez mocku `lookup_ico`, ktorý reálne fetchuje `api.statistics.sk`. Pri výpadku RPO API test padá.
**Fix:** Mock `lookup_ico` v teste.
**Priorita:** P2

### T3. Redis testy failujú lokálne
9 testov v `test_jwt_service.py` a `test_jwt_revocation_store.py` vyžaduje bežiaci Redis na `127.0.0.1:6379`. V CI aj tak bežia.
**Fix:** `fakeredis` knižnica alebo pytest fixture s `redis-server --daemonize yes`.
**Priorita:** P2

### T4. Mass assignment netestované
PATCH endpointy neboli testované s extra poľami (`role`, `status`) — vyžaduje prihlásenie. Pydantic schémy by to mali blokovať, ale treba overiť.

## Odporúčania pre ďalšie kolo

1. **Test 4 z round 2** — refresh token reuse detection naživo (kód má `family_revoked` check)
2. **Test 8 z round 2** — mass assignment s platným účtom
3. **Test 10 z round 2** — kontrola Render logov (heslá, tokeny v plain text)
4. **Cloudflare WAF** — zvážiť zapnutie pre `'; DROP TABLE--` už teraz vracia 403 (pravdepodobne CF)
5. **CSP pre frontend** — nonce-based prístup pre Next.js (nie `unsafe-inline`)
6. **Subresource Integrity (SRI)** pre externé skripty
7. **Audit dependencies** — `pip-audit` alebo `safety` v CI

## Commity tejto iterácie

| Commit | Popis |
|---|---|
| `c2b6716` | FastAPI SecurityHeadersMiddleware |
| `74506db` | Next.js security headers + poweredByHeader:false |
| `1e8e1b3` | Odstránený meno leak z /control/status |
| `60bfce6` | RateLimitMiddleware + drop python-jose |
| `103fa81` | CORS do env, fix nested-string default |
| `abde26d` | **XFF bypass fix + Pydantic input leak fix** |
