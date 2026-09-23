from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from app.modules.prediction.infrastructure.database_repository import (
    PredictionDataRepository,
)


@dataclass
class FakeRow:
    values: dict[str, Any]

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return tuple(self.values.values())[key]

        return self.values[key]


class FakeMappings:
    def __init__(
        self,
        row: dict[str, Any] | None,
    ) -> None:
        self._row = row

    def first(self) -> dict[str, Any] | None:
        return self._row


class FakeResult:
    def __init__(
        self,
        *,
        rows: list[Any] | None = None,
        scalar_value: Any = None,
        mapping: dict[str, Any] | None = None,
    ) -> None:
        self._rows = rows or []
        self._scalar = scalar_value
        self._mapping = mapping

    def fetchall(self) -> list[Any]:
        return self._rows

    def scalar(self) -> Any:
        return self._scalar

    def mappings(self) -> FakeMappings:
        return FakeMappings(self._mapping)


class FakeSession:
    def __init__(
        self,
        results: list[FakeResult],
    ) -> None:
        self.results = list(results)
        self.sql: list[str] = []

    async def execute(
        self,
        statement: Any,
        params: dict[str, Any] | None = None,
    ) -> FakeResult:
        self.sql.append(str(statement))

        if not self.results:
            raise AssertionError("Unexpected database query.")

        return self.results.pop(0)


@pytest.mark.asyncio
async def test_table_schema_discovers_columns() -> None:
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    ("id",),
                    ("material_type",),
                    ("company_id",),
                ]
            )
        ]
    )

    repository = PredictionDataRepository(session)

    schema = await repository.table_schema("listings")

    assert schema is not None

    assert schema.columns == (
        "id",
        "material_type",
        "company_id",
    )

    assert schema.has("material_type")
    assert not schema.has("missing")


@pytest.mark.asyncio
async def test_listing_is_read_from_existing_columns() -> None:
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    ("id",),
                    ("title",),
                    ("material_type",),
                    ("company_id",),
                ]
            ),
            FakeResult(
                mapping={
                    "id": "listing-1",
                    "title": "Wood",
                    "material_type": "wood",
                    "company_id": "company-1",
                }
            ),
        ]
    )

    repository = PredictionDataRepository(session)

    listing = await repository.get_listing("listing-1")

    assert listing["id"] == "listing-1"
    assert listing["material_type"] == "wood"
    assert listing["company_id"] == "company-1"


@pytest.mark.asyncio
async def test_missing_table_returns_empty_listing() -> None:
    session = FakeSession([FakeResult(rows=[])])

    repository = PredictionDataRepository(session)

    listing = await repository.get_listing("does-not-exist")

    assert listing == {}


@pytest.mark.asyncio
async def test_count_uses_discovered_foreign_key() -> None:
    session = FakeSession(
        [
            FakeResult(
                rows=[
                    ("id",),
                    ("listing_id",),
                ]
            ),
            FakeResult(scalar_value=17),
        ]
    )

    repository = PredictionDataRepository(session)

    count = await repository.count_for_subject(
        table_name="listing_views",
        subject_id="listing-1",
    )

    assert count == 17

    assert len(session.sql) == 2
    assert ":subject_id" in session.sql[1]
