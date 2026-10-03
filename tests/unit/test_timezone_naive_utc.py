"""Regression tests: governance timestamp columns are TIMESTAMP WITHOUT TIME ZONE.

Postgres (asyncpg) odmieta tz-aware datetime na stlpcoch bez timezone. Vsetky
zapisove cesty preto musia normalizovat cez to_naive_utc().

Historicky bug: control_repository.save_state() normalizoval len INSERT vetvu,
UPDATE vetva priradila tz-aware hodnotu priamo -> prva zmena rezimu presla,
druha padla na asyncpg. Rovnako approval_repository nikdy neukladal
decided_at (parameter neexistoval).

Preco fake session a nie SQLite:
SQLite (aiosqlite) tz-aware datetime pri zapise ticho odstrihne na naive a
SQLAlchemy po commite atribut expiruje/re-loadne. DB test by teda presiel aj s
bugom -> NIE je mutation-senzitivny (overene experimentalne). Fake session
zachyti presne tu Python hodnotu, ktora ide do DBAPI, takze odstranenie
to_naive_utc() test zhodi.
"""

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.agent_platform.domain.approval.approval_request import ApprovalRequest
from app.modules.agent_platform.domain.approval.approval_status import ApprovalStatus
from app.modules.agent_platform.domain.control.control_mode import ControlMode
from app.modules.agent_platform.domain.control.emergency_state import EmergencyState
from app.modules.agent_platform.infrastructure.models import (
    ApprovalRequestModel,
    ControlStateModel,
)
from app.modules.agent_platform.infrastructure.persistence.approval_repository import (
    SqlAlchemyApprovalRepository,
)
from app.modules.agent_platform.infrastructure.persistence.control_repository import (
    SqlAlchemyControlRepository,
)

pytestmark = pytest.mark.unit

_AT = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


class _FakeSession:
    """Minimal AsyncSession double used by the repositories under test.

    Repozitare volaju iba get()/add()/commit()/rollback(). get() vrati
    predpripraveny model (simuluje existujuci riadok = UPDATE vetva) alebo None
    (INSERT vetva). add() zachyti prave vytvoreny model na inspekciu.
    """

    def __init__(self, existing=None) -> None:
        self._existing = existing
        self.added: list = []
        self.committed = False

    async def get(self, model, pk):
        return self._existing

    def add(self, obj) -> None:
        self.added.append(obj)

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        return None


def _existing_control_row() -> ControlStateModel:
    """Riadok ako by ho nacitali z DB: naive hodnoty (bez timezone)."""
    return ControlStateModel(
        id=SqlAlchemyControlRepository._SINGLETON_ID,
        mode=ControlMode.NORMAL.value,
        changed_at=datetime(2026, 1, 1, 0, 0),
        changed_by="system",
        reason="init",
    )


def _state(mode: ControlMode, when: datetime) -> EmergencyState:
    return EmergencyState(mode=mode, changed_at=when, changed_by="tester", reason="test")


async def test_save_state_insert_uses_naive_datetime():
    """INSERT vetva: novy riadok musi mat naive changed_at."""
    session = _FakeSession(existing=None)
    repo = SqlAlchemyControlRepository(session)

    await repo.save_state(_state(ControlMode.NORMAL, _AT))

    assert len(session.added) == 1
    row = session.added[0]
    assert row.changed_at.tzinfo is None, "INSERT vetva musi zapisovat naive UTC"
    assert row.changed_at == _AT.replace(tzinfo=None)


async def test_save_state_update_uses_naive_datetime():
    """Regression: UPDATE vetva (druha zmena rezimu) musi tiez normalizovat.

    Toto je presny bug z produkcie: INSERT mal to_naive_utc, UPDATE nie.
    Ak sa to_naive_utc() z UPDATE vetvy odstrani, tento test PADNE.
    """
    existing = _existing_control_row()
    session = _FakeSession(existing=existing)
    repo = SqlAlchemyControlRepository(session)

    later = _AT + timedelta(hours=3)
    await repo.save_state(_state(ControlMode.READ_ONLY, later))

    assert session.added == []  # UPDATE vetva, ziadny INSERT
    assert existing.changed_at.tzinfo is None, "UPDATE vetva musi zapisovat naive UTC"
    assert existing.changed_at == later.replace(tzinfo=None)
    assert existing.mode == ControlMode.READ_ONLY.value


async def test_control_repository_get_state_returns_aware():
    """Read-path: domain validacia vyzaduje tz-aware changed_at."""
    session = _FakeSession(existing=_existing_control_row())
    repo = SqlAlchemyControlRepository(session)

    state = await repo.get_state()

    assert state.changed_at.tzinfo is not None
    assert state.mode is ControlMode.NORMAL


def _existing_approval_row() -> ApprovalRequestModel:
    return ApprovalRequestModel(
        approval_id="tz-existing",
        requested_by="tester",
        requested_by_type="user",
        action="do_thing",
        target=None,
        reason="test",
        risk_level="low",
        status=ApprovalStatus.PENDING.value,
        created_at=datetime(2026, 1, 1, 0, 0),
        expires_at=datetime(2026, 1, 2, 0, 0),
    )


async def test_approval_repository_decided_at_is_naive():
    """decided_at musi byt naive, rovnako ako created_at/expires_at.

    Ak sa normalizacia decided_at odstrani, tento test PADNE.
    """
    existing = _existing_approval_row()
    session = _FakeSession(existing=existing)
    repo = SqlAlchemyApprovalRepository(session)

    decided = _AT + timedelta(minutes=5)
    await repo.update_status("tz-existing", ApprovalStatus.APPROVED, decided_at=decided)

    assert existing.decided_at is not None
    assert existing.decided_at.tzinfo is None, "decided_at musi byt naive UTC"
    assert existing.decided_at == decided.replace(tzinfo=None)
    assert existing.status == ApprovalStatus.APPROVED.value


async def test_approval_repository_create_normalizes_timestamps():
    """create() normalizuje created_at aj expires_at (guard proti regresii)."""
    session = _FakeSession(existing=None)
    repo = SqlAlchemyApprovalRepository(session)

    await repo.create(
        ApprovalRequest(
            approval_id="tz-new",
            requested_by="tester",
            requested_by_type="user",
            action="do_thing",
            target=None,
            reason="test",
            risk_level="low",
            created_at=_AT,
            expires_at=_AT + timedelta(days=1),
            status=ApprovalStatus.PENDING,
        )
    )

    assert len(session.added) == 1
    row = session.added[0]
    assert row.created_at.tzinfo is None
    assert row.expires_at.tzinfo is None


async def test_approval_repository_read_returns_aware():
    """Read-path: domain validacia vyzaduje tz-aware created_at/expires_at."""
    session = _FakeSession(existing=_existing_approval_row())
    repo = SqlAlchemyApprovalRepository(session)

    got = await repo.get("tz-existing")

    assert got is not None
    assert got.created_at.tzinfo is not None
    assert got.expires_at.tzinfo is not None
