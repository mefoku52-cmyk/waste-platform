"""Fixtures for integration tests (shared cleanup of seeded rows)."""

import pytest

from tests.integration._company_helpers import cleanup_created


@pytest.fixture(autouse=True)
async def _cleanup_seeded_companies():
    """Po každom teste uprac firmy a nadväzné riadky vytvorené testom."""
    yield
    await cleanup_created()
