# CMEP — Backlog

## P1 (plánované)
- ~~**Signed URL pre uploads**~~ — **HOTOVÉ 2026-10-05**.
  Backend má `/uploads/{id}/sign` + verifikáciu podpisu v `GET /uploads/{id}`.
  Flag `UPLOADS_REQUIRE_SIGNED` je defaultne `False` — zapne sa po
  úprave frontendu (aby staré `<img src>` neprestali fungovať).
  Frontend integrácia je naplánovaná (viď TODO nižšie).

## P2 (dlhodobé)
- **Frontend: signed URLs pre uploads** — doplniť `getSignedUrl()` do
  `apps/web/src/features/uploads/api.ts` a použiť ho v
  `listing-form.tsx` a `document-form.tsx` pri `<img src>`. Potom
  zapnúť `UPLOADS_REQUIRE_SIGNED=true` na Renderi.
- **Joomla cloak email vetva akceptuje gmail** —
  `_extract_joomla_cloak_email` v directory_lookup.py povoľuje
  gmail.com adresy. Ak firma má len cloaked gmail v JS, prejde.
  Zjednotiť s _FREE_EMAIL_DOMAINS filtrom.
  Nájdené pri P0-4b (2026-10-02).
