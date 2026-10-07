"""Local file upload API (dev-friendly; later swap to MinIO)."""

from __future__ import annotations

import mimetypes
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.modules.documents.application.services import DocumentService
from app.modules.documents.presentation.dependencies import get_documents_service
from app.modules.uploads.application.signing import (
    DEFAULT_TTL_SECONDS,
    sign_file_url,
    verify_file_url,
)
from app.shared.presentation.auth_dependencies import (
    get_current_user_optional,
    require_current_user,
)
from app.shared.presentation.error_schemas import error_responses

from .schemas import UploadResponse

router = APIRouter(prefix="/uploads", tags=["uploads"], redirect_slashes=False)

APP_DATA_DIR = os.getenv("APP_DATA_DIR", "/var/data")
UPLOAD_ROOT = Path(APP_DATA_DIR) / "uploads"

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
ALLOWED_MIME = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
}
MAX_BYTES = 8 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


async def _authorize_document_file(
    file_id: str,
    current_user,
    service: DocumentService,
) -> None:
    document_url = f"/api/v1/uploads/{file_id}"
    document = await service.get_by_file_url(document_url)

    # Ak Document záznam neexistuje, file_id je capability: 32-znakový UUID
    # (neuhádnuteľný) + auth + podpis s expiráciou stačia. Upload endpoint
    # pre listing fotky Document nevytvára, takže bez tohto fallbacku by
    # každý listing obrázok padal na 404 a frontend by zobrazil
    # "podpis fotky zlyhal".
    if document is None:
        return

    status_value = getattr(document.status, "value", document.status)

    # Approved documents are public to authenticated platform users.
    if status_value == "approved":
        return

    # Platform administrators may access every document state.
    from app.shared.presentation.authorization import is_platform_admin

    if is_platform_admin(current_user):
        return

    # Pending/rejected documents require membership in the owning company.
    from app.shared.presentation.authorization import membership_company_ids

    allowed_company_ids = membership_company_ids(current_user)

    if document.company_id not in allowed_company_ids:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this document",
        )


def _validate_file_id(file_id: str) -> str:
    safe = Path(file_id).name
    if safe != file_id or ".." in file_id or "/" in file_id or "\\" in file_id:
        raise HTTPException(status_code=400, detail="Invalid file id")

    suffix = Path(safe).suffix.lower()
    stem = Path(safe).stem
    if suffix not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file extension")
    if len(stem) != 32 or any(c not in "0123456789abcdef" for c in stem.lower()):
        raise HTTPException(status_code=400, detail="Invalid file id format")
    return safe


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(400, 401, 403, 422, 500),
)
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(require_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported type {suffix}. Allowed: {sorted(ALLOWED_EXT)}",
        )

    if file.content_type:
        allowed_for_ext = ALLOWED_MIME.get(suffix, set())
        if allowed_for_ext and file.content_type not in allowed_for_ext:
            raise HTTPException(
                status_code=400,
                detail=f"Content type {file.content_type} does not match extension {suffix}",
            )

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    file_id = f"{uuid.uuid4().hex}{suffix}"
    dest = UPLOAD_ROOT / file_id

    total = 0
    try:
        with dest.open("wb") as out:
            while True:
                chunk = await file.read(CHUNK_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    raise HTTPException(status_code=400, detail="File too large (max 8MB)")
                out.write(chunk)
    except HTTPException:
        dest.unlink(missing_ok=True)
        raise
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    return UploadResponse(
        fileId=file_id,
        url=f"/api/v1/uploads/{file_id}",
        originalName=file.filename,
        size=total,
        contentType=file.content_type,
    )


class SignedUrlResponse(BaseModel):
    fileId: str
    urlPath: str
    expiresAt: int


@router.post(
    "/{file_id}/sign",
    response_model=SignedUrlResponse,
    responses=error_responses(400, 401, 403, 404, 500),
)
async def sign_uploaded_file(
    file_id: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    current_user=Depends(require_current_user),
    document_service: DocumentService = Depends(get_documents_service),
):
    """Generate a short-lived signed URL for a file.

    Any authenticated user can sign — the raw UUID is the capability
    (you must know it), auth adds a layer, signature adds expiry.
    """
    safe = _validate_file_id(file_id)
    path = UPLOAD_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    await _authorize_document_file(
        file_id=safe,
        current_user=current_user,
        service=document_service,
    )

    signed = sign_file_url(
        file_id=safe,
        secret=settings.uploads_signing_secret,
        ttl_seconds=ttl_seconds,
    )

    return SignedUrlResponse(
        fileId=signed["file_id"],
        urlPath=f"/api/v1{signed['url_path']}",
        expiresAt=signed["expires_at"],
    )


@router.get(
    "/{file_id}",
    responses=error_responses(400, 403, 404, 500),
)
async def get_uploaded_file(
    file_id: str,
    expires: int | None = Query(default=None),
    sig: str | None = Query(default=None),
    current_user=Depends(get_current_user_optional),
    document_service: DocumentService = Depends(get_documents_service),
):
    """Serve file — signed URL obíde auth, priamy prístup vyžaduje Bearer.

    Browser <img src> nevie poslať Authorization header. Ak je platný
    `?sig=...&expires=...`, file_id je capability (32-znakový UUID) a podpis
    s expiráciou stačí. Bez sign sa vyžaduje auth.
    """
    safe = _validate_file_id(file_id)

    # Skús signed URL cestu najprv (bez auth)
    signed_ok = False
    if sig and expires is not None:
        ok, _reason = verify_file_url(
            file_id=safe,
            secret=settings.uploads_signing_secret,
            expires_at=expires,
            signature=sig,
        )
        if ok:
            signed_ok = True

    # Ak nie je signed OK, vyžaduj auth
    if not signed_ok:
        if current_user is None:
            from app.shared.domain.exceptions import UnauthorizedDomainError

            raise UnauthorizedDomainError("Authentication required")

        await _authorize_document_file(
            file_id=safe,
            current_user=current_user,
            service=document_service,
        )

        if settings.UPLOADS_REQUIRE_SIGNED:
            raise HTTPException(
                status_code=403,
                detail="Signed URL required",
            )

    path = UPLOAD_ROOT / safe
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    media_type, _ = mimetypes.guess_type(str(path))
    filename = path.name

    response = FileResponse(
        path,
        media_type=media_type or "application/octet-stream",
        filename=filename,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "private, max-age=3600"
    response.headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response


@router.get(
    "/files/{file_id}",
    include_in_schema=False,
)
async def get_uploaded_file_legacy(
    file_id: str,
    current_user=Depends(get_current_user_optional),
    document_service: DocumentService = Depends(get_documents_service),
):
    return await get_uploaded_file(
        file_id=file_id,
        current_user=current_user,
        document_service=document_service,
    )
