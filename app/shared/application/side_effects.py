"""Audit + notifications – best-effort."""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


def _uuid(v):
    if v is None:
        return None
    return v if isinstance(v, UUID) else UUID(str(v))


def _uuid_safe(value):
    """Vrati UUID, alebo None ak hodnota nie je platne UUID.

    Pouziva sa pre nullable UUID stlpce (napr. admin_audit_entries.target_id),
    kde ne-UUID hodnota (email, ICO, ...) nesmie zhodit zapis celeho riadku.
    """
    if value is None:
        return None
    try:
        return value if isinstance(value, UUID) else UUID(str(value))
    except (ValueError, TypeError):
        return None


async def write_audit(
    *,
    session,
    actor_user_id,
    action: str,
    target_type: str,
    target_id=None,
    details: str | None = None,
):
    try:
        if not actor_user_id:
            return
        from app.modules.admin.domain.entities import AdminAuditEntryEntity
        from app.modules.admin.domain.enums import AdminAuditEntryStatus
        from app.modules.admin.infrastructure.repositories import (
            AdminAuditEntryRepositoryImpl,
        )

        now = datetime.now()
        aid = _uuid(actor_user_id)
        safe_target_id = _uuid_safe(target_id)
        if safe_target_id is None and target_id:
            # target_id nie je UUID (napr. email) → do UUID stlpca sa neda ulozit.
            # Zachovame hodnotu aspon v details, nezahodime cely audit riadok.
            details = f"target_raw={target_id}; {details or ''}"
        entity = AdminAuditEntryEntity(
            id=uuid4(),
            actor_user_id=aid,
            action=action,
            target_type=target_type,
            target_id=safe_target_id,
            details=details,
            status=AdminAuditEntryStatus.SUCCESS,
            created_at=now,
            updated_at=now,
            created_by_user_id=aid,
            updated_by_user_id=None,
        )
        await AdminAuditEntryRepositoryImpl(session).create(entity)
    except Exception:
        logger.exception("write_audit failed: %s", action)


async def notify_company_members(
    *,
    session,
    company_id,
    title: str,
    message: str,
    notif_type: str = "inquiry_received",
    related_entity_id=None,
    exclude_user_id=None,
):
    try:
        if not company_id:
            return
        from app.modules.company_memberships.infrastructure.repositories import (
            SqlAlchemyCompanyMembershipRepository,
        )
        from app.modules.notifications.domain.entities import NotificationEntity
        from app.modules.notifications.infrastructure.repositories import (
            NotificationRepositoryImpl,
        )

        cid = _uuid(company_id)
        members = await SqlAlchemyCompanyMembershipRepository(session).list_by_company_id(cid)
        nrepo = NotificationRepositoryImpl(session)
        now = datetime.now()
        rid = _uuid(related_entity_id)
        excl = str(exclude_user_id) if exclude_user_id else None
        for m in members:
            uid = getattr(m, "user_id", None)
            if uid is None or (excl and str(uid) == excl):
                continue
            await nrepo.create(
                NotificationEntity(
                    id=uuid4(),
                    user_id=_uuid(uid),
                    type=notif_type,
                    title=title,
                    message=message[:2000],
                    is_read=False,
                    related_entity_id=rid,
                    created_at=now,
                    updated_at=now,
                    created_by_user_id=None,
                    updated_by_user_id=None,
                )
            )

        # Best-effort: posle aj transakcny email vsetkym clenom.
        await _send_transactional_emails_to_members(
            session=session,
            company_id=company_id,
            title=title,
            message=message[:2000],
            related_entity_id=related_entity_id,
            exclude_user_id=exclude_user_id,
        )
    except Exception:
        logger.exception("notify_company_members failed")


async def _send_transactional_emails_to_members(
    *,
    session,
    company_id,
    title: str,
    message: str,
    related_entity_id=None,
    exclude_user_id=None,
) -> None:
    """Posle email vsetkym clenom firmy okrem excluded usera.

    Best-effort: nikdy nezlyha, nikdy nezablokuje volajuceho.
    Nikdy neposle na prazdny email.
    """
    try:
        from sqlalchemy import select

        from app.modules.company_memberships.infrastructure.repositories import (
            SqlAlchemyCompanyMembershipRepository,
        )
        from app.modules.users.infrastructure.models import UserModel

        cid = _uuid(company_id)
        if cid is None:
            return

        members = await SqlAlchemyCompanyMembershipRepository(session).list_by_company_id(cid)
        if not members:
            return

        excl = str(exclude_user_id) if exclude_user_id else None
        user_ids = []
        for m in members:
            uid = getattr(m, "user_id", None)
            if uid is None:
                continue
            if excl and str(uid) == excl:
                continue
            user_ids.append(uid)

        if not user_ids:
            return

        rows = (
            (
                await session.execute(
                    select(UserModel).where(UserModel.id.in_([str(u) for u in user_ids]))
                )
            )
            .scalars()
            .all()
        )

        from app.shared.infrastructure.email.transactional import (
            send_transactional_email,
        )

        for user in rows:
            email = (user.email or "").strip()
            if not email or "@" not in email:
                continue
            try:
                await send_transactional_email(
                    to=email,
                    subject=title,
                    body=message,
                )
            except Exception:
                logger.exception("transactional email to %s failed (company_id=%s)", email, cid)
    except Exception:
        logger.exception("_send_transactional_emails_to_members failed")


async def write_activity_event(
    *,
    session,
    event_type: str,
    actor_user_id=None,
    company_id=None,
    listing_id=None,
    payload: str | None = None,
) -> None:
    """Best-effort zapis do activity_events.

    Pouziva sa napr. na denny limit outreachu (event_type="lead_outreach.send").
    Nikdy nezlyha, nikdy nezablokuje volajuceho.
    """
    try:
        from app.modules.events.infrastructure.models import ActivityEventModel

        row = ActivityEventModel(
            event_type=event_type,
            actor_user_id=str(actor_user_id) if actor_user_id else None,
            company_id=str(company_id) if company_id else None,
            listing_id=str(listing_id) if listing_id else None,
            payload=payload,
        )
        session.add(row)
        commit = getattr(session, "commit", None)
        if commit:
            result = commit()
            if hasattr(result, "__await__"):
                await result
    except Exception:
        logger.exception("write_activity_event failed: %s", event_type)
