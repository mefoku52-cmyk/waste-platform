"""Read-only listing to company recommendations from existing columns."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.domain.enums import CompanyStatus
from app.modules.companies.infrastructure.models import CompanyModel
from app.modules.events.infrastructure.models import ActivityEventModel
from app.modules.listings.infrastructure.models import ListingsModel
from app.modules.recommendations.application.scoring import score_company
from app.shared.domain.exceptions import NotFoundDomainError


class RecommendationsService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_listing(self, listing_id: UUID) -> dict:
        listing = await self._get_listing(listing_id)
        companies = await self._buyer_candidates(exclude_company_id=str(listing.company_id))

        hits_by_company: dict[str, int] = {}
        try:
            result = await self._session.execute(
                select(ActivityEventModel.company_id).where(
                    ActivityEventModel.listing_id == str(listing.id),
                    ActivityEventModel.company_id.is_not(None),
                )
            )
            for cid in result.scalars().all():
                key = str(cid)
                hits_by_company[key] = hits_by_company.get(key, 0) + 1
        except Exception:
            hits_by_company = {}
        items: list[dict] = []
        for company in companies:
            score, reasons = score_company(
                listing_location=listing.location,
                listing_material=listing.material_type,
                listing_lat=getattr(listing, "latitude", None),
                listing_lng=getattr(listing, "longitude", None),
                city=company.city,
                logistics_capability=bool(company.logistics_capability),
                accepted_material_types=getattr(company, "accepted_material_types", None),
                company_lat=company.latitude,
                company_lng=company.longitude,
                event_hits=hits_by_company.get(str(company.id), 0),
            )
            if score <= 0:
                continue
            items.append(
                {
                    "companyId": UUID(str(company.id)),
                    "legalName": company.legal_name,
                    "city": company.city,
                    "countryCode": company.country_code,
                    "buyerCapability": bool(company.buyer_capability),
                    "logisticsCapability": bool(company.logistics_capability),
                    "score": score,
                    "reasons": reasons,
                }
            )

        items.sort(key=lambda row: (-row["score"], row["legalName"]))
        return {
            "listingId": listing.id,
            "materialType": listing.material_type,
            "location": listing.location,
            "items": items,
        }

    async def _get_listing(self, listing_id: UUID) -> ListingsModel:
        result = await self._session.execute(
            select(ListingsModel).where(ListingsModel.id == listing_id)
        )
        listing = result.scalar_one_or_none()
        if listing is None:
            raise NotFoundDomainError("Listing not found")
        return listing

    async def _buyer_candidates(self, *, exclude_company_id: str) -> list[CompanyModel]:
        result = await self._session.execute(
            select(CompanyModel).where(
                CompanyModel.status == CompanyStatus.VERIFIED.value,
                CompanyModel.buyer_capability.is_(True),
                CompanyModel.id != exclude_company_id,
            )
        )
        return list(result.scalars().all())

    async def logistics_candidates(self, near: str = "") -> list[dict]:
        needle = (near or "").strip().casefold()
        companies = await self._buyer_candidates(exclude_company_id="")
        items: list[dict] = []
        for company in companies:
            if not bool(company.logistics_capability):
                continue
            city = company.city or ""
            if (
                needle
                and needle not in city.casefold()
                and needle not in (company.legal_name or "").casefold()
            ):
                continue
            items.append(
                {
                    "name": company.legal_name,
                    "city": company.city,
                    "lat": company.latitude,
                    "lon": company.longitude,
                    "source": "companies",
                    "osmId": str(company.id),
                }
            )
        return items
