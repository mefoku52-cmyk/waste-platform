"""
Legacy compatibility router for analytics module.

Authoritative router lives in app.modules.analytics.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.analytics.presentation.router import router

__all__ = ["router"]
