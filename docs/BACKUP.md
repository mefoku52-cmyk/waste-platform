# Backup — Waste Platform

**Updated:** 2026-10-05

## Overview

Production database: Render Postgres `waste-platform-db`
(`dpg-dakh3fe1egvs73bs262g-a`).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup/backup-prod.sh` | Production DB dump + optional Telegram upload |
| `scripts/backup/healthcheck.sh` | Last backup validation (age, size, integrity) |
| `scripts/backup/backup-db.sh` | Deprecated (exits 1) |

## Manual run (Render Shell)

```

cd /opt/render/project/src
bash scripts/backup/backup-prod.sh --upload
bash scripts/backup/healthcheck.sh

```

## Automated run (Render Cron Job)

- Type: `Cron Job`
- Schedule: `0 3 * * *`
- Command: `bash scripts/backup/backup-prod.sh --upload`
- Env: same as web service + `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`

## Retention

7 daily backups (`-mtime +7` deletion). Telegram retains history.

## Restore

```

gunzip waste-platform-YYYYMMDD_HHMMSS.sql.gz
psql "$DATABASE_URL" < waste-platform-YYYYMMDD_HHMMSS.sql
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM outreach_candidates;"

```

## Incident log

- 2026-09-25 — 2026-10-05: silent backup failure. Legacy script dumped
  empty `cmep` DB; produced 20-byte `.gz` files. No healthcheck.
  Detected 2026-10-04. Fixed 2026-10-05.
