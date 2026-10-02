# CMEP — Backlog

## P1 (plánované)
- **Signed URL pre uploads** — endpoint GET /uploads/{file_id}
  je zámerne verejný, aby `<img src>` fungoval. UUID nie je
  secret (leaky cez referrer/logy/chat). Riešenie: signed URL
  s HMAC tokenom v query + expirácia (5 min).
  Nájdené v forensic audite 2026-10-02.

## P2 (dlhodobé)
- **Joomla cloak email vetva akceptuje gmail** —
  `_extract_joomla_cloak_email` v directory_lookup.py povoľuje
  gmail.com adresy. Ak firma má len cloaked gmail v JS, prejde.
  Zjednotiť s _FREE_EMAIL_DOMAINS filtrom.
  Nájdené pri P0-4b (2026-10-02).
