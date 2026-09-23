from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.prediction.domain.outcome import (
    OutcomeEvent,
    OutcomeKind,
    OutcomeWindow,
)


class OutcomeRepository:
    """
    Read-only historical outcome adapter.

    This layer does NOT decide the target.

    It exposes observable historical events when the existing CMEP
    schema provides enough information to identify them.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    @staticmethod
    def _identifier(
        value: str,
    ) -> str:
        if not value:
            raise ValueError("Empty SQL identifier.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

        if any(character not in allowed for character in value):
            raise ValueError(f"Unsafe SQL identifier: {value!r}")

        return f'"{value}"'

    async def _columns(
        self,
        table_name: str,
    ) -> tuple[str, ...]:
        try:
            result = await self._session.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = current_schema()
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                    """
                ),
                {
                    "table_name": table_name,
                },
            )

            return tuple(str(row[0]) for row in result.fetchall())

        except Exception:
            return ()

    @staticmethod
    def _first(
        columns: tuple[str, ...],
        candidates: tuple[str, ...],
    ) -> str | None:
        for candidate in candidates:
            if candidate in columns:
                return candidate

        return None

    async def list_events(
        self,
        *,
        subject_type: str,
        subject_id: str,
        window: OutcomeWindow,
    ) -> tuple[OutcomeEvent, ...]:
        """
        Read directly attributable historical events.

        Currently supported sources are discovered dynamically.

        We do not parse event_metadata blobs for identifiers because
        that would create ambiguous attribution.
        """

        if subject_type != "listing":
            return ()

        events: list[OutcomeEvent] = []

        # ----------------------------------------------------
        # Listing views
        # ----------------------------------------------------

        await self._append_table_events(
            events=events,
            table_name="listing_views",
            subject_id=subject_id,
            kind=OutcomeKind.VIEW,
            source="db:listing_views",
            window=window,
        )

        # ----------------------------------------------------
        # Inquiries
        # ----------------------------------------------------

        await self._append_table_events(
            events=events,
            table_name="inquiries",
            subject_id=subject_id,
            kind=OutcomeKind.INQUIRY,
            source="db:inquiries",
            window=window,
        )

        # ----------------------------------------------------
        # Activity events
        # ----------------------------------------------------

        await self._append_table_events(
            events=events,
            table_name="activity_events",
            subject_id=subject_id,
            kind=OutcomeKind.CUSTOM,
            source="db:activity_events",
            window=window,
        )

        # ----------------------------------------------------
        # Analytics events
        # ----------------------------------------------------

        await self._append_table_events(
            events=events,
            table_name="analytics_events",
            subject_id=subject_id,
            kind=OutcomeKind.CUSTOM,
            source="db:analytics_events",
            window=window,
        )

        events.sort(key=lambda item: item.occurred_at)

        return tuple(events)

    async def _append_table_events(
        self,
        *,
        events: list[OutcomeEvent],
        table_name: str,
        subject_id: str,
        kind: OutcomeKind,
        source: str,
        window: OutcomeWindow,
    ) -> None:
        columns = await self._columns(table_name)

        if not columns:
            return

        subject_column = self._first(
            columns,
            (
                "listing_id",
                "listingId",
                "subject_id",
                "subjectId",
                "entity_id",
                "entityId",
            ),
        )

        if subject_column is None:
            return

        timestamp_column = self._first(
            columns,
            (
                "created_at",
                "createdAt",
                "occurred_at",
                "occurredAt",
                "timestamp",
                "event_time",
                "eventTime",
            ),
        )

        if timestamp_column is None:
            return

        id_column = self._first(
            columns,
            (
                "id",
                "event_id",
                "eventId",
            ),
        )

        selected = [
            subject_column,
            timestamp_column,
        ]

        if id_column is not None:
            selected.append(id_column)

        quoted_columns = ", ".join(self._identifier(column) for column in selected)

        sql = (
            f"SELECT {quoted_columns} "
            f"FROM {self._identifier(table_name)} "
            f"WHERE {self._identifier(subject_column)} "
            f"= :subject_id "
            f"AND {self._identifier(timestamp_column)} "
            f">= :window_start "
            f"AND {self._identifier(timestamp_column)} "
            f"< :window_end "
            f"ORDER BY {self._identifier(timestamp_column)} ASC"
        )

        try:
            result = await self._session.execute(
                text(sql),
                {
                    "subject_id": subject_id,
                    "window_start": window.start,
                    "window_end": window.end,
                },
            )
        except Exception:
            # Some legacy/local schemas may have incompatible
            # timestamp types. The outcome adapter must not make
            # the prediction service unavailable.
            return

        for row in result.mappings().all():
            timestamp = row.get(timestamp_column)

            if not isinstance(
                timestamp,
                datetime,
            ):
                continue

            event_id = None

            if id_column is not None:
                raw_id = row.get(id_column)

                if raw_id is not None:
                    event_id = str(raw_id)

            events.append(
                OutcomeEvent(
                    subject_type="listing",
                    subject_id=subject_id,
                    kind=kind,
                    occurred_at=timestamp,
                    value=1.0,
                    source=source,
                    event_id=event_id,
                )
            )
