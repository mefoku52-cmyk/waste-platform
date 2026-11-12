"""inspections application services.

Server-side identita a autorizacia:
  - Publisher aj Viewer su identifikovani IBA z JWT prihlaseneho pouzivatela
    (require_current_user) — ziaden companyId/userId nie je prijimany od klienta.
  - Viewer (druha strana) musi byt counterpart chat vlakna na danej ponuke
    (alebo participant threadu, ktory je viazany na ponuku obhliadky).
  - Streamovaci token je viazany na konkretnu obhliadku (claim `insp`) a rolu.
"""

import asyncio
import contextlib
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import or_, select

from app.core.config import settings
from app.modules.chat.infrastructure.models import ChatThreadModel
from app.modules.inspections.application.dto import InspectionData
from app.modules.inspections.application.streaming_tokens import (
    StreamingTokenService,
)
from app.modules.inspections.domain.entities import InspectionEntity
from app.modules.inspections.domain.enums import InspectionEventType, InspectionState
from app.modules.inspections.infrastructure.repositories import (
    InspectionEventRepositoryImpl,
    InspectionRepositoryImpl,
)
from app.modules.inspections.infrastructure.streaming_client import (
    StreamingServiceClient,
)
from app.modules.listings.infrastructure.models import ListingsModel
from app.shared.application.side_effects import write_audit
from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    NotFoundDomainError,
    ValidationDomainError,
)

_ROOM_POLL_INTERVAL_S = 0.5
_ROOM_WAIT_DEFAULT_S = 6.0
_ROOM_WAIT_MAX_S = 15.0


def _uid(value):
    if value in (None, ""):
        return None
    return value if isinstance(value, UUID) else UUID(str(value))


class InspectionService:
    def __init__(
        self,
        session,
        repo: InspectionRepositoryImpl,
        events: InspectionEventRepositoryImpl,
        streaming=None,
    ):
        self.session = session
        self.repo = repo
        self.events = events
        self.tokens = StreamingTokenService()
        self.streaming = streaming or StreamingServiceClient()

    # ─── helpers ──────────────────────────────────────────────────

    async def _get_listing(self, listing_id):
        r = await self.session.execute(
            select(ListingsModel).where(ListingsModel.id == _uid(listing_id))
        )
        return r.scalar_one_or_none()

    async def _user_thread_on_listing(self, listing_id, user_id, thread_id=None):
        """Chat vlakna pouzivatela viazane na ponuku (counterpart pravidlo)."""
        q = (
            select(ChatThreadModel)
            .where(ChatThreadModel.listing_id == _uid(listing_id))
            .where(
                or_(
                    ChatThreadModel.initiator_user_id == _uid(user_id),
                    ChatThreadModel.recipient_user_id == _uid(user_id),
                )
            )
        )
        if thread_id is not None:
            q = q.where(ChatThreadModel.id == _uid(thread_id))
        q = q.order_by(ChatThreadModel.last_message_at.desc().nullslast()).limit(1)
        r = await self.session.execute(q)
        return r.scalar_one_or_none()

    @staticmethod
    def _is_member(company_ids: list[str], company_id) -> bool:
        return company_id is not None and str(company_id) in {str(c) for c in company_ids}

    @staticmethod
    def _public_url() -> str:
        return (getattr(settings, "CMEP_STREAMING_PUBLIC_URL", "") or "").strip().rstrip("/")

    def _publish_url(self, token: str, inspection_id) -> str:
        base = self._public_url()
        if not base:
            raise ValidationDomainError(
                "Live inspection is not configured: set CMEP_STREAMING_PUBLIC_URL."
            )
        return f"{base}/publish.html?token={token}&offer={inspection_id}&auto=1"

    def _viewer_url(self, token: str, inspection_id, room_id: str | None) -> str:
        base = self._public_url()
        if not base:
            raise ValidationDomainError(
                "Live inspection is not configured: set CMEP_STREAMING_PUBLIC_URL."
            )
        url = f"{base}/viewer.html?token={token}&insp={inspection_id}&auto=1"
        if room_id:
            url += f"&room={room_id}"
        return url

    @staticmethod
    def _to_data(e: InspectionEntity) -> InspectionData:
        return InspectionData(
            id=e.id,
            listing_id=e.listing_id,
            room_id=e.room_id,
            owner_user_id=e.owner_user_id,
            owner_company_id=e.owner_company_id,
            viewer_user_id=e.viewer_user_id,
            viewer_company_id=e.viewer_company_id,
            viewer_thread_id=e.viewer_thread_id,
            state=e.state,
            consent_to_record=e.consent_to_record,
            created_at=e.created_at,
            updated_at=e.updated_at,
            ended_at=e.ended_at,
        )

    # ─── publisher flow ───────────────────────────────────────────

    async def create_inspection(self, *, user_id, company_ids: list[str], listing_id) -> dict:
        """Vlastnik ponuky spusta zivu obhliadku. Vracia publisher pristup."""
        listing = await self._get_listing(listing_id)
        if listing is None:
            raise NotFoundDomainError(f"Listing {listing_id} not found")
        if not self._is_member(company_ids, listing.company_id):
            raise ForbiddenDomainError("You do not have access to this listing")

        existing = await self.repo.find_active_by_listing(listing_id)
        if existing is not None:
            raise ConflictDomainError("An active inspection already exists for this listing")

        entity = InspectionEntity(
            id=uuid4(),
            listing_id=_uid(listing_id),
            owner_user_id=_uid(user_id),
            owner_company_id=_uid(listing.company_id),
            state=InspectionState.CREATED,
            consent_to_record=False,
            created_by_user_id=_uid(user_id),
            updated_by_user_id=_uid(user_id),
        )
        entity.validate()
        created = await self.repo.create(entity)

        token = self.tokens.mint(
            user_id=user_id,
            company_id=listing.company_id,
            inspection_id=created.id,
            listing_id=created.listing_id,
            role="publisher",
            consent_to_record=created.consent_to_record,
        )
        await write_audit(
            session=self.session,
            actor_user_id=user_id,
            action="inspection.created",
            target_type="inspection",
            target_id=created.id,
            details=f"listing={listing_id}",
        )
        return {
            "inspection": self._to_data(created),
            "role": "publisher",
            "publishUrl": self._publish_url(token.token, created.id),
            "expiresIn": token.expires_in,
        }

    # ─── viewer flow ──────────────────────────────────────────────

    async def active_inspection_for_listing(
        self, *, user_id, company_ids: list[str], listing_id
    ) -> dict:
        """Aktivna obhliadka ponuky + co klient moze robit (pre UI)."""
        inspection = await self.repo.find_active_by_listing(listing_id)
        listing = await self._get_listing(listing_id)
        if listing is None:
            raise NotFoundDomainError(f"Listing {listing_id} not found")
        is_owner = self._is_member(company_ids, listing.company_id)
        if inspection is None:
            return {"inspection": None, "canPublish": is_owner, "canJoin": False}
        is_assigned_viewer = inspection.viewer_user_id is not None and str(
            inspection.viewer_user_id
        ) == str(user_id)
        if not is_owner and not is_assigned_viewer:
            # Counterpart (ma thread na ponuke) vidie existujucu obhliadku, aby sa
            # mohol pripojit; cudzi uzivatel dostane 404 (bez vyleja existencie).
            thread = await self._user_thread_on_listing(listing_id, user_id)
            if thread is None:
                raise NotFoundDomainError("Inspection not found")
        thread = await self._user_thread_on_listing(listing_id, user_id)
        return {
            "inspection": self._to_data(inspection),
            "canPublish": is_owner,
            "canJoin": not is_owner and thread is not None,
            "isViewer": is_assigned_viewer,
        }

    async def join_inspection(
        self,
        *,
        user_id,
        company_ids: list[str],
        inspection_id=None,
        listing_id=None,
        thread_id=None,
        wait_room_seconds: float = _ROOM_WAIT_DEFAULT_S,
    ) -> dict:
        """Druha strana sa pripaja k obhliadke — vracia viewer pristup."""
        if inspection_id:
            inspection = await self.repo.get(inspection_id)
            if inspection is None:
                raise NotFoundDomainError("Inspection not found")
            listing_id = inspection.listing_id
        elif listing_id:
            inspection = await self.repo.find_active_by_listing(listing_id)
            if inspection is None:
                raise NotFoundDomainError("No active inspection for this listing")
        else:
            raise ValidationDomainError("inspectionId or listingId is required")

        listing = await self._get_listing(listing_id)
        if listing is None:
            raise NotFoundDomainError(f"Listing {listing_id} not found")

        # Publisher nie je viewer.
        if self._is_member(company_ids, listing.company_id):
            raise ValidationDomainError(
                "Publisher of the listing cannot join as viewer — use the publisher link"
            )

        # Aktivna obhliadka.
        if not inspection.state.is_active:
            raise ConflictDomainError("Inspection is not active")

        # Counterpart pravidlo: user musi mat chat vlakno na tejto ponuke.
        thread = await self._user_thread_on_listing(listing_id, user_id, thread_id)
        if thread is None:
            raise ForbiddenDomainError(
                "Only the counterpart of this listing can join the inspection"
            )

        # Miesto viewera: prve priradenie vyhrava; iny viewer po accepte -> konflikt.
        if (
            inspection.viewer_user_id is not None
            and str(inspection.viewer_user_id) != str(user_id)
            and inspection.state in (InspectionState.ACCEPTED, InspectionState.LIVE)
        ):
            raise ConflictDomainError("Another viewer is already assigned to this inspection")

        # Room musí existovat (streaming potvrdil createRoom) — az po autorizacii.
        if inspection.state == InspectionState.CREATED:
            raise ConflictDomainError("Inspection room is not created yet — try again shortly")

        viewer_company_id = (
            thread.initiator_company_id
            if str(thread.initiator_user_id) == str(user_id)
            else thread.recipient_company_id
        )
        updated = False
        if (
            inspection.viewer_user_id is None
            or inspection.viewer_thread_id is None
            or inspection.viewer_company_id is None
        ):
            inspection.viewer_user_id = _uid(user_id)
            inspection.viewer_thread_id = thread.id
            if viewer_company_id:
                inspection.viewer_company_id = _uid(viewer_company_id)
            inspection.updated_by_user_id = _uid(user_id)
            inspection.updated_at = datetime.now()
            inspection = await self.repo.update(inspection)
            updated = True

        token = self.tokens.mint(
            user_id=user_id,
            company_id=viewer_company_id,
            inspection_id=inspection.id,
            listing_id=inspection.listing_id,
            role="viewer",
            consent_to_record=False,
        )

        # Pockaj na Room ID (publisher createRoom -> event -> room_id).
        wait = max(0.0, min(float(wait_room_seconds), _ROOM_WAIT_MAX_S))
        deadline = datetime.now() + timedelta(seconds=wait)
        while inspection.room_id is None and datetime.now() < deadline:
            await asyncio.sleep(_ROOM_POLL_INTERVAL_S)
            fresh = await self.repo.get(inspection.id)
            if fresh is not None:
                inspection = fresh

        if updated:
            await write_audit(
                session=self.session,
                actor_user_id=user_id,
                action="inspection.joined",
                target_type="inspection",
                target_id=inspection.id,
                details=f"listing={inspection.listing_id}",
            )

        return {
            "inspection": self._to_data(inspection),
            "role": "viewer",
            "viewerUrl": self._viewer_url(token.token, inspection.id, inspection.room_id),
            "expiresIn": token.expires_in,
            "roomId": inspection.room_id,
        }

    # ─── status / consent / end ───────────────────────────────────

    async def publisher_link(self, *, user_id, company_ids: list[str], inspection_id) -> dict:
        """Znova vystaví publisher URL pre existujúcu aktívnu obhliadku
        (napr. keď si publisher zavrel kartu — nový token, rovnaká obhliadka)."""
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")
        if not self._is_member(company_ids, inspection.owner_company_id):
            raise ForbiddenDomainError("Only the listing owner company can get the publisher link")
        if not inspection.state.is_active:
            raise ConflictDomainError("Inspection is not active")
        token = self.tokens.mint(
            user_id=inspection.owner_user_id,
            company_id=inspection.owner_company_id,
            inspection_id=inspection.id,
            listing_id=inspection.listing_id,
            role="publisher",
            consent_to_record=inspection.consent_to_record,
        )
        return {
            "role": "publisher",
            "publishUrl": self._publish_url(token.token, inspection.id),
            "expiresIn": token.expires_in,
        }

    async def get_inspection(self, *, user_id, company_ids: list[str], inspection_id) -> dict:
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")
        listing = await self._get_listing(inspection.listing_id)
        is_owner = listing is not None and self._is_member(company_ids, listing.company_id)
        is_viewer = inspection.viewer_user_id is not None and str(inspection.viewer_user_id) == str(
            user_id
        )
        if not (is_owner or is_viewer):
            raise NotFoundDomainError("Inspection not found")
        return {"inspection": self._to_data(inspection)}

    async def set_recording_consent(
        self, *, user_id, company_ids: list[str], inspection_id
    ) -> dict:
        """Vyslovny suhlas vlastnika ponuky s nahranim (GDPR). Bez neho rec=0."""
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")
        if not self._is_member(company_ids, inspection.owner_company_id):
            raise ForbiddenDomainError("Only the listing owner company can grant recording consent")
        if not inspection.state.is_active:
            raise ConflictDomainError("Inspection is not active")
        inspection.consent_to_record = True
        inspection.recording_consent_at = datetime.now()
        inspection.updated_by_user_id = _uid(user_id)
        inspection.updated_at = datetime.now()
        saved = await self.repo.update(inspection)
        await write_audit(
            session=self.session,
            actor_user_id=user_id,
            action="inspection.recording_consent",
            target_type="inspection",
            target_id=inspection.id,
            details="consent_to_record=true",
        )
        return {"inspection": self._to_data(saved)}

    async def end_inspection(self, *, user_id, company_ids: list[str], inspection_id) -> dict:
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")
        if not self._is_member(company_ids, inspection.owner_company_id):
            raise ForbiddenDomainError("Only the listing owner company can end the inspection")
        if not inspection.state.is_active:
            if inspection.state == InspectionState.ENDED:
                # Idempotne: opakovane ukoncenie uz ukončenej obhliadky je uspesne, ked miestnost
                # uz zanikla odchodom publishra. Ziadne dalsie volanie streamingu.
                return {"inspection": self._to_data(inspection)}
            raise ConflictDomainError("Inspection is not active")
        inspection.state = InspectionState.ENDED
        inspection.ended_at = datetime.now()
        inspection.updated_by_user_id = _uid(user_id)
        inspection.updated_at = datetime.now()
        saved = await self.repo.update(inspection)
        await write_audit(
            session=self.session,
            actor_user_id=user_id,
            action="inspection.ended",
            target_type="inspection",
            target_id=inspection.id,
        )
        # Synchronizuj ukončenie do streamovacieho jadra (uzavrie miestnosť).
        # Best-effort: platformový stav (ENDED) je autoritatívny aj ak volanie zlyhá.
        with contextlib.suppress(Exception):
            await self.streaming.end_inspection(saved.id)
        return {"inspection": self._to_data(saved)}

    # ─── interné rozhranie pre streamingsluzbu ────────────────────

    @staticmethod
    def _check_internal_key(header_key: str | None) -> None:
        expected = (getattr(settings, "CMEP_INTERNAL_API_KEY", "") or "").strip()
        if not expected:
            raise ForbiddenDomainError("Internal inspection API is not configured")
        import hmac as _hmac

        if not header_key or not _hmac.compare_digest(str(header_key), expected):
            raise ForbiddenDomainError("Invalid internal API key")

    async def verify_for_streaming(
        self,
        *,
        internal_key: str | None,
        inspection_id,
        sub: str | None,
        role: str | None,
    ) -> dict:
        """Verify endpoint pre HttpAdapter streamingu (fail-closed kontrakt).

        Vrati ok=True IBA ak:
          - obhliadka existuje a nie je terminalna,
          - sub/role zodpovedaju ucastnikom obhliadky (publisher = owner,
            viewer = priradeny viewer).
        """
        self._check_internal_key(internal_key)
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")
        if not inspection.state.is_active:
            return {"ok": False, "state": inspection.state.value, "reason": "inspection_ended"}
        if role == "publisher":
            if not sub or str(inspection.owner_user_id) != str(sub):
                return {"ok": False, "state": inspection.state.value, "reason": "not_publisher"}
        elif role == "viewer":
            if (
                not sub
                or not inspection.viewer_user_id
                or str(inspection.viewer_user_id) != str(sub)
            ):
                return {"ok": False, "state": inspection.state.value, "reason": "not_viewer"}
        else:
            return {"ok": False, "state": inspection.state.value, "reason": "invalid_role"}
        return {
            "ok": True,
            "state": inspection.state.value,
            "inspectionId": str(inspection.id),
            "listingId": str(inspection.listing_id),
            "ownerCompanyId": str(inspection.owner_company_id),
            "viewerCompanyId": (
                str(inspection.viewer_company_id) if inspection.viewer_company_id else None
            ),
            "consentToRecord": bool(inspection.consent_to_record),
            "roomId": inspection.room_id,
        }

    async def record_event(
        self,
        *,
        internal_key: str | None,
        event_uid: str,
        inspection_id,
        event_type: str,
        actor_sub: str | None = None,
        room_id: str | None = None,
        role: str | None = None,
        reason: str | None = None,
    ) -> dict:
        """Ingest eventov zo streamingu — idempotentny podla event_uid."""
        self._check_internal_key(internal_key)
        if event_type not in {e.value for e in InspectionEventType}:
            raise ValidationDomainError(f"Unknown inspection event type: {event_type}")
        inspection = await self.repo.get(inspection_id)
        if inspection is None:
            raise NotFoundDomainError("Inspection not found")

        recorded = await self.events.create(
            event_uid=event_uid,
            inspection_id=inspection.id,
            event_type=event_type,
            actor_user_id=_uid(actor_sub),
            room_id=room_id,
            role=role,
            reason=reason,
            payload=None,
        )
        if not recorded:
            return {"recorded": False, "duplicate": True}

        from app.modules.inspections.infrastructure.mappers import apply_event_to_entity

        apply_event_to_entity(inspection, event_type=event_type, role=role, room_id=room_id)
        inspection.updated_at = datetime.now()
        await self.repo.update(inspection)
        return {"recorded": True, "state": inspection.state.value}
