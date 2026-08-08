from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routerov
from app.modules.auth.presentation.router import router as auth_router
from app.modules.users.presentation.router import router as users_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import router as memberships_router
from app.modules.admin.presentation.router import router as admin_router
from app.modules.analytics.presentation.router import router as analytics_router
from app.modules.compliance.presentation.router import router as compliance_router
from app.modules.documents.presentation.router import router as documents_router
from app.modules.inquiries.presentation.router import router as inquiries_router
from app.modules.listings.presentation.router import router as listings_router
from app.modules.notifications.presentation.router import router as notifications_router

# Import databázy
from app.shared.database.db import engine, Base
from app.shared.database.migrations import create_tables

# Nastavenie logovania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vytvorenie FastAPI appky
app = FastAPI(
    title="Waste Platform API",
    description="Komplexná platforma pre správu odpadu",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API router
from app.shared.presentation.api_router import api_router
app.include_router(api_router, prefix="/api/v1")

# Health check
@app.get("/health")
async def healthcheck():
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return {"status": "ok", "service": "waste-platform"}

# Startup event - vytvorí tabuľky
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    create_tables()
    logger.info("✅ Databázové tabuľky inicializované")
    logger.info("🚀 Waste Platform API beží")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")
