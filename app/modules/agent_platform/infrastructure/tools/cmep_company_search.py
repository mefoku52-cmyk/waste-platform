"""CMEP adapter for the Agent Platform company-search port."""

from __future__ import annotations

from app.modules.agent_platform.application.tools.company_search import (
    CompanySearchItem,
    CompanySearchResult,
)


class CMEPCompanySearchAdapter:
    """Adapts the existing CMEP company service to CompanySearchPort.

    CMEP remains the owner of company business logic and persistence.
    This adapter only translates the application contract.
    """

    def __init__(self, *, service):
        self._service = service

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
    ) -> CompanySearchResult:
        items, total = await self._service.execute(
            status=status,
            company_type=company_type,
            seller_capability=seller_capability,
            buyer_capability=buyer_capability,
            logistics_capability=logistics_capability,
            q=q,
            page=page,
            page_size=page_size,
            company_ids=(None if company_ids is None else list(company_ids)),
        )

        return CompanySearchResult(
            items=tuple(self._to_item(item) for item in items),
            total=total,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _to_item(item) -> CompanySearchItem:
        return CompanySearchItem(
            id=str(item.id),
            legal_name=item.legal_name,
            trading_name=item.trading_name,
            registration_number=item.registration_number,
            company_type=item.company_type,
            status=item.status,
        )
