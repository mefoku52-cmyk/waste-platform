from app.shared.application.side_effects import write_audit
from app.shared.infrastructure.db.session import get_db_session
"""listings API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from app.shared.presentation.auth_dependencies import require_current_user

from app.shared.domain.exceptions import NotFoundDomainError, ValidationDomainError

from ..application.services import ListingsService
from ..domain.entities import ListingsEntity
from ..domain.enums import ListingsStatus
from .dependencies import get_listings_service
from .schemas import (
    ListingCreateRequest,
    ListingData,
    ListingResponse,
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
        status=entity.status.value,
        companyId=entity.company_id,
        description=entity.description,
        imageUrl=getattr(entity, "image_url", None),
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedListingsResponse)
async def list_listings(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    company_ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    company_ids = [cid for cid in company_ids if cid is not None]
    items = await service.list_all(page, limit, company_ids=company_ids)
    total = await service.count_all(company_ids=company_ids)
    return PaginatedListingsResponse(
        items=[_to_listing_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get("/marketplace", response_model=PaginatedListingsResponse)
async def list_marketplace(
    page: int = 1,
    limit: int = 20,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    company_ids = [
        (m.get("companyId") if isinstance(m, dict) else getattr(m, "companyId", None))
        for m in (current_user.memberships or [])
    ]
    company_ids = [cid for cid in company_ids if cid is not None]
    items = await service.list_marketplace(page, limit, exclude_company_ids=company_ids)
    total = await service.count_marketplace(exclude_company_ids=company_ids)
    return PaginatedListingsResponse(
        items=[_to_listing_data(e) for e in items],
        meta=PaginationMeta(page=page, pageSize=limit, total=total),
    )


@router.get("/{id}", response_model=ListingResponse)
async def get_listing(id: str, service: ListingsService = Depends(get_listings_service)):
    entity = await service.get_by_id(id)
    if entity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return ListingResponse(data=_to_listing_data(entity))


@router.post("/", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
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
    try:
        created = await service.create(entity)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return ListingResponse(data=_to_listing_data(created))


@router.put("/{id}", response_model=ListingResponse)
async def update_listing(
    id: str,
    request: ListingUpdateRequest,
    service: ListingsService = Depends(get_listings_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if request.status is not None and str(request.status).lower() == "published":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Na publikáciu použi POST /listings/{id}/publish (vyžaduje verified firmu).",
        )
    updated_entity = ListingsEntity(
        title=request.title if request.title is not None else existing.title,
        material_type=request.materialType if request.materialType is not None else existing.material_type,
        quantity=request.quantity if request.quantity is not None else existing.quantity,
        unit=request.unit if request.unit is not None else existing.unit,
        price=request.price if request.price is not None else existing.price,
        currency=request.currency if request.currency is not None else existing.currency,
        condition=request.condition if request.condition is not None else existing.condition,
        location=request.location if request.location is not None else existing.location,
        status=ListingsStatus(request.status) if request.status is not None else existing.status,
        company_id=existing.company_id,
        description=request.description if request.description is not None else existing.description,
        image_url=request.imageUrl if getattr(request, "imageUrl", None) is not None else getattr(existing, "image_url", None),
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return ListingResponse(data=_to_listing_data(result))



@router.post("/{id}/publish", response_model=ListingResponse)
async def publish_listing(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
    session=Depends(get_db_session),
):
    """Publikovať smie len overená (verified) firma vlastníca ponuky."""
    try:
        result = await service.publish(id)
    except ValidationDomainError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message) from exc
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
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



@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(id: str, service: ListingsService = Depends(get_listings_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
