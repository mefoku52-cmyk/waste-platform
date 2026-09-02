# Authority contract

| Concern | Canonical path | Everything else |
|---|---|---|
| Backend app | `app/` | no second backend tree |
| Frontend app | `apps/web/` | ignore `apps/t` |
| Env contract | `.env.example` | real values only in untracked `.env` |
| Compose | `docker-compose.yml` | backups in `_quarantine` |
| Backend image | `docker/backend/Dockerfile` | inner `app/Dockerfile` archived |
| Frontend image | `docker/frontend/Dockerfile` | inner `apps/web/Dockerfile` archived |
| Migrations | `alembic/` + `alembic.ini` | do not grow a second tree |
| Deploy docs | `docs/deployment.md` | no parallel `DEPLOYMENT.md` |
| Forensic scripts | `scripts/forensics/archive/` | not repository root |
| Generated audits | `_quarantine/` | never live `audit-output/` |

Rotate every secret that ever lived in `.env*`, README or compose.
This script does not rewrite git history.
