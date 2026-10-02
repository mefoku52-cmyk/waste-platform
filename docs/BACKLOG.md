# CMEP — Backlog

## P1 (plánované)
- **Signed URL pre uploads** — endpoint GET /uploads/{file_id}
  je zámerne verejný, aby `<img src>` fungoval. UUID nie je
  secret (leaky cez referrer/logy/chat). Riešenie: signed URL
  s HMAC tokenom v query + expirácia (5 min).
  Nájdené v forensic audite 2026-10-02.
