"""
Legacy compatibility router for compliance module.

Authoritative router lives in app.modules.compliance.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.compliance.presentation.router import router

__all__ = ["router"]
