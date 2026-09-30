# Platform Status — CMEP

**Dátum:** 2026-09-30 12:22 UTC
**Git HEAD:** ecac8dc feat(prediction): expose PredictionService via HTTP + mount metrics router
**Branch:** main

## Moduly — stav

| Modul | Routes | Testy | Mounted | Stav |
|---|---|---|---|---|
| admin | 6 | 0 | ✅ | OK |
| agent_platform | 23 | 0 | ✅ | OK (port/adapter, 14 Default* impl.) |
| analytics | 5 | 0 | ✅ | OK |
| auth | 14 | 3 | ✅ | OK |
| chat | 7 | 5 | ✅ | OK |
| companies | 8 | 1 | ✅ | OK |
| company_memberships | 4 | 0 | ✅ | OK |
| compliance | 5 | 0 | ✅ | OK |
| documents | 5 | 0 | ✅ | OK |
| events | 2 | 0 | ✅ | OK |
| inquiries | 8 | 0 | ✅ | OK |
| lead_finder | 7 | 0 | ✅ | OK |
| listings | 12 | 2 | ✅ | OK |
| notifications | 7 | 3 | ✅ | OK |
| prediction | 2 | 44 | ✅ | OK (nasadené 2026-09-30, `ecac8dc`) |
| recommendations | 3 | 0 | ✅ | OK |
| uploads | 3 | 0 | ✅ | OK, T1 trailing slash |
| users | 5 | 0 | ✅ | OK |

## Bezpečnosť

8 nálezov opravených v KROKU 4, všetky nasadené na produkcii.
Detaily: `docs/SECURITY_AUDIT.md`

Zhrnutie:
- Security headers (FastAPI + Next.js)
- Rate limit middleware pred Pydantic validáciou
- XFF spoofing fix (CF-Connecting-IP priorita)
- Pydantic input leak fix
- CORS env-driven
- python-jose odstránený

## Observability

- `metrics_router` na `/api/v1/metrics`
- Default `ENABLE_METRICS=False` → 404
- IP whitelist: `METRICS_ALLOWED_IPS`
- Infra (prometheus, grafana, loki, alertmanager) v `infra/` — **nebeží na Renderi**

## Tech debt

### T1. Upload trailing slash (P2)
`POST /api/v1/uploads/` → 308 Permanent Redirect.
**Fix:** dorovnať trailing slash alebo `redirect_slashes=False`.

### T2. Flaky test `test_company_transition` (P2)
Volá reálne RPO API (`api.statistics.sk`) cez `CreateCompanyService`.
**Fix:** mock `lookup_ico` v teste.

### T3. Redis testy (P2)
9 testov vyžaduje Redis na `127.0.0.1:6379`. CI OK, Termux fail.
**Fix:** `fakeredis` alebo fixture.

### T4. Mass assignment (P2)
PATCH endpointy netestované s extra poľami.
**Fix:** manuálny test s platným účtom.

## Posledné commity

```
ecac8dc feat(prediction): expose PredictionService via HTTP + mount metrics router
8ee3088 docs(security): add SECURITY_AUDIT.md from KROK 4 (8 findings fixed)
abde26d security(rate-limit): fix X-Forwarded-For spoofing bypass + hide Pydantic input
103fa81 security(cors): remove hardcoded dev origins, fix nested-string default
60bfce6 security(rate-limit): global middleware + drop unused python-jose
1e8e1b3 security(agent-platform): remove personal name leak from public /control/status
74506db security(headers): add security headers to Next.js frontend
c2b6716 security(headers): add global SecurityHeadersMiddleware
```
