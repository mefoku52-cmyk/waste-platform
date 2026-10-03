from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.infrastructure.db.timezone import to_naive_utc

"""Approval persistence contract."""

from abc import ABC, abstractmethod

from ...domain.approval.approval_request import ApprovalRequest
from ...domain.approval.approval_status import ApprovalStatus


class ApprovalRepository(ABC):
    @abstractmethod
    async def create(self, approval: ApprovalRequest) -> ApprovalRequest:
        raise NotImplementedError

    @abstractmethod
    async def get(self, approval_id: str) -> ApprovalRequest | None:
        raise NotImplementedError

    @abstractmethod
    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_at: datetime | None = None,
    ) -> ApprovalRequest:
        raise NotImplementedError


class SqlAlchemyApprovalRepository(ApprovalRepository):
    """SQLAlchemy implementation of approval persistence.

    Stlpce created_at / expires_at / decided_at su TIMESTAMP WITHOUT TIME ZONE.
    Zapis preto normalizujeme cez to_naive_utc() a citanie doplnuje tzinfo=UTC,
    aby domain validacia ApprovalRequest (tz-aware) presla.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, approval: ApprovalRequest) -> ApprovalRequest:
        from app.modules.agent_platform.infrastructure.models import (
            ApprovalRequestModel,
        )

        m = ApprovalRequestModel(
            approval_id=approval.approval_id,
            requested_by=approval.requested_by,
            requested_by_type=approval.requested_by_type,
            action=approval.action,
            target=approval.target,
            reason=approval.reason,
            risk_level=approval.risk_level,
            status=approval.status.value,
            created_at=to_naive_utc(approval.created_at),
            expires_at=to_naive_utc(approval.expires_at),
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return self._to_domain(m)

    async def get(self, approval_id: str) -> ApprovalRequest | None:
        from app.modules.agent_platform.infrastructure.models import (
            ApprovalRequestModel,
        )

        m = await self._session.get(ApprovalRequestModel, approval_id)
        return self._to_domain(m) if m else None

    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        decided_at: datetime | None = None,
    ) -> ApprovalRequest:
        from app.modules.agent_platform.infrastructure.models import (
            ApprovalRequestModel,
        )

        m = await self._session.get(ApprovalRequestModel, approval_id)
        if m is None:
            raise ValueError(f"Approval {approval_id} not found")
        m.status = status.value
        if decided_at is not None:
            m.decided_at = to_naive_utc(decided_at)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return self._to_domain(m)

    @staticmethod
    def _as_aware_utc(dt: datetime | None) -> datetime | None:
        """Normalize a naive DB column value back to tz-aware UTC on read."""
        if dt is None:
            return None
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

    @classmethod
    def _to_domain(cls, m) -> ApprovalRequest:
        return ApprovalRequest(
            approval_id=m.approval_id,
            requested_by=m.requested_by,
            requested_by_type=m.requested_by_type,
            action=m.action,
            target=m.target,
            reason=m.reason,
            risk_level=m.risk_level,
            created_at=cls._as_aware_utc(m.created_at),
            expires_at=cls._as_aware_utc(m.expires_at),
            status=ApprovalStatus(m.status),
        )
