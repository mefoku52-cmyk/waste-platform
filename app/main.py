from __future__ import annotations

from contextlib import asynccontextmanager
import importlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.http_exception_handlers import register_http_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url="/docs" if settings.ENABLE_PUBLIC_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_PUBLIC_DOCS else None,
        openapi_url="/openapi.json" if settings.ENABLE_PUBLIC_DOCS else None,
        root_path=settings.ROOT_PATH or "",
        lifespan=lifespan,
    )

    register_http_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }

    mounted = []

    try:
        from app.shared.presentation.api_router import api_router

        pref = getattr(api_router, "prefix", "") or ""
        if pref.startswith("/api"):
            app.include_router(api_router)
        else:
            app.include_router(api_router, prefix="/api/v1")
        mounted.append("shared.api_router")
    except Exception as e:
        print(f"[main] shared.api_router skip: {e}")

        module_routers = [
            "app.modules.auth.presentation.router",
            "app.modules.users.presentation.router",
            "app.modules.companies.presentation.router",
            "app.modules.company_memberships.presentation.router",
            "app.modules.listings.presentation.router",
            "app.modules.inquiries.presentation.router",
            "app.modules.documents.presentation.router",
            "app.modules.compliance.presentation.router",
            "app.modules.notifications.presentation.router",
            "app.modules.analytics.presentation.router",
            "app.modules.admin.presentation.router",
            "app.modules.uploads.presentation.router",
        ]

        for mod_path in module_routers:
            tag = mod_path.split(".")[2]
            try:
                mod = importlib.import_module(mod_path)
                router = getattr(mod, "router", None)
                if router is not None:
                    app.include_router(router, prefix="/api/v1")
                    mounted.append(tag)
            except Exception as ex:
                print(f"[main] module {tag} skip: {ex}")

    app.state.mounted_routers = mounted
    return app


app = create_app()
