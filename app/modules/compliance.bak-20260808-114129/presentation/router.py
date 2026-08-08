"""compliance API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import ComplianceResponse, ComplianceCreateRequest, ComplianceUpdateRequest
from ..application.services import ComplianceService
from ..infrastructure.repositories import ComplianceRepositoryImpl

router = APIRouter(prefix="/compliance", tags=["compliance"])


def get_service():
    """Get compliance service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[ComplianceResponse])
async def list_compliance(page: int = 1, limit: int = 20):
    """List all compliance."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=ComplianceResponse)
async def get_compliance(id: str):
    """Get compliance by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=ComplianceResponse)
async def create_compliance(request: ComplianceCreateRequest):
    """Create new compliance."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=ComplianceResponse)
async def update_compliance(id: str, request: ComplianceUpdateRequest):
    """Update compliance."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_compliance(id: str):
    """Delete compliance."""
    # TODO: Implement
    pass
