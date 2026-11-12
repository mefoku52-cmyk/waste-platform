"""Integracne testy modulu inspections (sluzba + repos + stavovy stroj).

Pouziva realne modely v hermetickej SQLite (conftest) a vola routery priamo
(vzor test_admin_analytics_stats) — tak sa testuje auth + servis + DB.
"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.core.config import settings
from app.modules.inspections.application.services import InspectionService
from app.modules.inspections.infrastructure.models import InspectionEventModel, InspectionModel
from app.modules.listings.infrastructure.models import ListingsModel
from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)

SECRET = "test-streaming-secret-0123456789abcdef0123456789"
INTERNAL_KEY = "test-internal-key-0123456789abcdef"


class _Member:
    def __init__(self, company_id):
        self.companyId = str(company_id)


class _User:
    def __init__(self, user_id, memberships):
        self.id = str(user_id)
        self.email = "t@example.com"
        self.isPlatformAdmin = False
        self.memberships = memberships
        self.roleCodes = []


@pytest.fixture(autouse=True)
def _settings(monkeypatch):
    monkeypatch.setattr(settings, "CMEP_STREAMING_SIGNING_SECRET", SECRET)
    monkeypatch.setattr(settings, "CMEP_STREAMING_PUBLIC_URL", "http://127.0.0.1:8504")
    monkeypatch.setattr(settings, "CMEP_INTERNAL_API_KEY", INTERNAL_KEY)
    yield


async def _seed_listing(db_session, company_id, status="published"):
    row = ListingsModel(
        id=uuid4(),
        title="Šrot oceľ",
        material_type="steel",
        quantity=100.0,
        unit="t",
        condition="used",
        location="Bratislava",
        status=status,
        company_id=company_id,
    )
    db_session.add(row)
    await db_session.commit()
    return row


async def _seed_thread(db_session, listing_id, owner_user, owner_company, viewer_user, viewer_company):
    from app.modules.chat.infrastructure.models import ChatThreadModel

    row = ChatThreadModel(
        id=uuid4(),
        listing_id=listing_id,
        initiator_user_id=viewer_user,
        initiator_company_id=viewer_company,
        recipient_user_id=owner_user,
        recipient_company_id=owner_company,
        subject="Obhliadka",
        last_message_at=datetime.now(),
    )
    db_session.add(row)
    await db_session.commit()
    return row


@pytest.fixture
def svc(db_session):
    from app.modules.inspections.infrastructure.repositories import (
        InspectionEventRepositoryImpl,
        InspectionRepositoryImpl,
    )

    return InspectionService(
        db_session,
        InspectionRepositoryImpl(db_session),
        InspectionEventRepositoryImpl(db_session),
    )


async def test_create_inspection_owner_mints_publisher_token(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    result = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    assert result["role"] == "publisher"
    assert result["inspection"].state.value == "created"
    assert f"offer={result['inspection'].id}" in result["publishUrl"]
    assert "token=" in result["publishUrl"]


async def test_create_inspection_non_member_forbidden(svc, db_session):
    company, other_company, owner = uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    with pytest.raises(ForbiddenDomainError):
        await svc.create_inspection(
            user_id=owner, company_ids=[str(other_company)], listing_id=listing.id
        )


async def test_create_second_active_inspection_conflict(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await svc.create_inspection(user_id=owner, company_ids=[str(company)], listing_id=listing.id)
    with pytest.raises(ConflictDomainError):
        await svc.create_inspection(user_id=owner, company_ids=[str(company)], listing_id=listing.id)


async def test_join_requires_counterpart_thread(svc, db_session):
    company, owner, stranger, stranger_co = uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id

    # Viewer bez chat vlakna -> forbidden
    with pytest.raises(ForbiddenDomainError):
        await svc.join_inspection(
            user_id=stranger,
            company_ids=[str(stranger_co)],
            inspection_id=insp_id,
            wait_room_seconds=0,
        )

    # Viewer zo spolocnosti vlastnika -> nie je viewer
    with pytest.raises(ValidationDomainError):
        await svc.join_inspection(
            user_id=owner, company_ids=[str(company)], inspection_id=insp_id, wait_room_seconds=0
        )


async def test_join_before_room_created_conflict(svc, db_session):
    company, owner, viewer, viewer_co = uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await _seed_thread(db_session, listing.id, owner, company, viewer, viewer_co)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    with pytest.raises(ConflictDomainError):
        await svc.join_inspection(
            user_id=viewer,
            company_ids=[str(viewer_co)],
            inspection_id=created["inspection"].id,
            wait_room_seconds=0,
        )


async def test_full_state_machine_and_room_id_flow(svc, db_session):
    company, owner, viewer, viewer_co = uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await _seed_thread(db_session, listing.id, owner, company, viewer, viewer_co)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id

    # join pred room -> conflict, ale po evente createRoom uz prejde
    room_id = "room-abc-123"
    ev1 = await svc.record_event(
        internal_key=INTERNAL_KEY,
        event_uid=str(uuid4()),
        inspection_id=insp_id,
        event_type="inspection_requested",
        actor_sub=str(owner),
        room_id=room_id,
        role="owner",
    )
    assert ev1["recorded"] is True
    assert ev1["state"] == "room_created"

    joined = await svc.join_inspection(
        user_id=viewer,
        company_ids=[str(viewer_co)],
        inspection_id=insp_id,
        wait_room_seconds=0,
    )
    assert joined["role"] == "viewer"
    assert f"room={room_id}" in joined["viewerUrl"]
    assert joined["inspection"].viewer_user_id == viewer
    assert joined["inspection"].viewer_company_id == viewer_co

    # opakovany join toho iste viewera je OK (rejoin)
    rejoined = await svc.join_inspection(
        user_id=viewer, company_ids=[str(viewer_co)], inspection_id=insp_id, wait_room_seconds=0
    )
    assert rejoined["inspection"].viewer_user_id == viewer

    # eventy: viewer poziada, publisher schvali, live, end
    for ev_type, role, actor, expected in [
        ("inspection_requested", "viewer", viewer, "requested"),
        ("inspection_accepted", "owner", owner, "accepted"),
        ("inspection_started", "viewer", viewer, "live"),
        ("inspection_ended", "owner", owner, "ended"),
    ]:
        res = await svc.record_event(
            internal_key=INTERNAL_KEY,
            event_uid=str(uuid4()),
            inspection_id=insp_id,
            event_type=ev_type,
            actor_sub=str(actor),
            room_id=room_id,
            role=role,
        )
        assert res["recorded"] is True
        assert res["state"] == expected


async def test_event_idempotency_duplicate_uid(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    uid = str(uuid4())
    first = await svc.record_event(
        internal_key=INTERNAL_KEY,
        event_uid=uid,
        inspection_id=insp_id,
        event_type="inspection_requested",
        actor_sub=str(owner),
        room_id="room-x",
        role="owner",
    )
    second = await svc.record_event(
        internal_key=INTERNAL_KEY,
        event_uid=uid,
        inspection_id=insp_id,
        event_type="inspection_requested",
        actor_sub=str(owner),
        room_id="room-x",
        role="owner",
    )
    assert first["recorded"] is True and first["state"] == "room_created"
    assert second["recorded"] is False and second["duplicate"] is True

    from sqlalchemy import select

    rows = (
        (await db_session.execute(
            select(InspectionEventModel).where(InspectionEventModel.event_uid == uid)
        ))
        .scalars()
        .all()
    )
    assert len(rows) == 1


async def test_event_unknown_type_and_bad_key(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    with pytest.raises(ForbiddenDomainError):
        await svc.record_event(
            internal_key="wrong",
            event_uid=str(uuid4()),
            inspection_id=insp_id,
            event_type="inspection_started",
        )
    with pytest.raises(ValidationDomainError):
        await svc.record_event(
            internal_key=INTERNAL_KEY,
            event_uid=str(uuid4()),
            inspection_id=insp_id,
            event_type="hacked_event",
        )
    with pytest.raises(NotFoundDomainError):
        await svc.record_event(
            internal_key=INTERNAL_KEY,
            event_uid=str(uuid4()),
            inspection_id=uuid4(),
            event_type="inspection_started",
        )


async def test_verify_for_streaming_fail_closed(svc, db_session):
    company, owner, viewer, viewer_co = uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await _seed_thread(db_session, listing.id, owner, company, viewer, viewer_co)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id

    # zly kluc
    with pytest.raises(ForbiddenDomainError):
        await svc.verify_for_streaming(
            internal_key="bad", inspection_id=insp_id, sub=str(owner), role="publisher"
        )
    # publisher: zly sub
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(viewer), role="publisher"
    )
    assert res["ok"] is False and res["reason"] == "not_publisher"
    # publisher: spravny sub
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(owner), role="publisher"
    )
    assert res["ok"] is True and res["consentToRecord"] is False

    # viewer overenie az po join-e (priradenie viewera)
    await svc.record_event(
        internal_key=INTERNAL_KEY,
        event_uid=str(uuid4()),
        inspection_id=insp_id,
        event_type="inspection_requested",
        actor_sub=str(owner),
        room_id="room-zz",
        role="owner",
    )
    await svc.join_inspection(
        user_id=viewer,
        company_ids=[str(viewer_co)],
        inspection_id=insp_id,
        wait_room_seconds=0,
    )
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(viewer), role="viewer"
    )
    assert res["ok"] is True
    # iny viewer neexistuje
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(uuid4()), role="viewer"
    )
    assert res["ok"] is False and res["reason"] == "not_viewer"


async def test_verify_after_end_is_not_ok(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    await svc.end_inspection(user_id=owner, company_ids=[str(company)], inspection_id=insp_id)
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(owner), role="publisher"
    )
    assert res["ok"] is False and res["reason"] == "inspection_ended"


async def test_recording_consent_owner_only(svc, db_session):
    company, owner, viewer, viewer_co = uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await _seed_thread(db_session, listing.id, owner, company, viewer, viewer_co)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    with pytest.raises(ForbiddenDomainError):
        await svc.set_recording_consent(
            user_id=viewer, company_ids=[str(viewer_co)], inspection_id=insp_id
        )
    res = await svc.set_recording_consent(
        user_id=owner, company_ids=[str(company)], inspection_id=insp_id
    )
    assert res["inspection"].consent_to_record is True

    token = svc.tokens.mint(
        user_id=owner,
        company_id=company,
        inspection_id=insp_id,
        listing_id=listing.id,
        role="publisher",
        consent_to_record=res["inspection"].consent_to_record,
    )
    from app.modules.inspections.application.streaming_tokens import verify_streaming_token_self

    assert verify_streaming_token_self(token.token)["rec"] == 1


async def test_publisher_link_reissues_url(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    link = await svc.publisher_link(user_id=owner, company_ids=[str(company)], inspection_id=insp_id)
    assert link["role"] == "publisher"
    assert f"offer={insp_id}" in link["publishUrl"]
    with pytest.raises(NotFoundDomainError):
        await svc.publisher_link(user_id=owner, company_ids=[str(company)], inspection_id=uuid4())


async def test_end_inspection_sets_ended(svc, db_session):
    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    ended = await svc.end_inspection(user_id=owner, company_ids=[str(company)], inspection_id=insp_id)
    assert ended["inspection"].state.value == "ended"
    # Idempotencia: opakovane ukoncenie uz ukoncenej obhliadky je uspesne
    # (miestnost uz zanikla odchodom publishra) — nie konflikt.
    again = await svc.end_inspection(user_id=owner, company_ids=[str(company)], inspection_id=insp_id)
    assert again["inspection"].state.value == "ended"


async def test_active_inspection_visibility(svc, db_session):

    company, owner, viewer, viewer_co, outsider, outsider_co = uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    await _seed_thread(db_session, listing.id, owner, company, viewer, viewer_co)
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id

    # owner vidi
    res = await svc.active_inspection_for_listing(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    assert res["inspection"].id == insp_id and res["canPublish"] is True

    # viewer (counterpart) vidi existujucu obhliadku a moze sa joinovat
    res = await svc.active_inspection_for_listing(
        user_id=viewer, company_ids=[str(viewer_co)], listing_id=listing.id
    )
    assert res["inspection"].id == insp_id and res["canJoin"] is True

    # outsider nevidi nic
    with pytest.raises(NotFoundDomainError):
        await svc.active_inspection_for_listing(
            user_id=outsider, company_ids=[str(outsider_co)], listing_id=listing.id
        )

    # po join-e viewer vidi
    await svc.record_event(
        internal_key=INTERNAL_KEY,
        event_uid=str(uuid4()),
        inspection_id=insp_id,
        event_type="inspection_requested",
        actor_sub=str(owner),
        room_id="room-v",
        role="owner",
    )
    await svc.join_inspection(
        user_id=viewer,
        company_ids=[str(viewer_co)],
        inspection_id=insp_id,
        wait_room_seconds=0,
    )
    res = await svc.active_inspection_for_listing(
        user_id=viewer, company_ids=[str(viewer_co)], listing_id=listing.id
    )
    assert res["inspection"].id == insp_id and res["isViewer"] is True


async def test_end_inspection_calls_streaming_client(db_session):
    """Ukoncenie obhliadky zavola streamovaciu sluzbu (zrušenie miestnosti)."""
    from app.modules.inspections.infrastructure.repositories import (
        InspectionEventRepositoryImpl,
        InspectionRepositoryImpl,
    )

    calls = []

    class FakeStreaming:
        async def end_inspection(self, inspection_id):
            calls.append(str(inspection_id))
            return True

    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    svc = InspectionService(
        db_session,
        InspectionRepositoryImpl(db_session),
        InspectionEventRepositoryImpl(db_session),
        FakeStreaming(),
    )
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    ended = await svc.end_inspection(
        user_id=owner, company_ids=[str(company)], inspection_id=insp_id
    )
    assert ended["inspection"].state.value == "ended"
    assert calls == [str(insp_id)]


async def test_end_inspection_tolerates_streaming_failure(db_session):
    """Streaming chyba nezbráni ukončeniu obhliadky na platforme (best-effort)."""
    from app.modules.inspections.infrastructure.repositories import (
        InspectionEventRepositoryImpl,
        InspectionRepositoryImpl,
    )

    class BrokenStreaming:
        async def end_inspection(self, inspection_id):
            raise RuntimeError("streaming down")

    company, owner = uuid4(), uuid4()
    listing = await _seed_listing(db_session, company)
    svc = InspectionService(
        db_session,
        InspectionRepositoryImpl(db_session),
        InspectionEventRepositoryImpl(db_session),
        BrokenStreaming(),
    )
    created = await svc.create_inspection(
        user_id=owner, company_ids=[str(company)], listing_id=listing.id
    )
    insp_id = created["inspection"].id
    ended = await svc.end_inspection(
        user_id=owner, company_ids=[str(company)], inspection_id=insp_id
    )
    assert ended["inspection"].state.value == "ended"
    # verify fail-closed po ukončení
    res = await svc.verify_for_streaming(
        internal_key=INTERNAL_KEY, inspection_id=insp_id, sub=str(owner), role="publisher"
    )
    assert res["ok"] is False
