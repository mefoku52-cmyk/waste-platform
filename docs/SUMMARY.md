# SUMMARY.md
## Circular Materials Exchange Platform

Tento dokument je celkový prehľad projektu B2B platformy pre obchodovanie s odpadom, vedľajšími produktmi a sekundárnymi surovinami medzi firmami. Projekt bol navrhnutý a rozpracovaný ako greenfield systém od produktovej špecifikácie až po produkčné nasadenie, monitoring, load testing a finalizačné prevádzkové postupy.

## Cieľ projektu

Platforma prepája firmy, ktoré produkujú materiálový odpad alebo vedľajšie produkty, s firmami, ktoré ich vedia kúpiť, spracovať alebo znovu použiť. Jadrom riešenia je dôveryhodný B2B marketplace s firemným overením, štruktúrovanými listingami materiálov, inquiry workflow, dokumentmi, auditom, administráciou a pripravenosťou na neskoršie AI rozšírenia.

## Prehľad 14 fáz

### Fáza 1 – Produktová špecifikácia
Definovaný business cieľ, problém, role, user journeys, MVP scope, non-MVP scope, riziká a success metrics. Táto fáza vytvorila source of truth pre ďalšie návrhové a implementačné rozhodnutia.

### Fáza 2 – Doménový model
Navrhnuté hlavné entity systému a ich väzby, vrátane konzistentných názvov, statusov a auditovateľných polí. Doménový model ukotvil entity ako company, user, listing, inquiry, negotiation, document a audit event.

### Fáza 3 – Workflow a stavy
Definované povinné lifecycle diagramy a stavové prechody, najmä pre listingy, inquiry a súvisiace procesy. Zafixované boli aj alternatívne vetvy ako rejected, expired, disputed a cancelled.

### Fáza 4 – Architektúra aplikácie
Navrhnutá modulárna architektúra systému s oddelením backend modulov, frontend vrstvy, storage, search a infra vrstvy. Dôraz bol na rozšíriteľnosť, bezpečnosť, traceability a B2B authorization model.

### Fáza 5 – Databázová schéma
Navrhnutá perzistentná dátová štruktúra nad PostgreSQL vrátane entít, kľúčov, statusov, väzieb a auditných polí. Schéma rešpektuje versionovateľnosť a neskoršie rozšírenia bez zmeny významu jadrových entít.

### Fáza 6 – API kontrakty
Definované API endpointy a kontrakty v OpenAPI štýle pre auth, companies, users, listings, inquiries a ďalšie moduly. V tejto fáze sa stabilizovali request/response modely a naming conventions medzi backendom a frontendom.

### Fáza 7 – Backend implementácia
Vygenerované backend moduly pre FastAPI vrátane auth, companies, users, listings, inquiries a ďalších služieb. Implementácia rešpektuje validáciu, auditovateľnosť, status transitions a repository/service pattern.

### Fáza 8 – Frontend implementácia
Vygenerované frontend stránky a komponenty v Next.js/React s TypeScriptom. Frontend je previazaný na reálne API kontrakty a typy, bez oddelených „mock-only“ UI vrstiev.

### Fáza 9 – Testy
Pridané unit a integračné testy pre backend a frontend vrstvy. Cieľom bolo overiť základné správanie jadrových modulov, API kontraktov a kritických workflow vetiev.

### Fáza 10 – Deployment a infra základ
Vytvorené Dockerfile, docker-compose, CI/CD základy a environment-based konfigurácia. Táto fáza pripravila projekt na kontajnerový runtime model a reprodukovateľné prostredia.

### Fáza 11 – Produkčný deployment na VPS
Navrhnutý produkčný docker-compose.yml, Nginx reverse proxy s HTTPS, GitHub Actions deploy workflow, deploy.sh, .env.production a health endpoint. Táto fáza pokrýva základné produkčné nasadenie na single VPS.

### Fáza 12 – Monitoring a logging
Pridaný observability stack s Prometheus, Grafana, Loki, Promtail a Alertmanager. Doplnili sa /metrics endpointy, dashboardy, alerty a dokumentácia pre monitoring a logovanie.

### Fáza 13 – Load testing a škálovanie
Pridané load testy cez k6 vrátane smoke, load a breakpoint testov, scenárov pre auth/listings/companies a základného rate limiteru. Výsledkom je baseline pre výkonové testovanie a capacity planning.

### Fáza 14 – Produkčná finalizácia
Doplnené finálne prevádzkové dokumenty, backup/restore skripty, production readiness checklist, troubleshooting, security headers, dependabot a celkové dokončenie projektu. Táto fáza uzatvára repozitár ako prevádzkovo pripravený základ.

## Hlavné moduly systému

- auth
- companies
- users
- company_memberships
- materials-taxonomy
- listings
- inquiries
- negotiations
- logistics
- compliance
- documents
- notifications
- analytics
- admin
- shared infrastructure a presentation vrstva

## Technický stack

### Backend
- FastAPI
- Python
- Pydantic
- SQLAlchemy
- Async repository/service pattern
- JWT autentifikácia
- RBAC authorization

### Frontend
- Next.js
- React
- TypeScript

### Dáta a storage
- PostgreSQL 16
- Redis
- MinIO ako S3-compatible object storage

### Infra a runtime
- Docker
- Docker Compose
- Nginx reverse proxy
- Let's Encrypt
- GitHub Actions CI/CD

### Observability a performance
- Prometheus
- Grafana
- Loki
- Promtail
- Alertmanager
- k6

## Štruktúra repozitára

