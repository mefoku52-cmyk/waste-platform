"""inspections domain repositories."""

from typing import Protocol
from uuid import UUID

from app.modules.inspections.domain.entities import InspectionEntity


class InspectionRepository(Protocol):
    async def create(self, entity: InspectionEntity) -> InspectionEntity: ...

    async def get(self, inspection_id: UUID | str) -> InspectionEntity | None: ...

    async def update(self, entity: InspectionEntity) -> InspectionEntity: ...

    async def find_active_by_listing(self, listing_id: UUID | str) -> InspectionEntity | None: ...

    async def list_by_listing(
        self, listing_id: UUID | str, limit: int = 20
    ) -> list[InspectionEntity]: ...


class InspectionEventRepository(Protocol):
    """Eventy prijate zo streamingu — idempotentne (unique event_uid)."""

    async def create(
        self,
        *,
        event_uid: str,
        inspection_id: UUID,
        event_type: str,
        actor_user_id: UUID | None,
        room_id: str | None,
        role: str | None,
        reason: str | None,
        payload: str | None,
    ) -> bool:
        """Vrati True ak event bol zapisany (prvy krat), False ak duplikat."""
        ...
