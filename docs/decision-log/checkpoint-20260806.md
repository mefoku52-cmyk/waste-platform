# CHECKPOINT — 2026-08-06 — waste-platform (CMEP)

CITAJ TOTO PRVE PRI NAVRATE, PRED AKYMKOLVEK DALSIM KROKOM.

## Co je HOTOVE a OVERENE

1. metrics_router.py — IndentationError OPRAVENY (KROK 6), syntax OK.
   Import test s prometheus_client zatial NEBOL uspesny — chyba balik (bod 2).
2. Diagnostika chybajuceho requirements.txt kompletna:
   - app/Dockerfile ocakava requirements.txt priamo v app/ (COPY requirements.txt .)
   - subor v app/ NEEXISTUJE (FAIL, OVERENE)
   - skutocne pouzite externe importy (z AST parseru, KROK 6e): fastapi, jwt, passlib,
     prometheus_client, pydantic, sqlalchemy
   - SQLAlchemy: potvrdene 2.x (DeclarativeBase, Mapped, mapped_column) — 1.x style NENAJDENY
   - JWT kniznica: PyJWT (import jwt), NIE python-jose
   - DB driver: asyncpg (create_async_engine, DATABASE_URL=postgresql+asyncpg://...)
   - uvicorn chyba v AST vystupe (skript necapture-uje CLI pouzitie v Dockerfile CMD),
     ale JE potrebny — pridat rucne do requirements.txt
   - Pydantic verzia: NEOVERENE do tohto checkpointu — cakalo sa na vystup grep BaseModel
   - passlib hash schema (bcrypt/argon2): NEOVERENE do tohto checkpointu
3. ForensicSuite-v1 sken nad waste-platform_clean (kopia bez venv):
   maintainability 80.8, architecture 100.0, security 100.0
   security 100.0 VYSVETLENE — pocita len CVE + hardcoded secrets, NEPOKRYVA nase FAIL zistenia,
   preto NIE je v rozpore s nimi.
   diff -rq waste-platform vs waste-platform_clean: cisty okrem backend_test_env
   (zamerne vymazany z _clean) a checkpoint suborov pridanych po kopirovani.
4. AI-1 samostatny report (docs/decision-log/ai1-self-report-20260806.md) OZNACENY
   ako NEOVERENE — obsahuje aspon jeden dokazany nespravny udaj (docs/architecture-overview.md
   PASS tvrdenie proti realnemu WARN z validate-project.sh). Nepouzivat cisla z neho
   (87.4% skore) bez samostatneho overenia.

## Kompletny zoznam OVERENYCH FAIL/kritickych zisteni

1. metrics_router.py IndentationError — OPRAVENE, cakalo sa na import test (blokovany bodom 2)
2. metrics_router.py /metrics bez auth — WARN, este NEOPRAVENE, potrebuje znalost auth stacku
3. .env.production chyba v koreni — FAIL, NEOPRAVENE
4. requirements.txt chyba v app/ — FAIL, diagnostika hotova, napisanie caka na Pydantic/passlib evidenciu
5. 7 modulov chyba (listings, inquiries, documents, compliance, notifications, analytics, admin) — NEOPRAVENE
6. Git: nepotvrdene zmeny v repozitari — caka sa na vystup "git status" (tento checkpoint blok)
7. Signal 9 pri jednom behu v minulosti — bez dopadu na data, priciny nezname, neriesit dalej

## DALSI KROK (presne v tomto poradi, nepreskakovat)

KROK A: Precitat vystup grep BaseModel/CryptContext z tohto checkpointu (mal by byt priamo
  nad timto blokom v terminali) a rozhodnut Pydantic verziu + passlib schemu.
KROK B: Napisat requirements.txt so VSETKYMI zistenymi balikmi + spravnymi verziami,
  otestovat cez pip install v izolovanom prostredi (napr. python3 -m venv), NIE priamo
  do systemoveho pythonu.
KROK C: Znova spustit import test pre metrics_router.py, potvrdit IMPORT OK.
KROK D: Riesit .env.production (zoznam pozadovanych klucov je v scripts/validate-project.sh,
  REQUIRED_KEYS pole).
KROK E: Az potom chybajuce moduly, jeden po druhom, zacat s listings (najcastejsie
  spominany v dokumentacii/docker-compose).

## Dovod, preco po jednom kroku, nie vsetko naraz

Pouzivatel navrhol velky autonomny prompt (Faza 0-4, "ak nieco chyba vytvor to, ak existuje
lepsie riesenie implementuj ho") — ZAMIETNUTE v tejto konverzacii, lebo:
- grok.py nema realny pristup k filesystemu/procesom (len text in, text out)
- "implementuj lepsie riesenie" = domnienka, priamy rozpor so zakladnym pravidlom projektu
- velky rozsah v jednom behu nie je overitelny v rozumnom case
Pouzivatel súhlasil pokracovat v povodnom overenom tempe (jeden modul/subor za krokom).
