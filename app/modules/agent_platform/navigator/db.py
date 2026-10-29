"""Rozhranie na PostgreSQL - iba overenie pripojenia. Ziadne vytvaranie ani migracie."""

from __future__ import annotations

import os
from typing import Any


class DatabaseInterface:
    """Iba citanie/overenie PostgreSQL. Bez CREATE DATABASE, bez migracii."""

    def __init__(self, dsn: str | None = None):
        self.dsn = dsn or os.environ.get("DATABASE_URL", "")

    def check_connection(self) -> dict[str, Any]:
        """Overi, ci je PostgreSQL dostupny. Nemeni nic. Nikdy nevracia surove chyby."""
        if not self.dsn:
            return {"available": False, "reason": "DATABASE_URL nie je nastavena"}
        try:
            import psycopg2  # type: ignore
        except ImportError:
            return {"available": False, "reason": "psycopg2 nie je nainstalovany (neinstalujem)"}
        try:
            conn = psycopg2.connect(self.dsn)
            conn.close()
            return {"available": True, "reason": "OK"}
        except Exception:
            return {"available": False, "reason": "Pripojenie zlyhalo (detail redigovany)"}

    def list_tables(self) -> list[str]:
        """Vrati zoznam tabuliek (iba citanie)."""
        if not self.dsn:
            return []
        try:
            import psycopg2  # type: ignore

            conn = psycopg2.connect(self.dsn)
            cur = conn.cursor()
            cur.execute(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            )
            rows = [r[0] for r in cur.fetchall()]
            cur.close()
            conn.close()
            return rows
        except Exception:
            return []
