# Modul 8 – Multi-photo + Document Versioning + ACL

## Prehľad
Správa fotografií pre listings s tenant izoláciou na úrovni firmy.

## ACL (prístupové práva)
- `PhotoACL.can_read` / `can_write` kontrolujú, či `company_id` fotky patrí do množiny firemných členstiev používateľa.
- Iba členovia firmy, ktorá vlastní listing, môžu čítať alebo zapisovať fotky.

## Pravidlá uploadu
- Povolené MIME typy: `image/jpeg`, `image/png`, `image/webp`
- Maximálna veľkosť: 10 MB

## Prečo UUID
Všetky entity v CMEP používajú UUID ako primárne kľúče.  
`listing_id`, `company_id`, `created_by` sú preto typu `UUID`.  
Endpointy prijímajú UUID, aby boli konzistentné so zvyškom platformy a tenant izoláciou.

## Súbory
- `app/modules/listings/domain/photos.py` – domain modely + ACL
- `app/modules/listings/infrastructure/models/listing_photo.py` – SQLAlchemy model
- `app/modules/listings/infrastructure/repositories/listing_photo_repository.py` – repository
- `app/modules/listings/presentation/photos_router.py` – router s validáciou
- `docs/platform-extensions/migrations/proposed_listing_photos.py` – návrh migrácie
- `tests/unit/test_listing_photos.py` – testy ACL
- `tests/unit/test_photo_upload_rules.py` – testy MIME a veľkosti

## Integrácia
Router zatiaľ nie je zaregistrovaný v `api_router.py` (chránený súbor).  
Navrhovaná registrácia:
```python
from app.modules.listings.presentation.photos_router import router as photos_router
api_router.include_router(photos_router)
```