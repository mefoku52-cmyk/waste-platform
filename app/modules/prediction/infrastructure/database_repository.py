from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class TableSchema:
    """
    Read-only description of a database table.

    The prediction adapter uses this instead of hard-coding a large
    number of assumptions about the evolving CMEP schema.
    """

    table_name: str
    columns: tuple[str, ...]

    def has(self, column: str) -> bool:
        return column in self.columns


class PredictionDataRepository:
    """
    Read-only repository for prediction feature extraction.

    IMPORTANT:

    This class deliberately does not use INSERT, UPDATE, DELETE,
    ALTER, CREATE, DROP, or migration operations.

    It reads the existing CMEP database through the existing
    SQLAlchemy AsyncSession.

    The repository is intentionally tolerant of schema differences.
    Before querying a table it discovers its columns.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session
        self._schema_cache: dict[str, TableSchema | None] = {}

    # --------------------------------------------------------
    # Identifier safety
    # --------------------------------------------------------

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        """
        Quote a SQL identifier after validating its shape.

        Identifiers never come directly from a user request.
        They originate from information_schema.
        """

        if not identifier:
            raise ValueError("Empty SQL identifier.")

        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")

        if any(character not in allowed for character in identifier):
            raise ValueError(f"Unsafe SQL identifier: {identifier!r}")

        return f'"{identifier}"'

    # --------------------------------------------------------
    # Schema discovery
    # --------------------------------------------------------

    async def table_schema(
        self,
        table_name: str,
    ) -> TableSchema | None:
        """
        Discover a table's columns using information_schema.

        PostgreSQL is the primary CMEP runtime.

        SQLite fallback is also supported for local tests/dev where
        information_schema is not available.
        """

        if table_name in self._schema_cache:
            return self._schema_cache[table_name]

        # PostgreSQL / compatible databases
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

            columns = tuple(str(row[0]) for row in result.fetchall())

            if columns:
                schema = TableSchema(
                    table_name=table_name,
                    columns=columns,
                )

                self._schema_cache[table_name] = schema

                return schema

        except Exception:
            # SQLite/local fallback below.
            pass

        # SQLite fallback
        try:
            result = await self._session.execute(
                text(f"PRAGMA table_info({self._quote_identifier(table_name)})")
            )

            columns = tuple(str(row[1]) for row in result.fetchall())

            if columns:
                schema = TableSchema(
                    table_name=table_name,
                    columns=columns,
                )

                self._schema_cache[table_name] = schema

                return schema

        except Exception:
            pass  # best-effort: never break caller

        self._schema_cache[table_name] = None

        return None

    # --------------------------------------------------------
    # Generic helpers
    # --------------------------------------------------------

    @staticmethod
    def _first_existing(
        schema: TableSchema | None,
        candidates: tuple[str, ...],
    ) -> str | None:
        if schema is None:
            return None

        for candidate in candidates:
            if schema.has(candidate):
                return candidate

        return None

    async def _scalar(
        self,
        sql: str,
        params: dict[str, Any],
    ) -> Any:
        result = await self._session.execute(
            text(sql),
            params,
        )

        return result.scalar()

    # --------------------------------------------------------
    # Listing
    # --------------------------------------------------------

    async def get_listing(
        self,
        listing_id: str,
    ) -> dict[str, Any]:
        """
        Read one listing.

        Only columns that actually exist are selected.
        """

        schema = await self.table_schema("listings")

        if schema is None:
            return {}

        selected_candidates = (
            "id",
            "title",
            "description",
            "material_type",
            "materialType",
            "category",
            "location",
            "quantity",
            "unit",
            "status",
            "company_id",
            "companyId",
            "created_at",
            "createdAt",
            "updated_at",
            "updatedAt",
            "published_at",
            "publishedAt",
        )

        selected = [column for column in selected_candidates if schema.has(column)]

        if not selected:
            return {}

        quoted = ", ".join(self._quote_identifier(column) for column in selected)

        id_column = self._first_existing(
            schema,
            (
                "id",
                "listing_id",
                "listingId",
            ),
        )

        if id_column is None:
            return {}

        sql = (
            f"SELECT {quoted} "
            f"FROM {self._quote_identifier('listings')} "
            f"WHERE {self._quote_identifier(id_column)} = :listing_id "
            f"LIMIT 1"
        )

        result = await self._session.execute(
            text(sql),
            {
                "listing_id": listing_id,
            },
        )

        row = result.mappings().first()

        if row is None:
            return {}

        return dict(row)

    # --------------------------------------------------------
    # Count helper
    # --------------------------------------------------------

    async def count_for_subject(
        self,
        *,
        table_name: str,
        subject_id: str,
        subject_columns: tuple[str, ...] = (
            "listing_id",
            "listingId",
            "listing",
            "subject_id",
            "subjectId",
            "entity_id",
            "entityId",
        ),
    ) -> int:
        """
        Count rows related to a subject.

        The actual foreign-key column is discovered from the table.
        """

        schema = await self.table_schema(table_name)

        if schema is None:
            return 0

        subject_column = self._first_existing(
            schema,
            subject_columns,
        )

        if subject_column is None:
            return 0

        sql = (
            f"SELECT COUNT(*) "
            f"FROM {self._quote_identifier(table_name)} "
            f"WHERE {self._quote_identifier(subject_column)} "
            f"= :subject_id"
        )

        value = await self._scalar(
            sql,
            {
                "subject_id": subject_id,
            },
        )

        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    # --------------------------------------------------------
    # Listing views
    # --------------------------------------------------------

    async def listing_view_count(
        self,
        listing_id: str,
    ) -> int:
        return await self.count_for_subject(
            table_name="listing_views",
            subject_id=listing_id,
            subject_columns=(
                "listing_id",
                "listingId",
                "listing",
                "subject_id",
                "subjectId",
            ),
        )

    # --------------------------------------------------------
    # Inquiries
    # --------------------------------------------------------

    async def inquiry_count(
        self,
        listing_id: str,
    ) -> int:
        return await self.count_for_subject(
            table_name="inquiries",
            subject_id=listing_id,
            subject_columns=(
                "listing_id",
                "listingId",
                "listing",
                "subject_id",
                "subjectId",
            ),
        )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    async def recommendation_count(
        self,
        listing_id: str,
    ) -> int:
        """
        Count recommendation records when such a table exists.

        Existing CMEP recommendations may currently be calculated
        dynamically rather than stored. In that case this returns 0
        without inventing a value.
        """

        for table_name in (
            "recommendations",
            "recommendation_results",
            "listing_recommendations",
        ):
            schema = await self.table_schema(table_name)

            if schema is None:
                continue

            return await self.count_for_subject(
                table_name=table_name,
                subject_id=listing_id,
            )

        return 0

    # --------------------------------------------------------
    # Event count
    # --------------------------------------------------------

    async def event_count(
        self,
        listing_id: str,
    ) -> int:
        """
        Count directly attributable event rows when the event schema
        contains a listing/subject foreign key.

        We intentionally do not search arbitrary event_metadata text
        for the ID. That would create false positives and turn an
        analytics log into a rather questionable oracle.
        """

        for table_name in (
            "activity_events",
            "events",
            "analytics_events",
        ):
            schema = await self.table_schema(table_name)

            if schema is None:
                continue

            subject_column = self._first_existing(
                schema,
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
                continue

            return await self.count_for_subject(
                table_name=table_name,
                subject_id=listing_id,
                subject_columns=(subject_column,),
            )

        return 0

    # --------------------------------------------------------
    # Company listing count
    # --------------------------------------------------------

    async def company_listing_count(
        self,
        company_id: str | None,
    ) -> int:
        if not company_id:
            return 0

        schema = await self.table_schema("listings")

        if schema is None:
            return 0

        company_column = self._first_existing(
            schema,
            (
                "company_id",
                "companyId",
                "company",
                "owner_company_id",
                "ownerCompanyId",
            ),
        )

        if company_column is None:
            return 0

        sql = (
            f"SELECT COUNT(*) "
            f"FROM {self._quote_identifier('listings')} "
            f"WHERE {self._quote_identifier(company_column)} "
            f"= :company_id"
        )

        value = await self._scalar(
            sql,
            {
                "company_id": company_id,
            },
        )

        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    # --------------------------------------------------------
    # Table availability report
    # --------------------------------------------------------

    async def available_tables(
        self,
        table_names: tuple[str, ...],
    ) -> dict[str, bool]:
        result: dict[str, bool] = {}

        for table_name in table_names:
            result[table_name] = (await self.table_schema(table_name)) is not None

        return result
