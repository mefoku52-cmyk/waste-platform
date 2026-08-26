"""
Legacy compatibility router for notifications module.

Authoritative router lives in app.modules.notifications.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.notifications.presentation.router import router

__all__ = ["router"]
