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

---

## Update — koniec relacie 2026-08-06, pred 12h pauzou

STAV GIT: prvy commit vytvoreny (46fbc54), 480 suborov. Bezpecny bod navratu.
Pri akomkolvek podozreni na poskodenie: git status, prip. git reset --hard 46fbc54

STAV app/modules/: VSETKYCH 11 modulov teraz FYZICKY EXISTUJE (predtym 7 chybalo).
Vytvoril ich pravdepodobne create-missing-files.sh, beh nezaznamenany v tejto konverzacii.
NEOVERENE: ci maju realny obsah/logiku, alebo len prazdne kostry. DALSI KROK po navrate:
kontrola velkosti/obsahu suborov v novych moduloch (napr. wc -l app/modules/listings/**/*.py).

STAV requirements.txt: napisany (app/requirements.txt), zalozeny na overenych importoch.
Vysledok pip install + import test v izolovanom venv NEBOL DOTIAHNUTY DO KONCA
(vystup sa v konverzacii prerusil). DALSI KROK: zopakovat cast 6 z full_diagnosis.sh
samostatne, poslat cely vystup.

STAV backend/ vs app/: docker-compose pouziva vylucne app/ (context: ./app).
backend/ ma VLASTNY requirements.txt, pyproject.toml, Alembic, a CIASTOCNY prekryv
s chybajucimi modulmi (listings: 6 vyskytov najdenych, inquiries: 0). Zvysok modulov
(documents/compliance/notifications/analytics/admin) v backend/ NEBOL preverenty
(skript sa prerusil). ROZHODNUTIE O OSUDE backend/ (zmazat/zlucit/ignorovat) STALE
NEBOLO PRIJATE — vyzaduje pouzivatelov kontext, ktory zatial neprisiel.

STAV auth na /metrics: STALE NEZNAME. Grok review auth_dependencies.py + main.py
nasiel len typovu anotacnu chybu (credentials: HTTPAuthorizationCredentials malo byt
| None) — FUNKCNE bezpecne (kod to osetruje), ale netykalo sa povodnej otazky.
DALSI KROK: precitat app/shared/presentation/api_router.py priamo, zistit ci a ako
je metrics router mountnuty a ci ma auth dependency.

FORENSICSUITE JSON AUDITY (3 uploadnute subory): security/architecture "80.0"/"40.0"
boli FALOSNY POPLACH sposobeny skenovanim obsahu backend_test_env (venv) vratane
kniznice pip samotnej. V REALNOM kode (app/) sa nenasla ANI JEDNA bezpecnostna/
architektonicka chyba tymto nastrojom. Jediny realny cyklicky import mimo venv:
backend/app/core/logging.py (self-import cez setuptools/logging.py) — izolovana,
nizka zavaznost.

PORADIE PRI NAVRATE (nemenit bez noveho dovodu):
1. cat app/shared/presentation/api_router.py — vyriesi otazku auth na /metrics
2. Dokoncit pip install test (cast 6 z full_diagnosis.sh)
3. Rozhodnutie o backend/ (potrebuje pouzivatelov kontext)
4. Kontrola obsahu 7 novo-existujucich modulov (prazdne kostry vs realna logika)
5. Oprava typovej anotacie v auth_dependencies.py (nizka priorita, rychla oprava)

---

## KRITICKE ROZHODNUTIE — 2026-08-08 — navrat k app/ + apps/web/

Zistene: docker-compose.yml (od prveho commitu, zmenene paralelnou reláciou) ukazoval
na backend/ + frontend/. Po hlbkovom vysetreni (KROK 36-50):
- frontend/ je prazdny skelet (0 .ts/.tsx suborov)
- backend/ ma funkcne modely a config, ale CHYBA CELA API vrstva (auth/companies/
  listings/users/websocket router moduly neexistuju, iba health.py)
- Viacero infrastrukturnych chyb postupne opravenych (SQLAlchemy verzia, DB driver,
  logging/metrics/security modulovy konflikt), ale zakladny problem (chybajuca logika)
  ostava.

ROZHODNUTIE: docker-compose.yml sa vracia na povodny cielsofer (context: ./app,
context: ./apps/web) - jediny funkcny, kompletne otestovany par. backend/ a frontend/
ostavaju v git historii nedotknute, NEMAZANE, pre pripadne buduce vyuzitie
(napr. ako referencia pre style/konvencie), ale nie su aktivny nasadzovaci ciel.
