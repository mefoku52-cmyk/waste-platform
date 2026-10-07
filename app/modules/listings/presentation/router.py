"""listings API router."""

from fastapi import APIRouter, Depends, Query, status
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.presentation.dependencies import (
    get_entitlement_service,
)
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import ConflictDomainError, NotFoundDomainError
from app.shared.infrastructure.db.session import get_db_session
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
    require_company_member,
)
from app.shared.presentation.error_schemas import error_responses

from ..application.services import ListingsService
from ..domain.entities import ListingsEntity
from .dependencies import get_listings_service
from .schemas import (
    AiDraftRequest,
    AiDraftResponse,
    ListingCreateRequest,
    ListingData,
    ListingResponse,
    ListingStatsResponse,
    ListingUpdateRequest,
    PaginatedListingsResponse,
    PaginationMeta,
    PromoteListingRequest,
    PromoteListingResponse,
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
        promotedUntil=getattr(entity, "promoted_until", None),
        promotedTier=getattr(entity, "promoted_tier", None),
    )


def _membership_company_ids(current_user) -> list:
    """Company IDs clenstva (stringova forma) — jedina zdielana definicia."""
    return membership_company_ids(current_user)


@router.post(
    "/ai-draft",
    response_model=AiDraftResponse,
    responses=error_responses(400, 401, 403, 409, 422, 500),
)
async def ai_draft_listing(
    payload: AiDraftRequest,
    current_user=Depends(require_current_user),
    entitlement=Depends(get_entitlement_service),
):
    """AI draft ponuky — vyžaduje AI tier firmy.

    Bez AI tier → 409. Bez GROQ_API_KEY → deterministický fallback.
    """
    from app.modules.companies.domain.enums import SubscriptionTier
    from app.modules.listings.presentation.schemas import (
        AiDraftData,
        AiDraftResponse,
    )

    # Zisti firmu (z payload alebo prvej membership)
    from app.shared.presentation.authorization import membership_company_ids

    from ..application.listing_drafter import (
        ListingDrafter,
    )

    if payload.companyId:
        company_id = str(payload.companyId)
    else:
        my_ids = membership_company_ids(current_user)
        if not my_ids:
            raise ConflictDomainError("Nemáš firmu — najprv ju vytvor.")
        company_id = str(my_ids[0])
        # Multi-company robustness: uprednostni prvú firmu s AI tierom.
        for candidate in my_ids:
            if await entitlement.has_tier(str(candidate), SubscriptionTier.AI):
                company_id = str(candidate)
                break

    has_ai = await entitlement.has_tier(company_id, SubscriptionTier.AI)
    if not has_ai:
        raise ConflictDomainError("AI draft je dostupný iba pre firmy s AI predplatným.")

    drafter = ListingDrafter()
    provider = "groq" if drafter.is_provider_configured() else "fallback"
    draft = await drafter.draft(prompt=payload.prompt)

    return AiDraftResponse(
        data=AiDraftData(
            title=draft.title,
            description=draft.description,
            materialType=draft.materialType,
            quantity=draft.quantity,
            unit=draft.unit,
            location=draft.location,
            condition=draft.condition,
            currency=draft.currency,
            price=draft.price,
        ),
        provider=provider,
    )


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
    uid = current_user_id(current_user)
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
    responses=error_responses(401, 403, 404, 500),
)
async def get_listing(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    entity = await service.get_by_id(id)
    if entity is None:
        raise NotFoundDomainError(f"Listing {id} not found")

    # Neverejny (nepublikovany) inzerat vidi len jeho firma alebo platform admin.
    is_public = str(getattr(entity.status, "value", entity.status)) == "published"
    if not is_public and not is_platform_admin(current_user):
        require_company_member(current_user, entity.company_id, action="access")

    return ListingResponse(data=_to_listing_data(entity))


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 409, 422, 500),
)
async def create_listing(
    request: ListingCreateRequest,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    require_company_member(current_user, request.companyId, action="create listings for")
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
    responses=error_responses(401, 403, 404, 409, 422, 500),
)
async def update_listing(
    id: str,
    request: ListingUpdateRequest,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {id} not found")

    require_company_admin(current_user, existing.company_id)

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
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {id} not found")
    require_company_admin(current_user, existing.company_id)

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
        actor = current_user_id(current_user)
        await write_audit(
            session=session,
            actor_user_id=actor,
            action="listing.published",
            target_type="listing",
            target_id=id,
            details=f"title={getattr(result, 'title', '')}",
        )
    except Exception:
        pass  # best-effort: never break caller

    return ListingResponse(data=_to_listing_data(result))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404, 500),
)
async def delete_listing(
    id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
):
    existing = await service.get_by_id(id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {id} not found")
    require_company_admin(current_user, existing.company_id)
    await service.delete(id)


@router.post(
    "/{listing_id}/promote",
    response_model=PromoteListingResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def promote_listing(
    listing_id: str,
    payload: PromoteListingRequest,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
    session: AsyncSession = Depends(get_db_session),
):
    """Zvýrazní ponuku (owner only). Top = 7/30 dní, Gold = 30 dní."""
    existing = await service.get_by_id(listing_id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {listing_id} not found")

    # Authorization: iba vlastník (alebo admin)
    if not is_platform_admin(current_user):
        my_companies = {str(x) for x in _membership_company_ids(current_user)}
        if str(existing.company_id) not in my_companies:
            raise ConflictDomainError("Nemáš oprávnenie topovať túto ponuku.")

    await service.promote(listing_id, days=payload.days, tier=payload.tier)
    updated = await service.get_by_id(listing_id)

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="listing.promote",
        target_type="listing",
        target_id=listing_id,
        details=f"days={payload.days},tier={payload.tier}",
    )

    return PromoteListingResponse(
        ok=True,
        promotedUntil=getattr(updated, "promoted_until", None),
        promotedTier=getattr(updated, "promoted_tier", None),
    )


@router.post(
    "/{listing_id}/unpromote",
    response_model=PromoteListingResponse,
    responses=error_responses(401, 403, 404, 422, 500),
)
async def unpromote_listing(
    listing_id: str,
    current_user=Depends(require_current_user),
    service: ListingsService = Depends(get_listings_service),
    session: AsyncSession = Depends(get_db_session),
):
    """Zruší zvýraznenie ponuky (owner only)."""
    existing = await service.get_by_id(listing_id)
    if existing is None:
        raise NotFoundDomainError(f"Listing {listing_id} not found")

    if not is_platform_admin(current_user):
        my_companies = {str(x) for x in _membership_company_ids(current_user)}
        if str(existing.company_id) not in my_companies:
            raise ConflictDomainError("Nemáš oprávnenie.")

    await service.unpromote(listing_id)
    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="listing.unpromote",
        target_type="listing",
        target_id=listing_id,
    )
    return PromoteListingResponse(ok=True)
