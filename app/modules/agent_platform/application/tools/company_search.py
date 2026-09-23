"""Application contract for searching CMEP companies.

This module belongs to the Agent Platform boundary.

The contract deliberately does not expose CMEP DTOs, ORM models,
repositories, SQLAlchemy objects, or presentation-layer response types.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CompanySearchItem:
    """Agent Platform-neutral company search result."""

    id: str
    legal_name: str
    trading_name: str | None = None
    registration_number: str | None = None
    company_type: str | None = None
    status: str | None = None


@dataclass(frozen=True, slots=True)
class CompanySearchResult:
    """Agent Platform-neutral paginated company search result."""

    items: tuple[CompanySearchItem, ...]
    total: int
    page: int
    page_size: int


class CompanySearchPort(Protocol):
    """Port from Agent Platform to the existing CMEP company service.

    Authorization scope is supplied by the trusted application boundary.
    Tool arguments must never be used to manufacture or expand that scope.
    """

    async def search(
        self,
        *,
        status: str | None,
        company_type: str | None,
        seller_capability: bool | None,
        buyer_capability: bool | None,
        logistics_capability: bool | None,
        q: str | None,
        page: int,
        page_size: int,
        company_ids: tuple[str, ...] | None,
    ) -> CompanySearchResult: ...
