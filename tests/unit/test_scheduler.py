"""Testy scheduler.py — bez reálneho spustenia taskov.

APScheduler beží v testoch iba na overenie registrácie a lifecycle.
Wrapper funkcie (delete_user, backfill) sú mockované na source module.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.core.config import settings
from app.shared.infrastructure import scheduler as sch


@pytest.fixture
def clean_scheduler():
    """Izolovaný scheduler pre každý test."""
    # ensure no global instance leak
    sch._scheduler = None
    yield
    sch._scheduler = None


@pytest.mark.asyncio
async def test_scheduler_starts_cleanly(clean_scheduler):
    """start_scheduler() zaregistruje joby bez chyby."""
    sch.start_scheduler()
    sched = sch._scheduler
    assert sched is not None
    assert sched.running is True
    sch.stop_scheduler()
    # stop_scheduler() hneď zahodí global; shutdown je queued cez @run_in_event_loop
    assert sch._scheduler is None
    await asyncio.sleep(0)
    assert sched.running is False


@pytest.mark.asyncio
async def test_shutdown_stops_scheduler(clean_scheduler):
    """stop_scheduler() ukončí scheduler po flush event loopu."""
    sch.start_scheduler()
    sched = sch._scheduler
    assert sched is not None
    assert sched.running is True
    sch.stop_scheduler()
    await asyncio.sleep(0)
    assert sched.running is False
    assert sch._scheduler is None


@pytest.mark.asyncio
async def test_jobs_registered(clean_scheduler):
    """start_scheduler() zaregistruje defaultne 3 joby s očakávanými ID."""
    sch.start_scheduler()
    sched = sch._scheduler
    assert sched is not None
    jobs = {j.id: j for j in sched.get_jobs()}
    # Reálne ID z kódu. daily_matching je podmienený MATCHING_ENABLED.
    expected_ids = {
        "lead_discover_12h",
        "cleanup_pending_users",
        "daily_lead_outreach",
    }
    assert expected_ids.issubset(set(jobs.keys()))
    if getattr(settings, "MATCHING_ENABLED", False):
        assert "daily_matching" in jobs
    else:
        assert "daily_matching" not in jobs
    sch.stop_scheduler()
    await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_job_max_instances_is_one(clean_scheduler):
    """Jeden job nemôže bežať dvakrát paralelne."""
    sch.start_scheduler()
    sched = sch._scheduler
    assert sched is not None
    for job in sched.get_jobs():
        assert job.max_instances == 1
    sch.stop_scheduler()
    await asyncio.sleep(0)


# --- Error handling + wrappers ------------------------------------------


@pytest.mark.asyncio
async def test_invalid_cron_expression_raises(clean_scheduler, monkeypatch):
    """Nesprávny cron výraz musí zlyhať pri registrácii."""
    from apscheduler.triggers.cron import CronTrigger

    with pytest.raises(ValueError):
        CronTrigger(hour=99, minute=0)


class _FakeResult:
    def __init__(self, ids):
        self._ids = ids

    def all(self):
        return [(i,) for i in self._ids]


class _FakeSession:
    def __init__(self, ids):
        self._ids = ids

    async def execute(self, stmt, *args, **kwargs):
        return _FakeResult(self._ids)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.mark.asyncio
async def test_wrapper_cleanup_deletes_stale_users(clean_scheduler, monkeypatch):
    """_cleanup_pending_users_wrapper zavolá DeleteUserService pre každé id.

    Reálne meno wrappera je _cleanup_pending_users_wrapper (nie
    _run_cleanup_pending_users). Bez id-ov z DB je wrapper no-op, takže
    treba podstrčiť aj fake session factory.
    """
    from app.modules.users.application import services as user_services
    from app.shared.infrastructure.db import session as dbsession

    monkeypatch.setattr(dbsession, "async_session_factory", lambda: _FakeSession([101, 202]))

    delete_service = AsyncMock()
    monkeypatch.setattr(user_services, "DeleteUserService", lambda *a, **kw: delete_service)

    await sch._cleanup_pending_users_wrapper()

    assert delete_service.execute.await_count == 2
    assert [c.kwargs["user_id"] for c in delete_service.execute.await_args_list] == [
        101,
        202,
    ]
