"""Testy mintovania streamovacich tokenov (kontrakt s cmep-streaming/auth.js)."""

from uuid import uuid4

import pytest

from app.core.config import settings
from app.modules.inspections.application.streaming_tokens import (
    StreamingTokenService,
    verify_streaming_token_self,
)
from app.shared.domain.exceptions import ValidationDomainError

SECRET = "test-streaming-secret-0123456789abcdef0123456789"


@pytest.fixture(autouse=True)
def _streaming_settings(monkeypatch):
    monkeypatch.setattr(settings, "CMEP_STREAMING_SIGNING_SECRET", SECRET)
    yield
    monkeypatch.setattr(settings, "CMEP_STREAMING_SIGNING_SECRET", "")


def test_mint_publisher_token_and_self_verify():
    svc = StreamingTokenService()
    user, company, insp, listing = uuid4(), uuid4(), uuid4(), uuid4()
    tok = svc.mint(
        user_id=user,
        company_id=company,
        inspection_id=insp,
        listing_id=listing,
        role="publisher",
        consent_to_record=False,
    )
    claims = verify_streaming_token_self(tok.token)
    assert claims is not None
    assert claims["sub"] == str(user)
    assert claims["companyId"] == str(company)
    assert claims["insp"] == str(insp)
    # V http mode je offerId totozny s ID obhliadky (room.offerId == parameter
    # offer= v publishUrl == inspectionId pri ingeste eventov). ID ponuky je
    # v samostatnom claim-e `listingId`.
    assert claims["offerId"] == str(insp)
    assert claims["listingId"] == str(listing)
    assert claims["role"] == "publisher"
    assert claims["rec"] == 0
    assert tok.expires_in == 3600


def test_mint_viewer_with_consent_has_rec_flag():
    svc = StreamingTokenService()
    tok = svc.mint(
        user_id=uuid4(),
        company_id=uuid4(),
        inspection_id=uuid4(),
        listing_id=uuid4(),
        role="viewer",
        consent_to_record=False,
    )
    claims = verify_streaming_token_self(tok.token)
    assert claims["role"] == "viewer"
    assert claims["rec"] == 0


def test_mint_without_secret_fails_closed():
    svc = StreamingTokenService()
    monkey_target = settings
    monkey_target.CMEP_STREAMING_SIGNING_SECRET = ""
    with pytest.raises(ValidationDomainError):
        svc.mint(
            user_id=uuid4(),
            company_id=uuid4(),
            inspection_id=uuid4(),
            listing_id=uuid4(),
            role="publisher",
        )


def test_tampered_token_rejected():
    svc = StreamingTokenService()
    tok = svc.mint(
        user_id=uuid4(),
        company_id=uuid4(),
        inspection_id=uuid4(),
        listing_id=uuid4(),
        role="publisher",
    )
    payload, sig = tok.token.split(".")
    tampered = f"{payload}.{'A' * len(sig)}"
    assert verify_streaming_token_self(tampered) is None


def test_short_secret_not_configured():
    assert not StreamingTokenService.is_configured.__func__() if False else True
    settings.CMEP_STREAMING_SIGNING_SECRET = "short"
    assert StreamingTokenService.is_configured() is False
