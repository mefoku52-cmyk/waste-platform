# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Celkové zhrnutie

Všetky 8 modulov majú základné vrstvy na vetve. Žiadny nie je plne IMPLEMENTED.

| Modul | Stav | Hlavné hotové časti |
|-------|------|---------------------|
| 1. Webhooks | PARTIAL | Signing, SSRF, delivery, router, návrh migrácie |
| 2. Command Bus | PARTIAL | In-memory bus + registration |
| 3. Partner OAuth | PARTIAL | Domain + scopes |
| 4. CQRS Light | PARTIAL | Listings projection |
| 5. Saga | PARTIAL | Inquiry process manager |
| 6. Observability | PARTIAL | Business span helpers |
| 7. AI Approval | PARTIAL | DB-backed gate, orchestrator wiring, router, self-approval |
| 8. Multi-photo | PARTIAL | Model, repo, router + membership ACL, MIME/size, magic-bytes helper, document version model |

## Module 8 – posledné doplnenia
- `infrastructure/magic_bytes.py` – overenie skutočného obsahu (JPEG/PNG/WEBP)
- `infrastructure/models/document_version.py` – základný model verzií dokumentov

## Čo ďalej
1. Zapoj magic-byte kontrolu do photos_router (prijímať bytes namiesto storage_key).
2. Repository + endpoint pre document versions.
3. Integračné testy s reálnou DB.
4. Rovnaký postup pre zvyšné moduly (1–6) podľa priority.