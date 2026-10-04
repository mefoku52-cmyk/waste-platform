"""Outreach candidate repository – ABC + SQLAlchemy implementation."""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.lead_finder.domain.entities.outreach_candidate import (
    OutreachCandidate,
    OutreachStatus,
)
from app.modules.lead_finder.infrastructure.persistence.models import (
    OutreachCandidateModel,
)

logger = logging.getLogger(__name__)


def _to_domain(m: OutreachCandidateModel) -> OutreachCandidate:
    def _aware(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

    return OutreachCandidate(
        id=str(m.id),
        company_name=m.company_name,
        ico=m.ico,
        city=m.city,
        industry=m.industry,
        email=m.email,
        status=OutreachStatus(m.status or "new"),
        draft_subject=m.draft_subject,
        draft_body=m.draft_body,
        created_at=_aware(m.created_at) or datetime.now(UTC),
        updated_at=_aware(m.updated_at) or datetime.now(UTC),
        approved_at=_aware(m.approved_at),
        sent_at=_aware(m.sent_at),
    )


class OutreachCandidateRepository(ABC):
    @abstractmethod
    async def create(
        self,
        *,
        company_name: str,
        ico: str | None,
        city: str | None,
        industry: str | None,
        email: str | None,
    ) -> OutreachCandidate: ...

    @abstractmethod
    async def get_by_id(self, candidate_id: str) -> OutreachCandidate | None: ...

    @abstractmethod
    async def list_by_status(
        self,
        *,
        status: OutreachStatus | None = None,
        city: str | None = None,
        limit: int = 100,
    ) -> list[OutreachCandidate]: ...

    @abstractmethod
    async def update_draft(
        self,
        *,
        candidate_id: str,
        subject: str,
        body: str,
    ) -> OutreachCandidate | None: ...

    @abstractmethod
    async def update_status(
        self,
        *,
        candidate_id: str,
        status: OutreachStatus,
    ) -> OutreachCandidate | None: ...


class SqlAlchemyOutreachCandidateRepository(OutreachCandidateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        company_name: str,
        ico: str | None,
        city: str | None,
        industry: str | None,
        email: str | None,
    ) -> OutreachCandidate:
        now = datetime.now(UTC).replace(tzinfo=None)
        m = OutreachCandidateModel(
            id=uuid.uuid4(),
            company_name=company_name.strip(),
            ico=(ico or "").strip() or None,
            city=(city or "").strip() or None,
            industry=(industry or "").strip() or None,
            email=(email or "").strip() or None,
            status=OutreachStatus.NEW.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(m)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_domain(m)

    async def get_by_id(self, candidate_id: str) -> OutreachCandidate | None:
        try:
            cid = uuid.UUID(candidate_id)
        except (ValueError, TypeError):
            return None
        m = await self._session.get(OutreachCandidateModel, cid)
        return _to_domain(m) if m else None

    async def list_by_status(
        self,
        *,
        status: OutreachStatus | None = None,
        city: str | None = None,
        limit: int = 100,
    ) -> list[OutreachCandidate]:
        stmt = select(OutreachCandidateModel)
        if status is not None:
            stmt = stmt.where(OutreachCandidateModel.status == status.value)
        if city:
            stmt = stmt.where(OutreachCandidateModel.city == city)
        stmt = stmt.order_by(OutreachCandidateModel.created_at.desc()).limit(
            max(1, min(limit, 500))
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(r) for r in rows]

    async def update_draft(
        self,
        *,
        candidate_id: str,
        subject: str,
        body: str,
    ) -> OutreachCandidate | None:
        try:
            cid = uuid.UUID(candidate_id)
        except (ValueError, TypeError):
            return None
        m = await self._session.get(OutreachCandidateModel, cid)
        if m is None:
            return None
        m.draft_subject = subject
        m.draft_body = body
        m.status = OutreachStatus.DRAFTED.value
        m.updated_at = datetime.now(UTC).replace(tzinfo=None)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_domain(m)

    async def update_email(
        self,
        *,
        candidate_id: str,
        email: str,
    ) -> OutreachCandidate | None:
        """Update only the email field of a candidate."""
        try:
            cid = uuid.UUID(candidate_id)
        except (ValueError, TypeError):
            return None
        m = await self._session.get(OutreachCandidateModel, cid)
        if m is None:
            return None
        m.email = email.strip() or None
        m.updated_at = datetime.now(UTC).replace(tzinfo=None)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_domain(m)

    async def update_status(
        self,
        *,
        candidate_id: str,
        status: OutreachStatus,
    ) -> OutreachCandidate | None:
        try:
            cid = uuid.UUID(candidate_id)
        except (ValueError, TypeError):
            return None
        m = await self._session.get(OutreachCandidateModel, cid)
        if m is None:
            return None
        now = datetime.now(UTC).replace(tzinfo=None)
        m.status = status.value
        m.updated_at = now
        if status == OutreachStatus.APPROVED:
            m.approved_at = now
        if status == OutreachStatus.SENT:
            m.sent_at = now
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return _to_domain(m)

    async def find_by_email(self, email: str) -> OutreachCandidate | None:
        """Nájdi kandidáta podľa emailu (case-insensitive).

        Používa sa na deduplikáciu pri category discovery. Prázdny email
        nikdy nematchuje — inak by sa zlúčili všetci kandidáti bez emailu.
        """
        cleaned = (email or "").strip().lower()
        if not cleaned:
            return None
        stmt = select(OutreachCandidateModel).where(
            func.lower(OutreachCandidateModel.email) == cleaned
        )
        m = (await self._session.execute(stmt)).scalars().first()
        return _to_domain(m) if m else None

    async def create_from_discovery(
        self,
        *,
        company_name: str,
        email: str,
        phone: str | None = None,
        website: str | None = None,
        city: str | None = None,
        source_url: str = "",
    ) -> OutreachCandidate:
        """Vytvor nového kandidáta z directory discovery (status NEW).

        POZOR: ``OutreachCandidateModel`` zatiaľ NEMÁ stĺpce pre
        ``phone``, ``website`` ani ``source_url``. Tie hodnoty sa preto
        neukladajú a len sa zalogujú — na ich uloženie treba Alembic
        migráciu. Ukladá sa company_name, email, city, status a timestampy.

        Metóda len ``flush``-uje; commituje volajúci (endpoint), aby sa
        celý beh dal vrátiť späť ako jedna transakcia.
        """
        dropped = [
            label
            for label, value in (
                ("phone", phone),
                ("website", website),
                ("source_url", source_url),
            )
            if value
        ]
        if dropped:
            logger.warning(
                "Discovery polia bez stĺpca v DB (zahodené): %s pre %r",
                ", ".join(dropped),
                company_name,
            )

        now = datetime.now(UTC).replace(tzinfo=None)
        m = OutreachCandidateModel(
            id=uuid.uuid4(),
            company_name=company_name.strip(),
            city=(city or "").strip() or None,
            email=(email or "").strip() or None,
            status=OutreachStatus.NEW.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(m)
        await self._session.flush()
        return _to_domain(m)
