# CMEP Platform Extensions – Implementation Status

Branch: feat/platform-extensions

## Modul 8: Multi-photo + Document Versioning + ACL

### Stav: PARTIAL

#### Hotové
- Domain modely + PhotoACL
- SQLAlchemy model + repository
- Návrh migrácie
- Router s kontrolou MIME a veľkosti
- Unit testy (ACL + upload pravidlá)
- Dokumentácia v slovenčine: docs/platform-extensions/module-8-photos.md

#### Zostáva
- Plné prepojenie routera na repository + membership ACL
- Document versioning
- Integračné testy

#### Poznámka
UUID sa používajú, pretože všetky entity v CMEP majú UUID primárne kľúče.