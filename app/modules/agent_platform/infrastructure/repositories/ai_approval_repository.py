"""Async repository for AI approval requests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agent_platform.infrastructure.models.ai_approval import AiApprovalRequestModel


class AiApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, request_id: UUID, company_id: UUID) -> AiApprovalRequestModel | None:
        stmt = select(AiApprovalRequestModel).where(
            AiApprovalRequestModel.id == request_id,
            AiApprovalRequestModel.company_id == company_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, model: AiApprovalRequestModel) -> None:
        self._session.add(model)
        await self._session.flush()

    async def transition_status(
        self,
        request_id: UUID,
        company_id: UUID,
        expected_status: str,
        new_status: str,
        **extra,
    ) -> bool:
        """Atomic status transition. Returns True if exactly one row was updated."""
        values = {"status": new_status, **extra}
        stmt = (
            update(AiApprovalRequestModel)
            .where(
                AiApprovalRequestModel.id == request_id,
                AiApprovalRequestModel.company_id == company_id,
                AiApprovalRequestModel.status == expected_status,
            )
            .values(**values)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount == 1