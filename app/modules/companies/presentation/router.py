from app.modules.companies.presentation.schemas import CompanyCreateRequest
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.shared.security import get_current_user, require_permission
from app.modules.companies.presentation.dependencies import get_company_service
from app.modules.companies.domain.service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/")
async def get_all(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service)
):
    return await service.get_all(
        owner_id=current_user.get("id"),
        role=current_user.get("role", "user")
    )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create(
    data: CompanyCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: CompanyService = Depends(get_company_service)
):
    return await service.create(data, current_user["id"])

@router.get("/{id}")
async def get_by_id(
    id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: CompanyService = Depends(get_company_service)
):
    result = service.get_by_id(id, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="Company not found or access denied")
    return result

@router.put("/{id}")
async def update(
    id: int,
    data: CompanyCreateRequest,
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: CompanyService = Depends(get_company_service)
):
    result = service.update(id, data, current_user.get("id"), current_user.get("role", "user"))
    if not result:
        raise HTTPException(status_code=404, detail="Company not found or access denied")
    return result

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    id: int,
    current_user: Dict[str, Any] = Depends(require_permission("write_own")),
    service: CompanyService = Depends(get_company_service)
):
    if not service.delete(id, current_user.get("id"), current_user.get("role", "user")):
        raise HTTPException(status_code=404, detail="Company not found or access denied")
    return None
