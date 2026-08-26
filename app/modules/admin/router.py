"""
Legacy compatibility router for admin module.

Authoritative router lives in app.modules.admin.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.admin.presentation.router import router

__all__ = ["router"]
