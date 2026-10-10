"""Hermetic test environment for module-level test packages.

`app/modules/**/tests` are unit tests and must never resolve to the real
database, Redis or external providers. Pytest loads this conftest before it
imports any test module below `app/modules`, so the environment is pinned
*before* `app.core.config.settings` (which otherwise reads the developer's
`.env`, potentially pointing at PostgreSQL) is imported.

Values mirror `tests/conftest.py`.
"""

import os
import tempfile

_test_db_url = f"sqlite+aiosqlite:////{os.path.join(tempfile.gettempdir(), 'zyvo_ci')}/test.db"

# Priame priradenie: shell môže exportovať DATABASE_URL/REDIS_URL (Postgres) —
# testy musia byť hermetic vždy, nie len keď env nie je nastavený.
os.environ["DATABASE_URL"] = _test_db_url
os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-ok"
os.environ["ENV"] = "test"
os.environ["APP_ENV"] = "test"

# Hermetic: never talk to a real Redis server.
os.environ["REDIS_URL"] = "memory://"
# Rate limiting is stateful; keep it off so a single run cannot trip 429.
os.environ["RATE_LIMIT_ENABLED"] = "false"
