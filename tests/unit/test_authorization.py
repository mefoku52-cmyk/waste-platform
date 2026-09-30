"""Unit tests for shared/presentation/authorization.py.

Pokryva: current_user_*, role_codes, is_platform_admin,
membership helpers, require_platform_admin, require_company_*.
"""

from dataclasses import dataclass, field

import pytest

from app.shared.domain.exceptions import ForbiddenDomainError
from app.shared.presentation import authorization as authz


@dataclass
class FakeUser:
    id: str = "user-1"
    email: str = "user@example.com"


@dataclass
class FakeMembership:
    companyId: str = "company-1"
    membershipRole: str = "owner"


@dataclass
class FakeCurrentUser:
    id: str = "user-1"
    email: str = "user@example.com"
    roleCodes: list = field(default_factory=list)
    memberships: list = field(default_factory=list)


def test_current_user_id_from_direct():
    cu = FakeCurrentUser(id="u-1")
    assert authz.current_user_id(cu) == "u-1"


def test_current_user_id_from_nested_user():
    @dataclass
    class Wrapper:
        user: FakeUser

    cu = Wrapper(user=FakeUser(id="u-2"))
    assert authz.current_user_id(cu) == "u-2"


def test_current_user_id_returns_none_when_no_id():
    @dataclass
    class NoId:
        pass

    assert authz.current_user_id(NoId()) is None


def test_current_user_email_lowercase():
    cu = FakeCurrentUser(email="USER@EXAMPLE.COM")
    assert authz.current_user_email(cu) == "user@example.com"


def test_role_codes_from_roleCodes_lowercase():
    cu = FakeCurrentUser(roleCodes=["Owner", "ADMIN"])
    assert authz.role_codes(cu) == {"owner", "admin"}


def test_role_codes_from_role_codes_alias():
    @dataclass
    class AliasUser:
        role_codes: list = field(default_factory=lambda: ["Platform_Admin"])

    assert authz.role_codes(AliasUser()) == {"platform_admin"}


def test_is_platform_admin_by_role():
    cu = FakeCurrentUser(roleCodes=["platform_admin"])
    assert authz.is_platform_admin(cu) is True


def test_is_platform_admin_false_for_owner():
    cu = FakeCurrentUser(roleCodes=["owner"])
    assert authz.is_platform_admin(cu) is False


def test_is_platform_admin_none_user():
    assert authz.is_platform_admin(None) is False


def test_is_platform_admin_by_email(monkeypatch):
    """Platform admin sa urci aj podla emailu (nie len role)."""
    monkeypatch.setattr(
        authz,
        "_platform_admin_emails",
        lambda: frozenset({"admin@example.com"}),
    )
    cu = FakeCurrentUser(email="admin@example.com")
    assert authz.is_platform_admin(cu) is True


def test_is_platform_admin_by_email_uppercase(monkeypatch):
    monkeypatch.setattr(
        authz,
        "_platform_admin_emails",
        lambda: frozenset({"admin@example.com"}),
    )
    cu = FakeCurrentUser(email="ADMIN@EXAMPLE.COM")
    assert authz.is_platform_admin(cu) is True


def test_is_not_platform_admin_for_other_email(monkeypatch):
    monkeypatch.setattr(
        authz,
        "_platform_admin_emails",
        lambda: frozenset({"admin@example.com"}),
    )
    cu = FakeCurrentUser(email="random@example.com")
    assert authz.is_platform_admin(cu) is False


def test_memberships_empty_by_default():
    cu = FakeCurrentUser()
    assert authz.memberships(cu) == []


def test_memberships_returns_list():
    m = FakeMembership()
    cu = FakeCurrentUser(memberships=[m])
    assert authz.memberships(cu) == [m]


def test_membership_company_ids():
    cu = FakeCurrentUser(
        memberships=[
            FakeMembership(companyId="c-1"),
            FakeMembership(companyId="c-2"),
        ]
    )
    assert authz.membership_company_ids(cu) == ["c-1", "c-2"]


def test_membership_role_in_company():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="admin")])
    assert authz.membership_role_in_company(cu, "c-1") == "admin"


def test_membership_role_not_member_returns_none():
    cu = FakeCurrentUser()
    assert authz.membership_role_in_company(cu, "c-99") is None


def test_is_company_member_true():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1")])
    assert authz.is_company_member(cu, "c-1") is True


def test_is_company_member_false():
    cu = FakeCurrentUser()
    assert authz.is_company_member(cu, "c-1") is False


def test_is_company_member_none_company():
    cu = FakeCurrentUser()
    assert authz.is_company_member(cu, None) is False


def test_is_company_admin_owner():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="owner")])
    assert authz.is_company_admin(cu, "c-1") is True


def test_is_company_admin_admin():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="admin")])
    assert authz.is_company_admin(cu, "c-1") is True


def test_is_company_admin_member_not_admin():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="member")])
    assert authz.is_company_admin(cu, "c-1") is False


def test_require_platform_admin_passes_for_platform_admin():
    cu = FakeCurrentUser(roleCodes=["platform_admin"])
    assert authz.require_platform_admin(cu) is cu


def test_require_platform_admin_raises_for_tenant_owner():
    cu = FakeCurrentUser(roleCodes=["owner"])
    with pytest.raises(ForbiddenDomainError):
        authz.require_platform_admin(cu)


def test_require_company_member_platform_admin_passes():
    cu = FakeCurrentUser(roleCodes=["platform_admin"])
    authz.require_company_member(cu, "c-any")


def test_require_company_member_member_passes():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1")])
    authz.require_company_member(cu, "c-1")


def test_require_company_member_raises_for_non_member():
    cu = FakeCurrentUser()
    with pytest.raises(ForbiddenDomainError):
        authz.require_company_member(cu, "c-1")


def test_require_company_admin_owner_passes():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="owner")])
    authz.require_company_admin(cu, "c-1")


def test_require_company_admin_raises_for_plain_member():
    cu = FakeCurrentUser(memberships=[FakeMembership(companyId="c-1", membershipRole="member")])
    with pytest.raises(ForbiddenDomainError):
        authz.require_company_admin(cu, "c-1")


def test_platform_admin_role_codes_constant():
    assert "platform_admin" in authz.PLATFORM_ADMIN_ROLE_CODES


def test_company_admin_roles_constant():
    assert "owner" in authz.COMPANY_ADMIN_ROLES
    assert "admin" in authz.COMPANY_ADMIN_ROLES
