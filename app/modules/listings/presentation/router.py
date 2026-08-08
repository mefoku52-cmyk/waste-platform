"""listings API router."""

from fastapi import APIRouter, Depends, HTTPException, status

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
        createdAt=entity.created_at,
        updatedAt=entity.updated_at,
    )


@router.get("/", response_model=PaginatedListingsResponse)
async def list_listings(
    page: int = 1,
    limit: int = 20,
    service: ListingsService = Depends(get_listings_service),
):
    items = await service.list_all(page, limit)
    total = await service.count_all()
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
    )
    try:
        result = await service.update(id, updated_entity)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ValidationDomainError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc
    return ListingResponse(data=_to_listing_data(result))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(id: str, service: ListingsService = Depends(get_listings_service)):
    try:
        await service.delete(id)
    except NotFoundDomainError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
