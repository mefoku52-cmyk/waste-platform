"""Unit tests for AI Approval Workflow state machine and payload binding."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.modules.agent_platform.application.approval_service import (
    ApprovalService,
    ApprovalStatus,
    RiskLevel,
)


def test_create_and_approve():
    svc = ApprovalService()
    actor = uuid4()
    company = uuid4()
    req = svc.create(actor, company, "update_listing", {"id": "1"}, "Update title", RiskLevel.MEDIUM_RISK)
    assert req.status == ApprovalStatus.PENDING
    approved = svc.approve(req.id, company, actor)
    assert approved is not None
    assert approved.status == ApprovalStatus.APPROVED


def test_payload_hash_binding():
    svc = ApprovalService()
    actor = uuid4()
    company = uuid4()
    args = {"id": "1", "title": "Old"}
    req = svc.create(actor, company, "update_listing", args, "desc")
    svc.approve(req.id, company, actor)
    # Try to execute with changed args
    changed_hash = svc._hash_args({"id": "1", "title": "New"})
    result = svc.mark_executing(req.id, company, changed_hash)
    assert result is None  # should fail because hash differs


def test_expire():
    svc = ApprovalService()
    actor = uuid4()
    company = uuid4()
    req = svc.create(actor, company, "tool", {}, "desc", ttl_minutes=0)
    # Force expire
    req.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    got = svc.get(req.id, company)
    assert got is not None
    assert got.status == ApprovalStatus.EXPIRED


def test_cross_tenant():
    svc = ApprovalService()
    actor = uuid4()
    company_a = uuid4()
    company_b = uuid4()
    req = svc.create(actor, company_a, "tool", {}, "desc")
    assert svc.get(req.id, company_b) is None