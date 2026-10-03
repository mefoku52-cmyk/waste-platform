# Waste Platform — Roadmap (aktuálny stav)

**Aktualizované:** 2026-10-03
**Aktuálna fáza:** Fáza 1.2 hotová lokálne, čaká na push

## Hotové commity (lokálne, nepushnuté)

| Hash    | Popis |
|---------|-------|
| e96bb58 | fix(website-finder): skip hst.link URL shortener |
| 6d22842 | fix(directory-lookup): extract company homepage, not register cross-link |
| ec8d465 | refactor(directory-lookup): _pick returns card mailto only, no HTTP |
| 9c9f886 | feat(lead-finder): crawl company homepage for contact email |

`main` je ahead 4 voči `origin/main`.

## Stav testov

`pytest tests/unit` -> **591 passed, 0 failed**
(pred fázou 1.2: 552 passed, 1 failed)

## Aktuálne blokátory

1. **Render billing** — Payment failed, doplniť kartu
2. **GitHub billing** — neoverené, možný ghost workflow `BuildFailed`
3. **CI gate** — mŕtvy od 2026-09-14 (ghost workflow_id 357626350, jobs=0)

## Rozhodnutia prijaté vo fáze 1.2

- D1: Domain-match je primárne pravidlo pre validáciu emailu
- D2: Free email (gmail/yahoo) prijatý len ak local-part obsahuje >=3 znaky z názvu firmy
- D3: Joomla cloak fetch odstránený z _pick — crawler je jediný fetch homepage
- D4: Cache = Redis (sync) + in-memory fallback; negatívny výsledok cachovaný LEN pri definitívnom mise
- D5: 1s delay medzi requestami na tú istú doménu

## Nasledujúce kroky (po vyriešení blokátorov)

1. Push 4 commitov -> over, či CI chytí event
2. Ak CI padne na reálnych chybách -> oprav (NIE gate)
3. Baseline meranie: vzorka 100 leadov z Render DB cez scripts/measure_coverage.py
4. Middle/final measurement — tá istá vzorka, rôzne commity
5. Fáza 2: doplňujúce zdroje URL (DuckDuckGo + IČO)
6. Fáza 3: DirectoryProvider Protocol (až keď bude >=2 live provideri)
7. Fáza 4: oprava tichého zlyhania záloh (od 2026-09-25 dumpuje prázdnu DB)

## Metriky

- **Baseline (ae3d486):** TBD
- **Po fixe A+B:** TBD (spätne už len cez git checkout)
- **Po 1.2:** TBD
- **Akceptačný cieľ:** +15 pb na vzorke s homepage URL
- **Realistický strop:** 5/9 kariet na zlatestranky má homepage -> crawler preskočí ~44% firiem
