"""Helper to normalize timezone-aware datetimes to naive UTC.

Postgres stlpce v governance tabulkach su TIMESTAMP WITHOUT TIME ZONE.
asyncpg odmieta tz-aware datetime. Preto pred vlozenim konvertujeme.
"""

from __future__ import annotations

from datetime import UTC, datetime


def to_naive_utc(dt: datetime | None) -> datetime | None:
    """Convert tz-aware datetime to naive UTC. tz-naive returns unchanged."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt
