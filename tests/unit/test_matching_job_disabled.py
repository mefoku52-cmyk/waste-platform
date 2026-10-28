import pytest

from app.modules.recommendations.application import matching_job


@pytest.mark.asyncio
async def test_run_daily_matching_disabled(monkeypatch):
    monkeypatch.setattr(matching_job.settings, "MATCHING_ENABLED", False)
    result = await matching_job.run_daily_matching(session=None)
    assert result == {"enabled": False, "companies_checked": 0, "notified": 0, "emails_sent": 0}
