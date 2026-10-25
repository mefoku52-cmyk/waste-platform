"""Test admin analytics stats endpoint."""

import pytest

from app.modules.analytics.presentation.router import get_admin_stats


class DummyUser:
    def __init__(self, email="admin@trc-cmep.sk", role_codes=None):
        self.id = "00000000-0000-0000-0000-000000000000"
        self.email = email
        self.role_codes = role_codes or ["platform_admin"]
        self.roles = []
        self.memberships = []


@pytest.mark.asyncio
async def test_get_admin_stats_returns_structure(db_session):
    user = DummyUser()
    res = await get_admin_stats(days=30, current_user=user, session=db_session)
    assert isinstance(res, dict)
    for key in [
        "total",
        "today",
        "yesterday",
        "week",
        "month",
        "uniqueToday",
        "daily",
        "topSources",
    ]:
        assert key in res
    assert isinstance(res["daily"], dict)
    assert isinstance(res["topSources"], list)
