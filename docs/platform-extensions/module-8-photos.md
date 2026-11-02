# Modul 8 – Multi-photo + Document Versioning + ACL

## Prehľad
Správa fotografií pre listings s tenant izoláciou na úrovni firmy.

## Upload endpoint
`POST /listings/{listing_id}/photos`

- `listing_id` je UUID (konzistentné s CMEP primárnymi kľúčmi).
- Kontroluje MIME typ (`image/jpeg`, `image/png`, `image/webp`).
- Kontroluje maximálnu veľkosť (10 MB).
- V plnej implementácii overí ACL (PhotoACL) proti členstvu používateľa vo firme, ktorá vlastní listing.
- Uloží záznam cez ListingPhotoRepository.

## ACL
- `PhotoACL.can_read` / `can_write` kontrolujú, či `company_id` fotky patrí do množiny firemných členstiev používateľa.
- Iba členovia firmy, ktorá vlastní listing, môžu čítať alebo zapisovať fotky.

## Prečo UUID
Všetky entity v CMEP používajú UUID ako primárne kľúče.  
`listing_id`, `company_id`, `created_by` sú preto typu `UUID`.

## Súbory
- `app/modules/listings/domain/photos.py` – domain modely + ACL
- `app/modules/listings/infrastructure/models/listing_photo.py` – SQLAlchemy model
- `app/modules/listings/infrastructure/repositories/listing_photo_repository.py` – repository
- `app/modules/listings/presentation/photos_router.py` – router s validáciou
- `docs/platform-extensions/migrations/proposed_listing_photos.py` – návrh migrácie
- `tests/unit/test_listing_photos.py` – testy ACL
- `tests/unit/test_photo_upload_rules.py` – testy MIME a veľkosti
- `tests/unit/test_photo_uuid_and_rules.py` – testy UUID konzistencie

## Integrácia
Router zatiaľ nie je zaregistrovaný v `api_router.py` (chránený súbor).  
Navrhovaná registrácia:
```python
from app.modules.listings.presentation.photos_router import router as photos_router
api_router.include_router(photos_router)
```

## Stav
PARTIAL – domain, model, repository, návrh migrácie, validácie, unit testy a dokumentácia sú hotové.  
Chýba plné prepojenie routera na repository + reálna ACL kontrola proti membership a document versioning.