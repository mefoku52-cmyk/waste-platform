"""Unit tests for the audit/notification side-effect helpers.

Both helpers are deliberately *best effort*: they must never propagate an error
into the request that triggered them. These tests pin the guard clauses, the
recipient fan-out, and the error-swallowing behaviour.

The helpers import their collaborators lazily inside the function body, so the
patch targets are the attributes on the implementation modules.
"""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from app.modules.admin.domain.entities import AdminAuditEntryEntity
from app.modules.admin.domain.enums import AdminAuditEntryStatus
from app.shared.application import side_effects

ADMIN_REPO_PATH = "app.modules.admin.infrastructure.repositories.AdminAuditEntryRepositoryImpl"
MEMBERSHIP_REPO_PATH = (
    "app.modules.company_memberships.infrastructure.repositories."
    "SqlAlchemyCompanyMembershipRepository"
)
NOTIFICATION_REPO_PATH = (
    "app.modules.notifications.infrastructure.repositories.NotificationRepositoryImpl"
)


class _RecordingRepo:
    """Drop-in repository that records created entities instead of persisting."""

    def __init__(self, sink, session=None):
        self.sink = sink

    async def create(self, entity):
        self.sink.append(entity)
        return entity


class _BoomRepo:
    def __init__(self, session=None):
        pass

    async def create(self, entity):
        raise RuntimeError("backend unavailable")


class _Member:
    def __init__(self, user_id):
        self.user_id = user_id


@pytest.fixture
def audit_sink(monkeypatch):
    sink = []
    monkeypatch.setattr(ADMIN_REPO_PATH, lambda session: _RecordingRepo(sink, session))
    return sink


@pytest.fixture
def notif_sink(monkeypatch):
    sink = []
    monkeypatch.setattr(NOTIFICATION_REPO_PATH, lambda session: _RecordingRepo(sink, session))
    return sink


def _members(monkeypatch, *user_ids):
    monkeypatch.setattr(
        MEMBERSHIP_REPO_PATH,
        lambda session: MagicMock(
            list_by_company_id=_async_returning([_Member(u) for u in user_ids])
        ),
    )


def _async_returning(value):
    async def _inner(*args, **kwargs):
        return value

    return _inner


# --------------------------------------------------------------------------
# write_audit
# --------------------------------------------------------------------------


async def test_write_audit_skips_when_actor_is_none(audit_sink):
    await side_effects.write_audit(session=None, actor_user_id=None, action="a", target_type="t")

    assert audit_sink == []


@pytest.mark.parametrize("actor", ["", 0, None])
async def test_write_audit_skips_falsy_actor(audit_sink, actor):
    """An empty string actor must not produce an orphan audit row."""
    await side_effects.write_audit(session=None, actor_user_id=actor, action="a", target_type="t")

    assert audit_sink == []


async def test_write_audit_persists_success_entry(audit_sink):
    actor = uuid4()

    await side_effects.write_audit(
        session=None,
        actor_user_id=actor,
        action="listing.publish",
        target_type="listing",
    )

    assert len(audit_sink) == 1
    entry = audit_sink[0]
    assert isinstance(entry, AdminAuditEntryEntity)
    assert entry.actor_user_id == actor
    assert entry.action == "listing.publish"
    assert entry.target_type == "listing"
    assert entry.status is AdminAuditEntryStatus.SUCCESS


async def test_write_audit_coerces_string_ids_to_uuid(audit_sink):
    actor = uuid4()
    target = uuid4()

    await side_effects.write_audit(
        session=None,
        actor_user_id=str(actor),
        action="a",
        target_type="t",
        target_id=str(target),
    )

    entry = audit_sink[0]
    assert isinstance(entry.actor_user_id, UUID)
    assert entry.actor_user_id == actor
    assert entry.target_id == target


async def test_write_audit_keeps_none_target_id(audit_sink):
    await side_effects.write_audit(session=None, actor_user_id=uuid4(), action="a", target_type="t")

    assert audit_sink[0].target_id is None


async def test_write_audit_passes_details_and_timestamps(audit_sink):
    await side_effects.write_audit(
        session=None,
        actor_user_id=uuid4(),
        action="a",
        target_type="t",
        details="extra context",
    )

    entry = audit_sink[0]
    assert entry.details == "extra context"
    assert isinstance(entry.created_at, datetime)


async def test_write_audit_swallows_backend_errors(monkeypatch):
    monkeypatch.setattr(ADMIN_REPO_PATH, _BoomRepo)

    # Must not raise: audit failures cannot break the triggering request.
    await side_effects.write_audit(session=None, actor_user_id=uuid4(), action="a", target_type="t")


# --------------------------------------------------------------------------
# notify_company_members
# --------------------------------------------------------------------------


async def test_notify_skips_when_company_id_missing(notif_sink):
    await side_effects.notify_company_members(session=None, company_id=None, title="T", message="M")

    assert notif_sink == []


async def test_notify_skips_for_empty_company_id(notif_sink):
    await side_effects.notify_company_members(session=None, company_id="", title="T", message="M")

    assert notif_sink == []


async def test_notify_fans_out_to_every_member(monkeypatch, notif_sink):
    u1, u2 = uuid4(), uuid4()
    _members(monkeypatch, u1, u2)

    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="Novy dopyt", message="Mate dopyt"
    )

    assert [n.user_id for n in notif_sink] == [u1, u2]
    assert all(n.title == "Novy dopyt" for n in notif_sink)
    assert all(n.is_read is False for n in notif_sink)


async def test_notify_applies_default_type(monkeypatch, notif_sink):
    _members(monkeypatch, uuid4())

    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="T", message="M"
    )

    assert notif_sink[0].type == "inquiry_received"


async def test_notify_honours_explicit_type(monkeypatch, notif_sink):
    _members(monkeypatch, uuid4())

    await side_effects.notify_company_members(
        session=None,
        company_id=uuid4(),
        title="T",
        message="M",
        notif_type="company_verified",
    )

    assert notif_sink[0].type == "company_verified"


async def test_notify_excludes_requested_user(monkeypatch, notif_sink):
    u1, u2 = uuid4(), uuid4()
    _members(monkeypatch, u1, u2)

    await side_effects.notify_company_members(
        session=None,
        company_id=uuid4(),
        title="T",
        message="M",
        exclude_user_id=u1,
    )

    assert [n.user_id for n in notif_sink] == [u2]


async def test_notify_excludes_user_given_as_string(monkeypatch, notif_sink):
    u1, u2 = uuid4(), uuid4()
    _members(monkeypatch, u1, u2)

    await side_effects.notify_company_members(
        session=None,
        company_id=uuid4(),
        title="T",
        message="M",
        exclude_user_id=str(u1),
    )

    assert [n.user_id for n in notif_sink] == [u2]


async def test_notify_truncates_long_messages(monkeypatch, notif_sink):
    _members(monkeypatch, uuid4())

    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="T", message="x" * 5000
    )

    assert len(notif_sink[0].message) == 2000


async def test_notify_skips_members_without_user_id(monkeypatch, notif_sink):
    member_without_user = _Member(None)
    member_with_user = _Member(uuid4())
    monkeypatch.setattr(
        MEMBERSHIP_REPO_PATH,
        lambda session: MagicMock(
            list_by_company_id=_async_returning([member_without_user, member_with_user])
        ),
    )

    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="T", message="M"
    )

    assert [n.user_id for n in notif_sink] == [member_with_user.user_id]


async def test_notify_carries_related_entity_id(monkeypatch, notif_sink):
    _members(monkeypatch, uuid4())
    related = uuid4()

    await side_effects.notify_company_members(
        session=None,
        company_id=uuid4(),
        title="T",
        message="M",
        related_entity_id=related,
    )

    assert notif_sink[0].related_entity_id == related


async def test_notify_produces_no_rows_for_empty_membership(monkeypatch, notif_sink):
    _members(monkeypatch)
    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="T", message="M"
    )

    assert notif_sink == []


async def test_notify_swallows_backend_errors(monkeypatch):
    _members(monkeypatch, uuid4())
    monkeypatch.setattr(NOTIFICATION_REPO_PATH, _BoomRepo)

    # Must not raise: a notification failure cannot break the request.
    await side_effects.notify_company_members(
        session=None, company_id=uuid4(), title="T", message="M"
    )


# --------------------------------------------------------------------------
# write_audit — Bug B: non-UUID target_id (email) must not drop the row
# --------------------------------------------------------------------------


async def test_write_audit_email_target_does_not_raise(audit_sink):
    """target_id='x@y.sk' must not blow up UUID coercion (BUG-02/B)."""
    actor = uuid4()

    await side_effects.write_audit(
        session=None,
        actor_user_id=actor,
        action="lead_outreach.send",
        target_type="email",
        target_id="x@y.sk",
        details="via=resend",
    )

    # 1 insert happened — the row is not swallowed by a ValueError.
    assert len(audit_sink) == 1


async def test_write_audit_email_target_moves_value_to_details(audit_sink):
    await side_effects.write_audit(
        session=None,
        actor_user_id=uuid4(),
        action="lead_outreach.send",
        target_type="email",
        target_id="x@y.sk",
        details="via=resend",
    )

    entry = audit_sink[0]
    assert isinstance(entry, AdminAuditEntryEntity)
    # UUID column cannot hold the email → stored as None, value preserved in details.
    assert entry.target_id is None
    assert "x@y.sk" in (entry.details or "")
    assert "via=resend" in (entry.details or "")


async def test_write_audit_invalid_uuid_string_does_not_raise(audit_sink):
    await side_effects.write_audit(
        session=None,
        actor_user_id=uuid4(),
        action="a",
        target_type="t",
        target_id="not-a-uuid",
    )

    assert len(audit_sink) == 1
    assert audit_sink[0].target_id is None


async def test_write_audit_valid_uuid_string_still_coerces(audit_sink):
    """Regression guard: the safe path must not break real UUID targets."""
    target = uuid4()

    await side_effects.write_audit(
        session=None,
        actor_user_id=uuid4(),
        action="a",
        target_type="t",
        target_id=str(target),
        details="keep",
    )

    entry = audit_sink[0]
    assert entry.target_id == target
    # Valid UUID → details untouched (no target_raw prefix).
    assert entry.details == "keep"


# --------------------------------------------------------------------------
# write_activity_event
# --------------------------------------------------------------------------


class _EventSinkSession:
    def __init__(self):
        self.added = []
        self.committed = 0

    def add(self, row):
        self.added.append(row)

    async def commit(self):
        self.committed += 1


async def test_write_activity_event_adds_row():
    from app.modules.events.infrastructure.models import ActivityEventModel

    session = _EventSinkSession()

    await side_effects.write_activity_event(
        session=session,
        event_type="lead_outreach.send",
        actor_user_id=str(uuid4()),
        payload="to=x@y.sk",
    )

    assert len(session.added) == 1
    row = session.added[0]
    assert isinstance(row, ActivityEventModel)
    assert row.event_type == "lead_outreach.send"
    assert row.payload == "to=x@y.sk"
    assert session.committed == 1


async def test_write_activity_event_swallows_backend_errors():
    class _Boom:
        def add(self, row):
            raise RuntimeError("db down")

        async def commit(self):
            raise RuntimeError("db down")

    # Must not raise: the daily-limit counter must never break a send.
    await side_effects.write_activity_event(
        session=_Boom(),
        event_type="lead_outreach.send",
    )
