import asyncio
import inspect

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import is_platform_admin

router = APIRouter(prefix="/api/v1/ops", tags=["operations"])


def private_response(payload, status_code=200):
    return JSONResponse(
        content=payload,
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


async def call_existing(request, name, path):
    matches = [
        route
        for route in request.app.routes
        if getattr(route, "path", None) == path
        and getattr(route, "name", None) == name
        and "GET" in (getattr(route, "methods", None) or set())
    ]

    if len(matches) != 1:
        return {"status": "unverified"}, 503

    try:
        result = matches[0].endpoint()

        if inspect.isawaitable(result):
            result = await asyncio.wait_for(result, timeout=8)

        if isinstance(result, JSONResponse):
            import json

            data = json.loads(result.body)
            status = result.status_code
        elif isinstance(result, dict):
            data = result
            status = 200
        else:
            return {"status": "unverified"}, 503

        if not isinstance(data, dict):
            return {"status": "unverified"}, 503

        return data, status

    except Exception:
        return {"status": "unverified"}, 503


@router.get("/health")
async def public_health(request: Request):
    data, code = await call_existing(request, "health", "/health")
    healthy = code == 200 and data.get("status") == "ok"

    return private_response(
        {"status": "ok" if healthy else "unavailable"},
        200 if healthy else 503,
    )


@router.get("/ready")
async def public_ready(request: Request):
    data, code = await call_existing(request, "ready", "/ready")
    ready = code == 200 and data.get("status") == "ready"

    return private_response(
        {"status": "ready" if ready else "not-ready"},
        200 if ready else 503,
    )


@router.get("/details")
async def admin_details(
    request: Request,
    current_user=Depends(require_current_user),
):
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform admin required")

    health, health_code = await call_existing(request, "health", "/health")
    ready, ready_code = await call_existing(request, "ready", "/ready")

    return private_response(
        {
            "health": {"http": health_code, "data": health},
            "readiness": {"http": ready_code, "data": ready},
        },
        200 if health_code == 200 and ready_code == 200 else 503,
    )
