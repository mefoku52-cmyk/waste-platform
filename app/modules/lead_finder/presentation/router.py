"""Lead finder admin endpoints – draft and send outreach emails.

Platform-admin only. One email per request. No bulk auto-send.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.core.config import settings
from app.modules.lead_finder.application.services.batch_drafter import (
    BatchDrafter,
    CompanyInput,
)
from app.modules.lead_finder.application.services.email_drafter import (
    EmailDrafter,
)
from app.modules.notifications.application.telegram_service import (
    TelegramService,
)
from app.shared.application.side_effects import write_activity_event, write_audit
from app.shared.infrastructure.db.session import get_db_session
from app.shared.infrastructure.email.resend_sender import (
    count_sent_today,
    send_via_resend,
)
from app.shared.infrastructure.email.sender import send_email
from app.shared.presentation.auth_dependencies import require_current_user
from app.shared.presentation.authorization import (
    current_user_id,
    is_platform_admin,
)
from app.shared.presentation.business_metrics import (
    BOUNCE_TOTAL,
    DRAFTS_TOTAL,
    PIPELINE_DURATION,
    SEND_TOTAL,
)

logger = logging.getLogger(__name__)


# Drzime silnu referenciu na beziace tasky, aby ich GC nezrusil pred
# dokoncenim (ruff RUF006). Task sa po dokonceni sam odstrani.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


# Drzime silnu referenciu na beziace tasky, aby ich GC nezrusil pred
# dokoncenim (ruff RUF006). Task sa po dokonceni sam odstrani.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


async def _notify_safe(coro) -> None:
    """Fire-and-forget Telegram notifikacia. Nikdy nezlyha request."""
    try:
        await coro
    except Exception:
        logger.warning("Telegram notify failed (ignored)", exc_info=True)


def _fire_and_forget(coro) -> None:
    """Spusti korutinu na pozadi a drz na nu referenciu."""
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)


router = APIRouter(prefix="/admin/lead-outreach", tags=["admin-lead-outreach"])


class DraftRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)
    reason: str | None = Field(default=None, max_length=500)


class DraftResponse(BaseModel):
    subject: str
    body: str


class SendRequest(BaseModel):
    to: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20000)


class SendResponse(BaseModel):
    ok: bool
    message: str


class ProviderStatus(BaseModel):
    """Stav jedneho providera — NIKDY neobsahuje hodnotu kluca."""

    is_set: bool


class LeadOutreachStatusResponse(BaseModel):
    """Diagnostika pre admin UI. Zamerne bez akychkolvek tajomstiev.

    Vsetky polia su bud bool, alebo negatívne/nepriamé — endpoint nikdy
    nevrati hodnotu API kluca, len informaciu ci je nastaveny.
    """

    outreach_enabled: bool
    email_provider: ProviderStatus
    from_email: ProviderStatus
    ai_provider: ProviderStatus
    ai_fallback_active: bool
    daily_limit: int
    sent_today: int
    remaining_today: int


class DiscoverCategoriesRequest(BaseModel):
    """Kategórie Zlatých stránok na prejdenie. None = default top 3."""

    categories: list[str] | None = Field(default=None, max_length=10)
    max_pages: int = Field(default=20, ge=1, le=30)


class DiscoverCategoriesResponse(BaseModel):
    discovered: int
    saved: int
    duplicates: int
    per_category: dict[str, int]


def _require_admin(current_user) -> None:
    if not is_platform_admin(current_user):
        raise HTTPException(status_code=403, detail="Platform admin access required")


async def _is_early_bird(session) -> bool:
    """True, ak je na platforme menej ako EARLY_BIRD_LIMIT overenych firiem.

    Zdielana logika pre /draft, /draft-batch a /draft-new, aby sa drafty
    z roznych ciest nerozisli. Pri chybe DB vraciame False — nikdy
    neslubujeme bonus, ktory nevieme dolozit.
    """
    try:
        r = await session.execute(text("SELECT COUNT(*) FROM companies WHERE status = 'verified'"))
        return int(r.scalar() or 0) < EARLY_BIRD_LIMIT
    except Exception:
        return False


class BatchCompanyItem(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    city: str | None = Field(default=None, max_length=128)
    industry: str | None = Field(default=None, max_length=128)
    reason: str | None = Field(default=None, max_length=500)


class BatchDraftRequest(BaseModel):
    companies: list[BatchCompanyItem] = Field(min_length=1, max_length=30)


class BatchDraftItem(BaseModel):
    company_name: str
    city: str | None
    industry: str | None
    subject: str
    body: str


class BatchDraftResponse(BaseModel):
    count: int
    items: list[BatchDraftItem]


EARLY_BIRD_LIMIT = 10


class DiscoverDailyItem(BaseModel):
    id: str
    company_name: str
    ico: str | None = None
    city: str | None = None
    industry: str | None = None
    subject: str | None = None
    body: str | None = None
    email: str | None = None


class DiscoverDailyResponse(BaseModel):
    ok: bool
    picked: int
    created: int
    drafted: int
    failed: int
    emails_found: int = 0
    known_before: int
    send: bool = False
    items: list[DiscoverDailyItem] = []


@router.get("/status", response_model=LeadOutreachStatusResponse)
async def lead_outreach_status(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> LeadOutreachStatusResponse:
    """Diagnostika outreach pipeline pre admin UI.

    Bezpecnost: vracia VYLUCNE booly a cisla. Nikdy nenavracia hodnotu
    API kluca, jeho cast ani dlzku — len ci je nastaveny.
    """
    _require_admin(current_user)

    ai_provider_set = EmailDrafter.is_provider_configured()
    daily_limit = max(1, int(settings.LEAD_OUTREACH_DAILY_LIMIT or 30))
    sent_today = await count_sent_today(session)

    return LeadOutreachStatusResponse(
        outreach_enabled=bool(settings.LEAD_OUTREACH_ENABLED),
        email_provider=ProviderStatus(
            is_set=bool((settings.RESEND_API_KEY or "").strip()),
        ),
        from_email=ProviderStatus(
            is_set=bool((settings.RESEND_FROM_EMAIL or "").strip()),
        ),
        ai_provider=ProviderStatus(is_set=ai_provider_set),
        ai_fallback_active=not ai_provider_set,
        daily_limit=daily_limit,
        sent_today=sent_today,
        remaining_today=max(0, daily_limit - sent_today),
    )


@router.get("/quota")
async def outreach_quota(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    _require_admin(current_user)
    from app.core.config import settings

    limit = max(1, int(getattr(settings, "LEAD_OUTREACH_DAILY_LIMIT", 30) or 30))
    sent = 0
    rejected = 0
    try:
        row = await session.execute(
            text(
                """
                SELECT
                  COUNT(*) FILTER (WHERE action = 'lead_outreach.send') AS sent,
                  COUNT(*) FILTER (WHERE action = 'lead_outreach.reject') AS rejected
                FROM audit_logs
                WHERE created_at >= date_trunc('day', now() AT TIME ZONE 'UTC')
                """
            )
        )
        found = row.mappings().first() or {}
        sent = int(found.get("sent") or 0)
        rejected = int(found.get("rejected") or 0)
    except Exception:
        await session.rollback()
    return {
        "limit": limit,
        "sent_today": sent,
        "rejected_today": rejected,
        "remaining": max(0, limit - sent),
    }


@router.post("/discover-daily", response_model=DiscoverDailyResponse)
async def discover_daily(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
):
    _require_admin(current_user)
    from app.modules.lead_finder.application.services.daily_discover import (
        run_daily_discover,
    )

    # Jedno kliknutie = kompletný discovery workflow:
    # RPO -> kandidát -> web -> verejný email -> AI draft -> DB.
    # Nikdy neposiela email automaticky.
    result = await run_daily_discover(session, limit=30, draft=True)
    return DiscoverDailyResponse(**result)


@router.post("/draft", response_model=DraftResponse)
async def draft_email(
    payload: DraftRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> DraftResponse:
    _require_admin(current_user)

    # Zisti, kolko overenych firiem je na platforme.
    early_bird = await _is_early_bird(session)

    try:
        draft = await EmailDrafter().draft(
            company_name=payload.company_name,
            city=payload.city,
            industry=payload.industry,
            reason=payload.reason,
            early_bird=early_bird,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Nepodarilo sa pripraviť návrh emailu.",
        )
    return DraftResponse(subject=draft.subject, body=draft.body)


@router.post("/send", response_model=SendResponse)
async def send_outreach_email(
    payload: SendRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SendResponse:
    _require_admin(current_user)

    result = await send_via_resend(
        session=session,
        to=payload.to,
        subject=payload.subject,
        body=payload.body,
    )

    if not result.ok:
        # Fallback na SMTP len ak Resend nie je nakonfigurovany vobec
        if "nie je nakonfigurovany" in result.message:
            ok = send_email(to=payload.to, subject=payload.subject, body=payload.body)
            if ok:
                await write_audit(
                    session=session,
                    actor_user_id=current_user_id(current_user),
                    action="lead_outreach.send",
                    target_type="email",
                    target_id=payload.to,
                    details=f"via=smtp,subject={payload.subject[:80]}",
                )
                await write_activity_event(
                    session=session,
                    event_type="lead_outreach.send",
                    actor_user_id=current_user_id(current_user),
                    company_id=None,
                    listing_id=None,
                    payload=f"to={payload.to},via=smtp",
                )
                _fire_and_forget(TelegramService.notify_sent(payload.to, ok=True))
                return SendResponse(ok=True, message="Email odoslaný cez SMTP.")
            return SendResponse(ok=False, message="SMTP zlyhalo.")
        return SendResponse(ok=False, message=result.message)

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.send",
        target_type="email",
        target_id=payload.to,
        details=f"via=resend,subject={payload.subject[:80]}",
    )
    await write_activity_event(
        session=session,
        event_type="lead_outreach.send",
        actor_user_id=current_user_id(current_user),
        company_id=None,
        listing_id=None,
        payload=f"to={payload.to},via=resend",
    )

    SEND_TOTAL.labels(result="ok").inc()

    # Bounce detection: ak Resend hlási odmietnutie, započítaj bounce.
    if result.message and (
        "bounce" in result.message.lower() or "odmietol" in result.message.lower()
    ):
        BOUNCE_TOTAL.inc()

    _fire_and_forget(TelegramService.notify_sent(payload.to, ok=True))

    remaining = result.remaining_today
    msg = result.message
    if remaining is not None:
        msg = f"{msg} Zostáva dnes: {remaining}."
    return SendResponse(ok=True, message=msg)


@router.post("/draft-batch", response_model=BatchDraftResponse)
async def draft_batch(
    payload: BatchDraftRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> BatchDraftResponse:
    """Draft N emails at once (max 30). Admin only."""
    _require_admin(current_user)

    # Early bird detection (rovnaka logika ako v /draft)
    early_bird = await _is_early_bird(session)

    companies = [
        CompanyInput(
            company_name=c.company_name,
            city=c.city,
            industry=c.industry,
            reason=c.reason,
        )
        for c in payload.companies
    ]

    try:
        items = await BatchDrafter().draft_batch(
            companies=companies,
            early_bird=early_bird,
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Nepodarilo sa pripraviť dávku emailov.",
        )

    return BatchDraftResponse(
        count=len(items),
        items=[
            BatchDraftItem(
                company_name=i.company_name,
                city=i.city,
                industry=i.industry,
                subject=i.subject,
                body=i.body,
            )
            for i in items
        ],
    )


# ══════════════════════════════════════════════════════════════
# PENDING / SEND / SKIP  — automaticky outreach workflow
# ══════════════════════════════════════════════════════════════


class PendingCandidateItem(BaseModel):
    id: str
    company_name: str
    ico: str | None = None
    city: str | None = None
    industry: str | None = None
    email: str | None = None
    subject: str | None = None
    body: str | None = None
    status: str
    created_at: str | None = None


class PendingCandidatesResponse(BaseModel):
    count: int
    items: list[PendingCandidateItem]


class DraftNewRequest(BaseModel):
    """Davkovy draft pre kandidatov so statusom new."""

    limit: int = Field(default=30, ge=1, le=50)


class DraftNewResponse(BaseModel):
    drafted: int
    failed: int
    skipped: int


class AutoApproveRequest(BaseModel):
    """Automaticke schvalenie kandidatov s platnym emailom."""

    limit: int = Field(default=100, ge=1, le=500)
    dry_run: bool = Field(default=False)


class AutoApproveResponse(BaseModel):
    approved: int
    skipped_no_email: int
    skipped_junk: int
    skipped_invalid: int
    total_checked: int
    sample_approved: list[dict]


class AutoSendBatchRequest(BaseModel):
    """Batch send s oneskorenim medzi emailmi (rate limit safe)."""

    limit: int = Field(default=30, ge=1, le=50)
    delay_seconds: float = Field(default=2.0, ge=0.5, le=10.0)


class AutoSendBatchResponse(BaseModel):
    sent: int
    failed: int
    skipped: int
    total_checked: int
    duration_seconds: float


class ApproveCandidateRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=20000)


class ApproveCandidateResponse(BaseModel):
    ok: bool
    message: str
    status: str


class SendCandidateResponse(BaseModel):
    ok: bool
    message: str
    status: str = "sent"


class BackfillEmailsItem(BaseModel):
    company_name: str
    ico: str | None = None
    website: str | None = None
    email: str | None = None
    reason: str


class BackfillEmailsResponse(BaseModel):
    ok: bool
    processed: int
    found: int
    no_website: int
    no_email_on_website: int
    failed: int
    items: list[BackfillEmailsItem] = []


@router.post("/backfill-emails", response_model=BackfillEmailsResponse)
async def backfill_emails_endpoint(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
    limit: int = 35,
) -> BackfillEmailsResponse:
    """Doplní chýbajúce verejné firemné emaily existujúcim kandidátom.

    Web -> verejný firemný email -> Zlaté stránky fallback -> DB.
    Nič neposiela.
    Limit max 100, default 35.
    """
    _require_admin(current_user)

    from app.modules.lead_finder.application.services.backfill_emails import (
        backfill_emails,
    )

    result = await backfill_emails(session, limit=limit)
    return BackfillEmailsResponse(**result)


@router.post("/discover-categories", response_model=DiscoverCategoriesResponse)
async def discover_categories(
    payload: DiscoverCategoriesRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> DiscoverCategoriesResponse:
    """Spusti category discovery z Zlatých stránok. Admin only.

    Prejde zadané kategórie (default: odpady, Recyklácia, kovový odpad),
    vytvorí nových kandidátov s verejným emailom z karty. Nikdy
    neposiela email a nikdy nevymýšľa adresu.
    """
    _require_admin(current_user)

    from app.modules.lead_finder.application.services.daily_discover import (
        run_category_discover,
    )

    result = await run_category_discover(
        session,
        categories=payload.categories,
        max_pages_per_category=payload.max_pages,
    )
    await session.commit()

    _fire_and_forget(
        TelegramService.notify_discovery(
            saved=result["saved"],
            duplicates=result["duplicates"],
            per_category=result.get("per_category") or {},
        )
    )

    return DiscoverCategoriesResponse(**result)


def _pending_item(r) -> PendingCandidateItem:
    return PendingCandidateItem(
        id=r.id,
        company_name=r.company_name,
        ico=r.ico,
        city=r.city,
        industry=r.industry,
        email=r.email,
        subject=r.draft_subject,
        body=r.draft_body,
        status=r.status.value,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )


@router.get("/pending", response_model=PendingCandidatesResponse)
async def list_pending_candidates(
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
    limit: int = 50,
    include_new: bool = False,
):
    """Vrati kandidatov cakajucich na odoslanie (drafted + approved).

    Ak `include_new=True`, pribudnu aj kandidati so statusom `new` —
    teda firmy, ktore objavila discovery, ale email draft pre ne este
    nikto nevytvoril. Admin ich vidi v tom istom zozname a jednym
    klikom pre ne pripravi drafty (POST /draft-new).

    Default `False` zachovava presne povodne spravanie endpointu.
    """
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)

    rows = await repo.list_by_status(
        status=OutreachStatus.DRAFTED,
        limit=limit,
    )

    rows = [
        *rows,
        *await repo.list_by_status(
            status=OutreachStatus.APPROVED,
            limit=limit,
        ),
    ]

    if include_new:
        rows = [
            *rows,
            *await repo.list_by_status(
                status=OutreachStatus.NEW,
                limit=limit,
            ),
        ]

    # Najnovsie hore. Pri rovnakom created_at drzime poradie new pred
    # drafted (cakaju na akciu), aby sa zoznam pri refreshi neskakal.
    rows = sorted(
        rows,
        key=lambda row: (row.created_at, row.status == OutreachStatus.NEW),
        reverse=True,
    )[:limit]

    items = [_pending_item(r) for r in rows]

    return PendingCandidatesResponse(count=len(items), items=items)


DRAFT_NEW_CHUNK = 5


@router.post("/draft-new", response_model=DraftNewResponse)
async def draft_new_candidates(
    payload: DraftNewRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> DraftNewResponse:
    """Pripravi drafty pre kandidatov so statusom `new`.

    Discovery vytvara kandidatov bez draftu — admin sa sam rozhodne,
    kedy pre nich email pripravit. Tento endpoint je ta davkova akcia:
    zoberie max `limit` (max 50) firiem so statusom `new`, pre kazdu
    zavola EmailDrafter.draft() a ulozi vysledok cez repo.update_draft()
    (ktory kandidata posunie do `drafted`).

    Bezi po CHUNKOCH (DRAFT_NEW_CHUNK) aby sme jednorazovo nespalili
    AI kvotu. Nikdy neposiela email.

    `skipped` = kandidati, ktori draft dostali uz predtym (napr. medzi
    nami dvaja admini) alebo medzitym zmizli — preskocime ich namiesto
    prepisovania hotovej prace.
    """
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)

    candidates = await repo.list_by_status(
        status=OutreachStatus.NEW,
        limit=payload.limit,
    )

    if not candidates:
        return DraftNewResponse(drafted=0, failed=0, skipped=0)

    early_bird = await _is_early_bird(session)
    drafter = EmailDrafter()

    drafted = 0
    failed = 0
    skipped = 0

    for start in range(0, len(candidates), DRAFT_NEW_CHUNK):
        chunk = candidates[start : start + DRAFT_NEW_CHUNK]

        for candidate in chunk:
            # Stav sa mohol medzitym zmenit (iny admin, iny beh).
            # Nikdy neprepisujeme existujuci draft ani iny stav.
            if candidate.status != OutreachStatus.NEW:
                skipped += 1
                continue

            try:
                draft = await drafter.draft(
                    company_name=candidate.company_name,
                    city=candidate.city,
                    industry=candidate.industry,
                    reason=None,
                    early_bird=early_bird,
                )
            except Exception:
                # draft() ma vlastny deterministicky fallback, takze sem
                # sa dostaneme len pri skutocne neocakavanej chybe.
                logger.exception(
                    "draft-new zlyhal pre kandidata %s",
                    candidate.ico,
                )
                failed += 1
                continue

            updated = await repo.update_draft(
                candidate_id=candidate.id,
                subject=draft.subject,
                body=draft.body,
            )

            if updated is None:
                # Kandidat medzitym zmizol — neratame ako draft.
                skipped += 1
                continue

            drafted += 1

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.draft_new",
        target_type="outreach_candidate",
        target_id=None,
        details=f"drafted={drafted},failed={failed},skipped={skipped}",
    )

    _fire_and_forget(
        TelegramService.notify_drafts(
            drafted=drafted,
            failed=failed,
            skipped=skipped,
        )
    )

    if drafted:
        DRAFTS_TOTAL.labels(result="ok").inc(drafted)
    if failed:
        DRAFTS_TOTAL.labels(result="failed").inc(failed)
    if skipped:
        DRAFTS_TOTAL.labels(result="skipped").inc(skipped)

    return DraftNewResponse(drafted=drafted, failed=failed, skipped=skipped)


@router.post("/auto-approve", response_model=AutoApproveResponse)
async def auto_approve_candidates(
    payload: AutoApproveRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> AutoApproveResponse:
    """Hromadne schval kandidatov s platnym emailom. Admin only.

    Kandidati so statusom `new`, ktori maju platny email (nie junk,
    nie invalid), sa posunu na `approved`. Zvysok zostava v `new`
    a caka na manualne rozhodnutie.

    Idempotentne — opatovne spustenie nic nepokazi.

    Ak dry_run=True, len reportuje co by sa stalo (ziadne zmeny).
    """
    _require_admin(current_user)

    from app.modules.lead_finder.application.services.auto_approve import (
        run_auto_approve,
    )

    result = await run_auto_approve(
        session,
        limit=payload.limit,
        dry_run=payload.dry_run,
    )

    if not payload.dry_run:
        await session.commit()

        # Telegram notifikacia (fire-and-forget)
        _fire_and_forget(
            TelegramService.notify(
                f"✅ <b>Auto-approve</b>\n"
                f"Schválených: <b>{result['approved']}</b>\n"
                f"Bez emailu: {result['skipped_no_email']}\n"
                f"Junk: {result['skipped_junk']}\n"
                f"Invalid: {result['skipped_invalid']}"
            )
        )

    return AutoApproveResponse(**result)


@router.post("/auto-send-batch", response_model=AutoSendBatchResponse)
async def auto_send_batch(
    payload: AutoSendBatchRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> AutoSendBatchResponse:
    """Batch send schvalenych kandidatov s oneskorenim. Admin only.

    Posiela `approved` kandidatov jeden po druhom s `delay_seconds`
    pauzou medzi requestami. Riesi Resend rate limit (2 req/s).

    Max 50 emailov za jeden beh. Pri 2s delay to trva ~2 minuty.

    Nikdy neposiela na `new` alebo `drafted` kandidatov — tie musia
    byt najprv schvalene (auto-approve alebo manualne).
    """
    import time as _time

    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    started = _time.monotonic()
    repo = SqlAlchemyOutreachCandidateRepository(session)

    candidates = await repo.list_by_status(
        status=OutreachStatus.APPROVED,
        limit=payload.limit,
    )

    if not candidates:
        return AutoSendBatchResponse(
            sent=0,
            failed=0,
            skipped=0,
            total_checked=0,
            duration_seconds=0.0,
        )

    sent = 0
    failed = 0
    skipped = 0

    for i, candidate in enumerate(candidates):
        if not candidate.email:
            skipped += 1
            continue

        try:
            result = await send_via_resend(
                session=session,
                to=candidate.email,
                subject=candidate.draft_subject or f"Pozvánka na CMEP pre {candidate.company_name}",
                body=candidate.draft_body or "",
            )

            if result.ok:
                await repo.update_status(
                    candidate_id=candidate.id,
                    status=OutreachStatus.SENT,
                )
                sent += 1
            else:
                failed += 1
                logger.warning(
                    "auto-send-batch: %s -> %s failed: %s",
                    candidate.company_name,
                    candidate.email,
                    result.message,
                )
        except Exception:
            failed += 1
            logger.exception("auto-send-batch exception pre %s", candidate.email)

        # Delay medzi emailmi (okrem posledneho)
        if i < len(candidates) - 1:
            await asyncio.sleep(payload.delay_seconds)

    await session.commit()

    duration = _time.monotonic() - started

    # Telegram notifikacia
    _fire_and_forget(
        TelegramService.notify(
            f"📧 <b>Batch send hotový</b>\n"
            f"Odoslaných: <b>{sent}</b>\n"
            f"Zlyhalo: {failed}\n"
            f"Preskočených: {skipped}\n"
            f"Trvanie: {duration:.1f}s"
        )
    )

    if sent:
        SEND_TOTAL.labels(result="ok").inc(sent)
    if failed:
        SEND_TOTAL.labels(result="failed").inc(failed)

    PIPELINE_DURATION.labels(stage="send_batch").observe(duration)

    return AutoSendBatchResponse(
        sent=sent,
        failed=failed,
        skipped=skipped,
        total_checked=len(candidates),
        duration_seconds=round(duration, 1),
    )


@router.post(
    "/candidates/{candidate_id}/approve",
    response_model=ApproveCandidateResponse,
)
async def approve_candidate(
    candidate_id: str,
    payload: ApproveCandidateRequest,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> ApproveCandidateResponse:
    """Ulozi skontrolovane udaje a nastavi kandidata na APPROVED."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)

    candidate = await repo.get_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Kandidat sa nenasiel",
        )

    # Draft mozeme schvalit.
    # Approved mozeme znovu schvalit, ak administrator zmenil
    # email/predmet pred opakovaným odoslanim.
    if candidate.status not in (
        OutreachStatus.DRAFTED,
        OutreachStatus.APPROVED,
    ):
        raise HTTPException(
            status_code=409,
            detail=(f"Kandidata nie je mozne schvalit v tomto stave: {candidate.status.value}"),
        )

    email = payload.email.strip().lower()
    subject = payload.subject.strip()
    body = payload.body.strip()

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=422,
            detail="Neplatny email.",
        )

    if not subject:
        raise HTTPException(
            status_code=422,
            detail="Chyba predmet emailu.",
        )

    if not body:
        raise HTTPException(
            status_code=422,
            detail="Chyba telo emailu.",
        )

    # Najprv ulozime presne to, co administrator skontroloval.
    await repo.update_email(
        candidate_id=candidate_id,
        email=email,
    )

    await repo.update_draft(
        candidate_id=candidate_id,
        subject=subject,
        body=body,
    )

    updated = await repo.update_status(
        candidate_id=candidate_id,
        status=OutreachStatus.APPROVED,
    )

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Kandidat sa nenasiel",
        )

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.approve_candidate",
        target_type="outreach_candidate",
        target_id=candidate_id,
        details=f"to={email},company={candidate.company_name}",
    )

    return ApproveCandidateResponse(
        ok=True,
        message="Kandidat bol schvaleny na odoslanie.",
        status=OutreachStatus.APPROVED.value,
    )


@router.post(
    "/candidates/{candidate_id}/send",
    response_model=SendCandidateResponse,
)
async def send_candidate_email(
    candidate_id: str,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SendCandidateResponse:
    """Odosle iba APPROVED kandidata a pouzije udaje ulozene v DB."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)

    candidate = await repo.get_by_id(candidate_id)

    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail="Kandidat sa nenasiel",
        )

    # Toto je hlavna ochrana proti obchadzaniu approval workflow.
    if candidate.status != OutreachStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail=(f"Kandidat musi byt najprv schvaleny. Aktualny stav: {candidate.status.value}"),
        )

    # SEND NESMIE POUZIVAT DATA Z REQUESTU.
    # Pouzivame iba data, ktore boli ulozene pri approve.
    to = (candidate.email or "").strip().lower()
    subject = (candidate.draft_subject or "").strip()
    body = (candidate.draft_body or "").strip()

    if "@" not in to or "." not in to.rsplit("@", 1)[-1]:
        raise HTTPException(
            status_code=422,
            detail="Schvaleny kandidat nema platny email.",
        )

    if not subject:
        raise HTTPException(
            status_code=422,
            detail="Schvaleny kandidat nema predmet emailu.",
        )

    if not body:
        raise HTTPException(
            status_code=422,
            detail="Schvaleny kandidat nema telo emailu.",
        )

    result = await send_via_resend(
        session=session,
        to=to,
        subject=subject,
        body=body,
    )

    if not result.ok:
        if "nie je nakonfigurovany" in result.message:
            ok = send_email(
                to=to,
                subject=subject,
                body=body,
            )

            if not ok:
                return SendCandidateResponse(
                    ok=False,
                    message="SMTP zlyhalo.",
                )
        else:
            return SendCandidateResponse(
                ok=False,
                message=result.message,
            )

    updated = await repo.update_status(
        candidate_id=candidate_id,
        status=OutreachStatus.SENT,
    )

    if updated is None:
        raise HTTPException(
            status_code=500,
            detail=("Email bol odoslany, ale stav kandidata sa nepodarilo ulozit."),
        )

    await write_audit(
        session=session,
        actor_user_id=current_user_id(current_user),
        action="lead_outreach.send_candidate",
        target_type="outreach_candidate",
        target_id=candidate_id,
        details=f"to={to},company={candidate.company_name}",
    )

    await write_activity_event(
        session=session,
        event_type="lead_outreach.send",
        actor_user_id=current_user_id(current_user),
        company_id=None,
        listing_id=None,
        payload=f"to={to},company={candidate.company_name}",
    )

    remaining = getattr(result, "remaining_today", None)

    msg = result.message if result.ok else "Email odoslany cez SMTP."

    if remaining is not None:
        msg = f"{msg} Zostava dnes: {remaining}."

    return SendCandidateResponse(
        ok=True,
        message=msg,
        status=OutreachStatus.SENT.value,
    )


class SkipCandidateResponse(BaseModel):
    ok: bool
    status: str


@router.post("/candidates/{candidate_id}/skip", response_model=SkipCandidateResponse)
async def skip_candidate(
    candidate_id: str,
    current_user=Depends(require_current_user),
    session=Depends(get_db_session),
) -> SkipCandidateResponse:
    """Preskoci kandidata (status -> skipped)."""
    _require_admin(current_user)

    from app.modules.lead_finder.domain.entities.outreach_candidate import (
        OutreachStatus,
    )
    from app.modules.lead_finder.infrastructure.persistence.repositories import (
        SqlAlchemyOutreachCandidateRepository,
    )

    repo = SqlAlchemyOutreachCandidateRepository(session)
    candidate = await repo.get_by_id(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Kandidat sa nenasiel")

    await repo.update_status(
        candidate_id=candidate_id,
        status=OutreachStatus.SKIPPED,
    )
    return SkipCandidateResponse(ok=True, status="skipped")
