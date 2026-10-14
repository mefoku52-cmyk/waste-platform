# Backup — Waste Platform

**Updated:** 2026-10-14

## Overview

Production database: Render Postgres `waste-platform-db`
(`dpg-dakh3fe1egvs73bs262g-a`).

Backups are **always age-encrypted** before leaving the host. The plaintext
dump is deleted after encryption; only `waste-platform-<stamp>.sql.gz.age`
(+ a `.sha256` checksum) is kept and uploaded.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/backup/backup-prod.sh` | Dump → gzip → age encrypt → verify → optional Telegram upload |
| `scripts/backup/healthcheck.sh` | Latest backup validation (age, size, checksum, decrypt) |
| `scripts/backup/test-backup.sh` | Self-contained end-to-end test on a throwaway local Postgres |
| `scripts/backup/backup-db.sh` | Deprecated (exits 1) |
| `scripts/restore.sh` | Restore; refuses production targets unless `--confirm-production` |

## Encryption configuration (keys NEVER inside the repo)

`backup-prod.sh` requires keys supplied via environment variables or paths
outside the repository. A key path that resolves inside the repo is rejected.

| Variable | Meaning |
|----------|---------|
| `BACKUP_AGE_RECIPIENT` | age public key (`age1...`) |
| `BACKUP_AGE_RECIPIENT_FILE` | file containing the public key (alternative to the above) |
| `BACKUP_AGE_IDENTITY_FILE` | age identity (secret key) used to verify the encrypted file decrypts |

Without a recipient **and** an identity file the script exits non-zero and
uploads nothing. A recommended location for the identity is
`$HOME/.config/cmep/backup-identity.txt` (chmod 600, outside the repo).

## Run

```
bash scripts/backup/backup-prod.sh            # local encrypted backup
bash scripts/backup/backup-prod.sh --upload   # + Telegram (encrypted only)
bash scripts/backup/healthcheck.sh
bash scripts/backup/test-backup.sh            # local self-test
```

## Automated run (Render Cron Job)

- Type: `Cron Job`
- Schedule: `0 3 * * *`
- Command: `bash scripts/backup/backup-prod.sh --upload`
- Env: web-service env + `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ADMIN_CHAT_ID`,
  `BACKUP_AGE_RECIPIENT` (or `BACKUP_AGE_RECIPIENT_FILE`),
  `BACKUP_AGE_IDENTITY_FILE`

## Retention

7 days of encrypted backups (`-mtime +7` deletion). Telegram retains history.

## Restore

```
age -d -i "$BACKUP_AGE_IDENTITY_FILE" waste-platform-YYYYMMDD_HHMMSS.sql.gz.age \
  | gunzip | psql "$DATABASE_URL" -
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM listings;"
```

`scripts/restore.sh` refuses any target whose database name or host looks like
production (Render host, `dpg-*` id, `cmep` / `waste-platform`) unless called
with `--confirm-production`.

## Table count reconciliation

`backup-prod.sh` prints tables in the live DB vs `CREATE TABLE` in the dump and
their difference. The two can legitimately differ (e.g. 29 vs 26): the DB count
includes tables in non-public schemas or partitioned tables, while the dump
scan counts only `CREATE TABLE` lines for the dumped schema(s).

## Incident log

- 2026-09-25 — 2026-10-05: silent backup failure. Legacy
  `scripts/backup/backup-db.sh` dumped an empty `cmep` DB and produced 20-byte
  `.gz` files (no size check, no healthcheck). Detected 2026-10-04. Fixed
  2026-10-05 (deprecated the legacy script, added `backup-prod.sh` +
  `healthcheck.sh`).
- 2026-10-14: added age encryption, checksum + decrypt verification, table
  count reconciliation, restore production guard and `test-backup.sh`.
