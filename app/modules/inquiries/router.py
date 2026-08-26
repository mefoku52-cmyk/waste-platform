"""
Legacy compatibility router for inquiries module.

Authoritative router lives in app.modules.inquiries.presentation.router.
This file exists only to preserve older import paths.
"""

from app.modules.inquiries.presentation.router import router

__all__ = ["router"]
