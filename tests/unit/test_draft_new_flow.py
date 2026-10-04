"""Testy pre POST /admin/lead-outreach/draft-new.

Admin sam rozhoduje, kedy sa pre "new" kandidatov (z ZS discovery)
pripravia drafty. Tento endpoint to robi davkovo, po chunkoch,
s deterministickym fallbackom.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.main import app


def test_draft_new_endpoint_exists():
    """Endpoint /draft-new je v OpenAPI a ma spravnu response schema."""
    schema = app.openapi()
    assert "/api/v1/admin/lead-outreach/draft-new" in schema["paths"]
    path = schema["paths"]["/api/v1/admin/lead-outreach/draft-new"]
    assert "post" in path


def test_draft_new_request_model_validation():
    """Limit je 1..50, default 30."""
    from app.modules.lead_finder.presentation.router import DraftNewRequest

    req = DraftNewRequest()
    assert req.limit == 30

    with pytest.raises(ValidationError):
        DraftNewRequest(limit=0)

    with pytest.raises(ValidationError):
        DraftNewRequest(limit=51)


def test_draft_new_response_model():
    """Response ma drafted/failed/skipped."""
    from app.modules.lead_finder.presentation.router import DraftNewResponse

    res = DraftNewResponse(drafted=5, failed=1, skipped=0)
    assert res.drafted == 5
    assert res.failed == 1
    assert res.skipped == 0


def test_draft_new_chunk_size_is_reasonable():
    """Chunk nesmie byt prilis velky (rate limit Groq)."""
    from app.modules.lead_finder.presentation.router import DRAFT_NEW_CHUNK

    assert 1 <= DRAFT_NEW_CHUNK <= 10
