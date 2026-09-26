"""Batch outreach drafting.

Legal B2B outreach. Admin supplies a list of companies.
AI drafts one personalized email per company.
Never auto-sends.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.agent_platform.infrastructure.ai.groq_gateway import GroqModelGateway
from app.modules.lead_finder.application.services.email_drafter import (
    DraftedEmail,
    EmailDrafter,
)


@dataclass(frozen=True, slots=True)
class CompanyInput:
    company_name: str
    city: str | None = None
    industry: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class BatchDraftItem:
    company_name: str
    city: str | None
    industry: str | None
    subject: str
    body: str


class BatchDrafter:
    """Drafts N emails in sequence.

    Limits: MAX_BATCH = 30 (daily limit). Never more.
    """

    MAX_BATCH = 30

    def __init__(self, *, gateway: GroqModelGateway | None = None) -> None:
        self._drafter = EmailDrafter(gateway=gateway)

    async def draft_batch(
        self,
        *,
        companies: list[CompanyInput],
        early_bird: bool = False,
    ) -> list[BatchDraftItem]:
        out: list[BatchDraftItem] = []
        for c in companies[: self.MAX_BATCH]:
            try:
                draft: DraftedEmail = await self._drafter.draft(
                    company_name=c.company_name,
                    city=c.city,
                    industry=c.industry,
                    reason=c.reason,
                    early_bird=early_bird,
                )
            except Exception:
                continue
            out.append(
                BatchDraftItem(
                    company_name=c.company_name,
                    city=c.city,
                    industry=c.industry,
                    subject=draft.subject,
                    body=draft.body,
                )
            )
        return out
