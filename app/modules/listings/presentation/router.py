"""listings API router."""

from fastapi import APIRouter, Depends, Query, status
from fastapi import status as http_status

from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import ConflictDomainError, NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.error_schemas import error_responses

from ..application.services import ListingsService
from ..domain.entities import ListingsEntity
from .dependencies import get_listings_service
from .schemas import (
    ListingCreateRequest,
    ListingData,
    ListingResponse,
    ListingStatsResponse,
    ListingUpdateRequest,
    PaginatedListingsResponse,
    PaginationMeta,
)

router = APIRouter(prefix="/listings", tags=["listings"])


def _to_listing_data(entity: ListingsEntity) -> ListingData:
    return ListingData(
        id=entity.id,
        title=entity.title,
        materialType=entity.material_type,
        quantity=entity.quantity,
        unit=entity.unit,
        price=entity.price,
        currency=entity.currency,
        condition=entity.condition,
        location=entity.location,
        status=entity.status,
        companyId=entity.company_id,
        description=entity.description,
        imageUrl=getattr(entity, "image_url", None),
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


def _membership_company_ids(current_user) -> list:
    company_ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    return [cid for cid in company_ids if cid is not None]


@router.get(
    "",
    response_model=PaginatedListingsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_listings(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    effective_page_size = limit or pageSize
    company_ids = _membership_company_ids(current_user)
    items = await service.list_all(page, effective_page_size, company_ids=company_ids)
    total = await service.count_all(company_ids=company_ids)
    return PaginatedListingsResponse(
        items=[_to_listing_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=effective_page_size, total=total),
    )


@router.get(
    "/marketplace",
    response_model=PaginatedListingsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_marketplace(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    effective_page_size = limit or pageSize
    company_ids = _membership_company_ids(current_user)
    items = await service.list_marketplace(
        page, effective_page_size, exclude_company_ids=company_ids
    )
    total = await service.count_marketplace(exclude_company_ids=company_ids)
    return PaginatedListingsResponse(
        items=[_to_listing_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=effective_page_size, total=total),
    )


@router.get(
    "/matches",
    response_model=PaginatedListingsResponse,
    responses=error_responses(401, 403, 422, 500),
)
async def list_matches(
    materialType: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=20, ge=1, le=100),
    limit: int | None = Query(default=None, ge=1, le=100, include_in_schema=False),
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    effective_page_size = limit or pageSize
    company_ids = _membership_company_ids(current_user)
    items = await service.find_matches(
        material_type=materialType,
        exclude_company_ids=company_ids,
        limit=effective_page_size * page,
    )
    start = (page - 1) * effective_page_size
    slice_items = items[start : start + effective_page_size]
    return PaginatedListingsResponse(
        items=[_to_listing_data(e) for e in slice_items],
        meta=PaginationMeta(page=page, pageSize=effective_page_size, total=len(items)),
    )


@router.post(
    "/{id}/view",
    status_code=http_status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404, 500),
)
async def record_listing_view(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    """Zapise jedno zobrazenie ponuky prihlasenym userom. Pouziva frontend pri otvoreni detailu."""
    uid = getattr(getattr(current_user, "user", None), "id", None) or getattr(
        current_user, "id", None
    )
    if uid is None:
        return None
    await service.record_view(id, uid)
    return None


@router.get(
    "/{id}/stats",
    response_model=ListingStatsResponse,
    responses=error_responses(401, 403, 404, 500),
)
async def get_listing_stats(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    """Vrati pocet zobrazeni a unikatnych divakov. Len pre vlastnika."""
    company_ids = _membership_company_ids(current_user)
    stats = await service.get_stats(id, owner_company_ids=company_ids)
    return ListingStatsResponse(**stats)


@router.get(
    "/{id}",
    response_model=ListingResponse,
    responses=error_responses(404, 500),
)
async def get_listing(id: str, service: ListingsService = Depends(get_listings_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Listing {id} not found")
    return ListingResponse(data=_to_listing_data(entity))


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409, 422, 500),
)
async def create_listing(
    request: ListingCreateRequest,
    service: ListingsService = Depends(get_listings_service),
):
    entity = ListingsEntity(
        title=request.title,
        material_type=request.materialType,
        quantity=request.quantity,
        unit=request.unit,
        price=request.price,
        currency=request.currency,
        condition=request.condition,
        location=request.location,
        company_id=str(request.companyId),
        description=request.description,
        image_url=getattr(request, "imageUrl", None),
    )
    created = await service.create(entity)
    return ListingResponse(data=_to_listing_data(created))


@router.patch(
    "/{id}",
    response_model=ListingResponse,
    responses=error_responses(404, 409, 422, 500),
)
async def update_listing(
    id: str,
    request: ListingUpdateRequest,
    service: ListingsService = Depends(get_listings_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {id} not found")

    if request.status is not None and request.status.value == "published":
        raise ConflictDomainError("Listing publication must use POST /api/v1/listings/{id}/publish")

    updated_entity = ListingsEntity(
        title=request.title if request.title is not None else existing.title,
        material_type=request.materialType
        if request.materialType is not None
        else existing.material_type,
        quantity=request.quantity if request.quantity is not None else existing.quantity,
        unit=request.unit if request.unit is not None else existing.unit,
        price=request.price if request.price is not None else existing.price,
        currency=request.currency if request.currency is not None else existing.currency,
        condition=request.condition if request.condition is not None else existing.condition,
        location=request.location if request.location is not None else existing.location,
        status=request.status if request.status is not None else existing.status,
        company_id=existing.company_id,
        description=request.description
        if request.description is not None
        else existing.description,
        image_url=request.imageUrl
        if getattr(request, "imageUrl", None) is not None
        else getattr(existing, "image_url", None),
    )
    result = await service.update(id, updated_entity)
    return ListingResponse(data=_to_listing_data(result))


@router.post(
    "/{id}/publish",
    response_model=ListingResponse,
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def publish_listing(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
    session=Depends(get_db_session),
):
    try:
        result = await service.publish(id)
    except NotFoundDomainError:
        raise
    except Exception as exc:
        msg = str(exc)
        if "verified" in msg.lower() or "publikovať" in msg.lower():
            raise ConflictDomainError(msg) from exc
        raise

    try:
        u = getattr(current_user, "user", None)
        actor = getattr(u, "id", None) if u is not None else getattr(current_user, "id", None)
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="listing.published",
            target_type="listing",
            target_id=id,
            details=f"title={getattr(result, 'title', '')}",
        )
    except Exception:
        pass

    return ListingResponse(data=_to_listing_data(result))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404, 500),
)
async def delete_listing(id: str, service: ListingsService = Depends(get_listings_service)):
    await service.delete(id)
