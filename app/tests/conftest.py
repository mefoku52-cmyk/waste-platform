"""Hermetic test environment pre app/tests.

`app/tests` musia byť unit testy — nikdy nesmú reálne čítať developérsky `.env`
(ktorý mieri na PostgreSQL) ani reálny Redis. Tento conftest pinne prostredie
pred importom `app.core.config.settings`. Hodnoty zrkadlia tests/conftest.py.
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

# Hermetic: nikdy reálny Redis server.
os.environ["REDIS_URL"] = "memory://"
# Rate limiting je stavový — vypnutý v testoch.
os.environ["RATE_LIMIT_ENABLED"] = "false"
