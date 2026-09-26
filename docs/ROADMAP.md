# ROADMAP

> Stav ku commitu: b776ba6 (feat: transport + nearby companies READ-ONLY tools)
> Tento súbor sa updatuje pri každom milestone.

## Dokončené

### Fáza 1 — Core marketplace
- [x] Companies (CRUD, status transitions, capabilities)
- [x] Listings (CRUD, publish, promote, view stats)
- [x] Inquiries
- [x] Chat (threads + messages, anti-leak sanitizácia)
- [x] Documents, Compliance, Notifications, Analytics
- [x] Company memberships + roly

### Fáza 2 — Auth hardening
- [x] Login / refresh / logout (JWT revocation)
- [x] Email verification
- [x] Password reset
- [x] Rate limiting (login, forgot, resend)

### Fáza 3 — Admin
- [x] Admin dashboard (stats, users, audit)
- [x] Subscription tiers panel (FREE/PRO/AI)
- [x] Company verification workflow

### Fáza 4 — Agent platform foundation
- [x] Domain: agent, policy, permission, audit, events, tools
- [x] Application: pipeline, orchestrator, memory
- [x] Infrastructure: allowlist policy, permission engine, sqlalchemy event publisher
- [x] Presentation: chat router s entitlement gate

### Fáza 5 — AI chat
- [x] Groq gateway (tool calls)
- [x] Conversation memory (ai_conversations, ai_messages)
- [x] Rolu-aware system prompt (architect / customer)
- [x] Persona picker (bystry/drzy/lenivy/op)
- [x] Anti-leak rules (base prompt)

### Fáza 6 — Admin AI tools
- [x] get_platform_stats
- [x] get_recent_activity
- [x] get_companies_with_tiers
- [x] get_my_company_context

### Fáza 7 — Lead finder
- [x] outreach_candidates table + entity + repository
- [x] AI email drafter (early bird offer)
- [x] Batch drafter (max 30)
- [x] Resend sender s daily limitom
- [x] Admin UI (single + batch)

### Fáza 8 — Recommendations
- [x] Deterministic scoring (score_company)
- [x] Material taxonomy (EWC-style families)
- [x] Routing (Nominatim + OSRM + fuel)
- [x] Carrier search
- [x] Daily matching job (APScheduler + email templates)

### Fáza 9 — Prediction (foundation only)
- [x] Feature extractor + feature set
- [x] Baseline predictor (deterministický, nie ML)
- [x] Recommendation bridge (inactive by default)
- [x] Outcome repository (read-only)
- [ ] Zapnúť v produkcii a reálne používať — TODO

### Fáza 10 — Agent tools pre bežných userov
- [x] search_companies
- [x] search_listings
- [x] search_nearby_companies (commit b776ba6)
- [x] get_listing_transport (commit b776ba6)

## Práve teraz

- [x] Cleanup _archive/ (historické .bak/.backup-*/.before-*)
- [x] AGENT_CONTEXT.md + tento ROADMAP.md
- [ ] Overiť že AI chat má reálny kontext o nových tools
- [ ] Testy pre nové agent tools

## Blízke ďalšie

- [ ] Prediction — zapnúť PREDICTION_SERVICE_ENABLED=true v dev, overiť dáta
- [ ] Prediction — napojiť do recommendations (prediction_bridge je hotový, neaktívny)
- [ ] Testy pre prediction modul

## Plánované (nie urgentné)

- [ ] GoPay — platobná brána (v terms spomenuté, v kóde chýba)
- [ ] Production deploy — VPS + Nginx + Let's Encrypt
- [ ] MinIO migrácia — teraz uploads idú do lokálneho var/uploads/
- [ ] Frontend testy — Vitest nastavený, minimálne pokrytie
- [ ] Monitoring — Prometheus/Grafana/Loki configy sú, deployment neoverený

## Mimo scope (vedome)

- WordPress / Netlify / Joomla — CMEP je vlastný FastAPI + Next.js stack
- LLM tréning — používame Groq API (hosted)
- Auto-deal — platforma NIKDY neuzatvára obchod, len sprostredkuje kontakt

## Pravidlá pre commity

1. Každý commit = jedna logická zmena.
2. Message: feat(modul): popis / fix(modul): popis / docs: popis / chore: popis.
3. Pred commitom: ruff format, ruff check, ty check, pytest — všetko musí prejsť.
4. Žiadne .bak, .backup-*, .before-* v commite.
5. Tajomstvá (.env, .env.production, JWT kľúče) NIKDY v gite.
6. Pri zmene DB schémy: nová Alembic migrácia, nie editácia starej.

## Otvorené rozhodnutia (čakajú na usera)

- Kedy spustiť produkčný deploy? (VPS, doména, DNS)
- GoPay: teraz alebo po deployi?
- Prediction: ML model alebo zostať pri deterministickom baseline?
- Ktoré AI funkcie sú top priorita pre PRO/AI tiera?
