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
        entity = AdminAuditEntryEntity(
            id=uuid4(),
            actor_user_id=aid,
            action=action,
            target_type=target_type,
            target_id=_uuid(target_id),
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
    except Exception:
        logger.exception("notify_company_members failed")
