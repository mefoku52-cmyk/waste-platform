# CMEP — History

Kronika sessions. Append-only, nikdy sa neprepisuje.

---

## 2026-10-05 → 2026-10-07

**Session focus:** oprava Render buildu, marketplace split, acquisition tracking, batch send, entity_type, dashboard UI.

### Commity (24)

| Commit | Oblasť |
|---|---|
| `3d07a58` | Render build fix — `'use client'` v ai-upgrade-panel |
| `b05a91c` | Auto-approve + batch tlačidlá v lead-outreach |
| `6bd21ed` | Thumbnail v listings aj na mobile |
| `c50a76a` + `2bf8247` | Marketplace / Moje ponuky split |
| `b96956d` | Acquisition tracking backend (`/api/v1/analytics/acquisition/events`) |
| `4902807` | Acquisition tracking frontend (`page_view`, `landing_view`) |
| `fab979c` + `8ae377e` | Batch send fix — fallback body, 30/30 emailov |
| `3614e01` | Sign endpoint bez Document row (listing fotky) |
| `b87646b` | imageUrl zod validácia |
| `29b4e28` | IČO regex fix (dvojitý backslash) |
| `6fbf1f9` | entity_type backend (migrácia `ab3fa1390046`) |
| `743e3a4` | Dynamický formulár firmy (SZČO / s.r.o. / NGO) |
| `4d22cb2` | entity_type v profile firmy |
| `0725077` + `a0b2e5d` + `952f9a6` | Edit firmy + request verification |
| `eae8740` | Landing redirect pre prihlásených |
| `5f3993d` | Dashboard 6 navigačných dlaždíc |
| `40491ae` | Header bez malých tlačidiel, dashboard bez marketplace preview |
| `b0262c2` | Header zjednodušený, ru/fr preklady |
| `2bc27ce` | Dashboard dlaždice cez i18n |

### Hotové features

- **Lead finder / outreach:** auto-approve, batch send, AI drafter, Resend sender
  - Fallback body ak draft chýba → **30/30 emailov úspešných**
- **Marketplace:** Moje ponuky vs Marketplace (vylučuje vlastné firmy)
- **Firmy:** entity_type (SZČO / s.r.o. / NGO), dynamický formulár, edit route,
  request verification, admin schvaľovanie
- **Acquisition tracking:** UTM + fbp/fbc + anonymous_id → DB. **Pripravené pre Meta Pixel.**
- **Dashboard:** 6 strieborných dlaždíc s fotkami, 5 dekoratívnych materiálov
- **Header:** logo + Admin + jazyk + odhlásiť + "← Späť na prehľad"

### i18n stav

- 5 jazykov: sk, en, de, ru, fr
- 648-649 kľúčov v každom
- ru/fr doplnené (13 kľúčov: companyForm.*, dashboard.nav.myListings)

### Zistené problémy

- `SESSION_STATE.md` bol zastaraný (commit `92ab304`, my na `2bc27ce`) — teraz aktuálny
- `alembic check` padá na pre-existing drift (`agent_*`, `activity_events`,
  `listing_views`, `user_2fa`) — **nie je naša chyba**, naša migrácia je čistá
- Bezpečnosť: Telegram token, Render API kľúč, Deploy Hook **leaknuté v chate**
  — treba rotovať pred finálnym spustením reklám

### TODO ďalej

Vysoká priorita:
1. Meta Pixel + Conversions API (acquisition je hotový)
2. Preklady hardcoded textov (landing, listings, companies, admin, auth, features)
3. GoPay / AI tier ceny
4. Push notifikácia po zverejnení ponuky

Stredná:
5. Detail firmy — logo, aktívne ponuky tejto firmy
6. Android app dokončiť

---

## Staršie sessions

Pozri `git log` alebo `ROADMAP_CURRENT.md` pre históriu pred 2026-10-05.
