"""Round-trip tests for conversation memory + rolling summary storage.

Uses an in-memory SQLite DB with only the two AI tables — no network, no
production data. Verifies backward compatibility (summary lives in the existing
ai_messages table; no migration) and that only one summary row ever exists.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.modules.agent_platform.infrastructure.models import (
    AiConversationModel,
    AiMessageModel,
)
from app.modules.agent_platform.infrastructure.persistence.ai_conversation_repository import (
    SqlAlchemyAiConversationRepository,
)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(AiConversationModel.__table__.create)
        await conn.run_sync(AiMessageModel.__table__.create)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _seed(repo: SqlAlchemyAiConversationRepository) -> str:
    conv = await repo.get_or_create(session_id="s1", user_id=uuid.uuid4(), company_id=None)
    return conv.id


@pytest.mark.asyncio
async def test_count_ignores_summary_rows(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)
    cid = await _seed(repo)
    assert await repo.count_messages(conversation_id=cid) == 0

    await repo.append_message(conversation_id=cid, role="user", content="ahoj")
    await repo.append_message(conversation_id=cid, role="assistant", content="cau")
    assert await repo.count_messages(conversation_id=cid) == 2

    await repo.replace_summary(conversation_id=cid, content="sum", meta={"covers": 2})
    assert await repo.count_messages(conversation_id=cid) == 2


@pytest.mark.asyncio
async def test_summary_roundtrip_and_replace(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)
    cid = await _seed(repo)
    assert await repo.get_summary(conversation_id=cid) is None

    await repo.replace_summary(
        conversation_id=cid,
        content="prve zhrnutie",
        meta={"covers": 5, "lang": "sk"},
    )
    got = await repo.get_summary(conversation_id=cid)
    assert got is not None
    assert got.content == "prve zhrnutie"
    assert got.covers == 5
    assert got.language == "sk"

    # Replacing must keep exactly one summary row.
    await repo.replace_summary(conversation_id=cid, content="druhe zhrnutie", meta={"covers": 9})
    got2 = await repo.get_summary(conversation_id=cid)
    assert got2 is not None
    assert got2.content == "druhe zhrnutie"
    assert got2.covers == 9

    rows = await repo.get_messages(conversation_id=cid, limit=50)
    summary_rows = [r for r in rows if r.role == "summary"]
    assert len(summary_rows) == 1


@pytest.mark.asyncio
async def test_invalid_conversation_id_is_safe(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)
    assert await repo.count_messages(conversation_id="not-a-uuid") == 0
    assert await repo.get_summary(conversation_id="not-a-uuid") is None
    assert await repo.replace_summary(conversation_id="not-a-uuid", content="x") is None


# N2 contract: get_or_create must normalise user_id/company_id to UUIDs so the
# repository works on both Postgres (asyncpg) and SQLite (aiosqlite), regardless
# of whether callers pass uuid objects, uuid strings or None.


@pytest.mark.asyncio
async def test_get_or_create_accepts_uuid_object(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)
    uid = uuid.uuid4()
    cid = uuid.uuid4()

    conv = await repo.get_or_create(session_id="s-obj", user_id=uid, company_id=cid)

    assert conv.id
    assert conv.user_id == str(uid)
    assert conv.company_id == str(cid)


@pytest.mark.asyncio
async def test_get_or_create_accepts_uuid_string(session) -> None:
    # Regression for N2: previously a string user_id crashed on SQLite
    # ("'str' object has no attribute 'hex'") while working on Postgres.
    repo = SqlAlchemyAiConversationRepository(session)
    uid = str(uuid.uuid4())
    cid = str(uuid.uuid4())

    conv = await repo.get_or_create(session_id="s-str", user_id=uid, company_id=cid)

    assert conv.user_id == uid
    assert conv.company_id == cid


@pytest.mark.asyncio
async def test_get_or_create_company_id_none(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)

    conv = await repo.get_or_create(session_id="s-none", user_id=str(uuid.uuid4()), company_id=None)

    assert conv.company_id is None


@pytest.mark.asyncio
async def test_get_or_create_same_session_is_idempotent(session) -> None:
    repo = SqlAlchemyAiConversationRepository(session)
    uid = str(uuid.uuid4())

    first = await repo.get_or_create(session_id="s-dup", user_id=uid, company_id=None)
    second = await repo.get_or_create(session_id="s-dup", user_id=uid, company_id=None)

    assert second.id == first.id


@pytest.mark.asyncio
async def test_get_or_create_rejects_missing_user_id(session) -> None:
    # user_id is NOT NULL and must be a valid UUID — the repository must not
    # silently persist an empty/invalid owner (N2 contract).
    repo = SqlAlchemyAiConversationRepository(session)
    with pytest.raises(IntegrityError):
        await repo.get_or_create(session_id="s-bad", user_id=None, company_id=None)
