# Backup — Waste Platform

**Updated:** 2026-10-14

## Overview

Production database: Render Postgres `waste-platform-db`
(`dpg-dakh3fe1egvs73bs262g-a`).

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup/backup-prod.sh` | Production DB dump + gzip + optional age encryption + optional Telegram upload |
| `scripts/backup/healthcheck.sh` | Last backup validation (age, size, checksum/gzip integrity) |
| `scripts/restore.sh` | Restore a dump into a target DB; refuses production-looking targets |
| `scripts/backup/backup-restore-test.sh` | Self-contained E2E test (temp Postgres, encrypt/decrypt/restore round-trip) |
| `scripts/backup/backup-db.sh` | Deprecated (exits 1) |

## Env (backup host)

| Var | Meaning |
|-----|---------|
| `BACKUP_AGE_RECIPIENT` | age public key (`age1...`); enables `--encrypt` |
| `BACKUP_AGE_IDENTITY_FILE` | age private-key file; needed to decrypt/verify |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID` | needed for `--upload` |

Secrets are read from env only and are never printed. If encryption is
requested but the recipient is missing, the script FAILS — it never
uploads an unencrypted dump.

## Manual run (Render Shell)

```
cd /opt/render/project/src
bash scripts/backup/backup-prod.sh --encrypt --upload
bash scripts/backup/healthcheck.sh
```

## Automated run (Render Cron Job)

- Type: `Cron Job`
- Schedule: `0 3 * * *`
- Command: `bash scripts/backup/backup-prod.sh --encrypt --upload`
- Env: same as web service + `BACKUP_AGE_RECIPIENT`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`

## Retention

7 daily backups (`-mtime +7` deletion). Telegram retains history.

## Restore

Use `scripts/restore.sh` — it guards against overwriting production.

```
# 1) Decrypt + verify (if encrypted)
age -d -i "$BACKUP_AGE_IDENTITY_FILE" waste-platform-YYYYMMDD_HHMMSS.sql.gz.age \
  > waste-platform-YYYYMMDD_HHMMSS.sql.gz
sha256sum -c waste-platform-YYYYMMDD_HHMMSS.sql.gz.age.sha256

# 2) Restore into a NON-production target (guard blocks prod names)
DATABASE_URL="postgresql://..." bash scripts/restore.sh waste-platform-YYYYMMDD_HHMMSS.sql.gz

# Overwriting production requires an explicit flag:
bash scripts/restore.sh dump.sql.gz --confirm-production
```

`restore.sh` prints `SOURCE_TABLES`, `TARGET_TABLES` and `DIFF` so a
mismatch is visible immediately.

### Note: 29 vs 26 tables

A `SOURCE_TABLES`/`TARGET_TABLES` diff does NOT always mean data loss.
Known reasons:

- `activity_events` and `admin_audit_entries` are created by raw SQL on
  some environments but ARE in Alembic (`b1a2c3d4e5f6`, `1577dceccd9e`).
  A dump taken before those migrations, restored into an
  `alembic upgrade head` DB (or vice-versa), yields a count diff.
- `alembic_version` itself is a table and counts.

Always compare the actual table NAMES, not just the count, before
concluding anything was lost.

## Incident log

- 2026-09-25 — 2026-10-05: silent backup failure. Legacy `backup-db.sh`
  ran `pg_dump ... | gzip > file` with no size guard; on failure gzip
  still produced a valid 20-byte empty `.gz`, so bad backups looked
  "present" and passed a naive existence check. No healthcheck.
  Detected 2026-10-04. Fixed 2026-10-05 with a size guard in
  `backup-prod.sh`.
- 2026-10-14: added age encryption before any upload, per-file
  `.sha256` checksum, decrypt-verify, and a production guard in
  `restore.sh`. `healthcheck.sh` now validates `.age` checksums too.
