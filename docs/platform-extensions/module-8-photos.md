# Modul 8 – Multi-photo + Document Versioning + ACL

## Stav: PARTIAL (repository + membership ACL zapojené)

### Hotové
- Domain modely + PhotoACL
- SQLAlchemy model + repository
- Návrh migrácie
- Router napojený na ListingPhotoRepository
- Vlastnícka firma sa načítava z tabuľky `listings` (nie z klienta)
- Membership ACL cez `require_company_member` proti reálnemu `company_id`
- MIME whitelist + max 10 MB
- Unit testy

### Ako funguje ochrana
1. `POST` / `GET` dostanú `listing_id`.
2. `_resolve_listing_company` načíta `company_id` z `listings` tabuľky.
3. Ak listing neexistuje → 404.
4. `require_company_member(current_user, company_id)` overí členstvo.
5. Iba potom sa volá repository.

### Zostáva
- Kontrola skutočného obsahu súboru (magic bytes)
- Document versioning
- Integračné testy s reálnou DB a cross-tenant scenármi

### Súbory
- `presentation/photos_router.py` (aktualizovaný)
- `infrastructure/models/listing_photo.py`
- `infrastructure/repositories/listing_photo_repository.py`
- `docs/platform-extensions/migrations/proposed_listing_photos.py`