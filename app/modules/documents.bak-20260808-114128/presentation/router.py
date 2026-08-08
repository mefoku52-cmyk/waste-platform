"""documents API router."""

from fastapi import APIRouter, Depends
from typing import List

from .schemas import DocumentsResponse, DocumentsCreateRequest, DocumentsUpdateRequest
from ..application.services import DocumentsService
from ..infrastructure.repositories import DocumentsRepositoryImpl

router = APIRouter(prefix="/documents", tags=["documents"])


def get_service():
    """Get documents service."""
    # TODO: Implement dependency injection
    pass


@router.get("/", response_model=List[DocumentsResponse])
async def list_documents(page: int = 1, limit: int = 20):
    """List all documents."""
    # TODO: Implement
    return []


@router.get("/{id}", response_model=DocumentsResponse)
async def get_documents(id: str):
    """Get documents by ID."""
    # TODO: Implement
    pass


@router.post("/", response_model=DocumentsResponse)
async def create_documents(request: DocumentsCreateRequest):
    """Create new documents."""
    # TODO: Implement
    pass


@router.put("/{id}", response_model=DocumentsResponse)
async def update_documents(id: str, request: DocumentsUpdateRequest):
    """Update documents."""
    # TODO: Implement
    pass


@router.delete("/{id}")
async def delete_documents(id: str):
    """Delete documents."""
    # TODO: Implement
    pass
