"""Cross-service E2E runner for CMEP Live Inspections."""

import asyncio
import json
import os
import signal
import sys
import tempfile
import uuid
from uuid import UUID
from datetime import datetime
from pathlib import Path

# Unikatny DB subor na kazdy beh: paralelne behy (alebo zvysok z predchadzajuceho
# behu) by si delili subor a SQLite write contention by stracal eventy/stav obhliadky.
_E2E_DB = Path(tempfile.gettempdir()) / f"cmep_live_e2e_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_E2E_DB}"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-ok"
os.environ["APP_ENV"] = "test"
os.environ["REDIS_URL"] = "memory://"
os.environ["RATE_LIMIT_ENABLED"] = "false"

import uvicorn  # noqa: E402
from app.main import create_app  # noqa: E402
from app.modules.chat.infrastructure.models import ChatThreadModel  # noqa: F401
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel  # noqa: F401
from app.modules.inspections.infrastructure.models import (  # noqa: F401
    InspectionEventModel,
    InspectionModel,
)
from app.modules.listings.infrastructure.models import ListingsModel  # noqa: F401
from app.modules.users.infrastructure.models import UserModel  # noqa: F401
from app.shared.infrastructure.db import register_models  # noqa: F401
from app.shared.infrastructure.db.base import Base  # noqa: F401
from app.shared.infrastructure.db.session import async_session_factory  # noqa: F401
from app.shared.infrastructure.security.jwt_service import JwtService  # noqa: F401

APP = create_app()
TOKEN_PATH = os.environ.get(
    "E2E_TOKENS_PATH", "/data/data/com.termux/files/usr/tmp/opencode/cmep-e2e-tokens.json"
)
# Port je konfigurovatelný, aby sa E2E testy neopakovali o ten istý port
# (zvyšok z predchádzujúceho behu by inak odpovedal starou konfiguráciou).
def _resolve_port() -> int:
    """Port platformy: z E2E_PORT, inak automaticky vybrany volny port.

    Pevny port je krehky - zvysok z predchadzajuceho (zlyhaneho) behu by ho
    obsadil a dalsi beh by zlyhal na "address already in use". Automaticky
    vyber odstranuje kolizie medzi behmi.
    """
    raw = (os.environ.get("E2E_PORT") or "").strip()
    if raw.isdigit() and 1 <= int(raw) <= 65535:
        return int(raw)
    if not raw:
        # Bez E2E_PORT sa pouzije predvoleny port (dohodnutý s testom).
        return 8765
    # Neplatna hodnota (napr. 'undefined') -> automaticky vybrany volny port,
    # aby sa beh vedelo spustit namiesto padnutia na ValueError.
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])

PORT = _resolve_port()


async def seed_and_mint():
    owner_uid = str(uuid.uuid4())
    viewer_uid = str(uuid.uuid4())
    outsider_uid = str(uuid.uuid4())
    company_uuid = uuid.uuid4()
    outsider_company_uuid = uuid.uuid4()
    listing_uuid = uuid.uuid4()
    thread_uuid = uuid.uuid4()

    from sqlalchemy import delete as sa_delete

    async with async_session_factory() as session:
        from sqlalchemy.ext.asyncio import AsyncEngine
        from app.shared.infrastructure.db.base import Base  # noqa: F401
        from app.shared.infrastructure.db import register_models  # noqa: F401

        engine = session.get_bind() if hasattr(session, "get_bind") else None
        from app.shared.infrastructure.db.session import engine as _engine

        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        for tbl in (InspectionEventModel, InspectionModel, ChatThreadModel, ListingsModel, UserModel):
            await session.execute(sa_delete(tbl))
        owner = UserModel(
            id=owner_uid,
            status="active",
            email=f"owner-{owner_uid[:8]}@cmep.local",
            password_hash="x" * 64,
            first_name="Owner",
            last_name="Company",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        viewer = UserModel(
            id=viewer_uid,
            status="active",
            email=f"viewer-{viewer_uid[:8]}@cmep.local",
            password_hash="x" * 64,
            first_name="Viewer",
            last_name="Company",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        outsider = UserModel(
            id=outsider_uid,
            status="active",
            email=f"outsider-{outsider_uid[:8]}@cmep.local",
            password_hash="x" * 64,
            first_name="Outsider",
            last_name="Company",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add_all([owner, viewer, outsider])
        await session.commit()
        membership = CompanyMembershipModel(
            id=str(uuid.uuid4()),
            status="active",
            company_id=str(company_uuid),
            user_id=owner_uid,
            membership_role="owner",
            is_primary_contact=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        outsider_membership = CompanyMembershipModel(
            id=str(uuid.uuid4()),
            status="active",
            company_id=str(outsider_company_uuid),
            user_id=outsider_uid,
            membership_role="owner",
            is_primary_contact=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add_all([membership, outsider_membership])
        await session.commit()
        listing = ListingsModel(
            id=listing_uuid,
            title="E2E obalivka oceľového šrotu",
            material_type="steel",
            quantity=100.0,
            unit="t",
            condition="used",
            location="Bratislava",
            status="published",
            company_id=company_uuid,
        )
        thread = ChatThreadModel(
            id=thread_uuid,
            listing_id=listing_uuid,
            initiator_user_id=uuid.UUID(viewer_uid),
            initiator_company_id=company_uuid,
            recipient_user_id=uuid.UUID(owner_uid),
            recipient_company_id=company_uuid,
            subject="E2E živá obhliadka",
            status="open",
        )
        session.add_all([listing, thread])
        await session.commit()

        token_service = JwtService()
        _o = await token_service.issue_access_token(subject=owner_uid)
        _v = await token_service.issue_access_token(subject=viewer_uid)
        _x = await token_service.issue_access_token(subject=outsider_uid)
        owner_token = _o[0] if isinstance(_o, (list, tuple)) else _o
        viewer_token = _v[0] if isinstance(_v, (list, tuple)) else _v
        outsider_token = _x[0] if isinstance(_x, (list, tuple)) else _x

        out = {
            "baseUrl": f"http://127.0.0.1:{PORT}",
            "listingId": str(listing_uuid),
            "ownerUserId": owner_uid,
            "viewerUserId": viewer_uid,
            "outsiderUserId": outsider_uid,
            "ownerToken": owner_token,
            "viewerToken": viewer_token,
            "outsiderToken": outsider_token,
        }
        with open(TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f)
        print("E2E_TOKENS_WRITTEN", flush=True)


async def main():
    await seed_and_mint()
    config = uvicorn.Config(APP, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    stop = asyncio.Event()

    def _sig():
        stop.set()

    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(s, _sig)
        except NotImplementedError:
            pass

    stop_task = asyncio.create_task(stop.wait())
    task.add_done_callback(lambda _t: stop_task.cancel())
    await task
    stop_task.cancel()
    try:
        await stop_task
    except Exception:
        pass


if __name__ == "__main__":
    if "--seed-only" in sys.argv:
        asyncio.run(seed_and_mint())
        sys.exit(0)
    asyncio.run(main())
