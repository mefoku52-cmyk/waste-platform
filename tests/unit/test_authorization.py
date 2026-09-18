"""Unit tests for the centralised platform/tenant authorization module.

These tests pin down the security-critical distinction between:

* **platform admin** — global operator, derived only from
  `PLATFORM_ADMIN_EMAILS` or the reserved `platform_admin` role.
* **company admin** — tenant-level `owner`/`admin` inside one company.

The regression they guard against: `roleCodes` are built solely from company
memberships, so treating a membership role `admin` as a platform role let any
tenant admin perform platform-admin operations (privilege escalation).
"""

from __future__ import annotations

import pytest

from app.shared.domain.exceptions import ForbiddenDomainError
from app.shared.presentation.authorization import (
    current_user_email,
    current_user_id,
    is_company_admin,
    is_company_member,
    is_platform_admin,
    membership_company_ids,
    require_company_admin,
    require_company_member,
    require_platform_admin,
)

COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"
USER_ID = "33333333-3333-3333-3333-333333333333"


class _User:
    def __init__(self, email: str):
        self.id = USER_ID
        self.email = email


class _Context:
    """Mimics CurrentUserResponse: user + roleCodes + memberships."""

    def __init__(self, email: str, roles=None, memberships=None):
        self.user = _User(email)
        self.roleCodes = roles or []
        self.memberships = memberships or []

    # property used by some routers
    @property
    def id(self):  # pragma: no cover - only present on some DTOs
        return USER_ID


def _membership(company_id, role, status="active"):
    return {
        "id": "44444444-4444-4444-4444-444444444444",
        "companyId": company_id,
        "membershipRole": role,
        "status": status,
        "isPrimaryContact": False,
    }


@pytest.fixture
def admin_emails(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "root@cmep.dev", raising=False)


class TestPlatformAdmin:
    def test_email_in_allowlist_is_platform_admin(self, admin_emails):
        assert is_platform_admin(_Context("root@cmep.dev")) is True

    def test_email_allowlist_is_case_insensitive(self, admin_emails):
        assert is_platform_admin(_Context("ROOT@CMEP.DEV")) is True

    def test_reserved_platform_admin_role_is_platform_admin(self, admin_emails):
        assert is_platform_admin(_Context("other@x.sk", roles=["platform_admin"])) is True

    def test_tenant_admin_role_is_not_platform_admin(self, admin_emails):
        """Regression: membership role `admin` must NOT grant platform admin."""
        ctx = _Context(
            "tenant@x.sk", roles=["admin"], memberships=[_membership(COMPANY_A, "admin")]
        )
        assert is_platform_admin(ctx) is False

    def test_plain_user_is_not_platform_admin(self, admin_emails):
        ctx = _Context("user@x.sk", memberships=[_membership(COMPANY_A, "member")])
        assert is_platform_admin(ctx) is False

    def test_require_platform_admin_raises_for_tenant_admin(self, admin_emails):
        ctx = _Context("tenant@x.sk", roles=["admin"])
        with pytest.raises(ForbiddenDomainError):
            require_platform_admin(ctx)

    def test_require_platform_admin_allows_allowlisted_email(self, admin_emails):
        ctx = _Context("root@cmep.dev")
        assert require_platform_admin(ctx) is ctx


class TestTenantAuthorization:
    def test_membership_company_ids_reads_all_memberships(self, admin_emails):
        ctx = _Context(
            "user@x.sk",
            memberships=[_membership(COMPANY_A, "member"), _membership(COMPANY_B, "owner")],
        )
        assert set(membership_company_ids(ctx)) == {COMPANY_A, COMPANY_B}

    def test_company_admin_roles_owner_and_admin(self, admin_emails):
        assert is_company_admin(
            _Context("a@x.sk", memberships=[_membership(COMPANY_A, "owner")]), COMPANY_A
        )
        assert is_company_admin(
            _Context("a@x.sk", memberships=[_membership(COMPANY_A, "admin")]), COMPANY_A
        )

    def test_plain_member_is_not_company_admin(self, admin_emails):
        ctx = _Context("m@x.sk", memberships=[_membership(COMPANY_A, "member")])
        assert is_company_admin(ctx, COMPANY_A) is False
        assert is_company_member(ctx, COMPANY_A) is True

    def test_cross_tenant_access_is_denied(self, admin_emails):
        """A member of company A must not manage company B."""
        ctx = _Context("m@x.sk", memberships=[_membership(COMPANY_A, "owner")])
        with pytest.raises(ForbiddenDomainError):
            require_company_admin(ctx, COMPANY_B)
        with pytest.raises(ForbiddenDomainError):
            require_company_member(ctx, COMPANY_B)

    def test_platform_admin_passes_tenant_checks(self, admin_emails):
        ctx = _Context("root@cmep.dev")
        # no exception expected
        require_company_member(ctx, COMPANY_B)
        require_company_admin(ctx, COMPANY_B)

    def test_tenant_admin_limited_to_own_company(self, admin_emails):
        ctx = _Context("t@x.sk", memberships=[_membership(COMPANY_A, "admin")])
        require_company_admin(ctx, COMPANY_A)
        with pytest.raises(ForbiddenDomainError):
            require_company_admin(ctx, COMPANY_B)


class TestHelpers:
    def test_current_user_id_prefers_nested_user(self):
        assert current_user_id(_Context("a@x.sk")) == USER_ID

    def test_current_user_email_normalises(self):
        assert current_user_email(_Context("  MiXeD@X.sk ")) == "mixed@x.sk"
