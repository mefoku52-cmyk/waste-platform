"""
Legacy compatibility router for documents module.

Authoritative router lives in app.modules.documents.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.documents.presentation.router import router

__all__ = ["router"]
