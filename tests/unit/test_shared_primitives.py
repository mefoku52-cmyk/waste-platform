from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.modules.company_memberships.domain.enums import (
    CompanyMembershipRole,
    CompanyMembershipStatus,
)
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator


def test_clock_now_is_aware():
    assert Clock().now().tzinfo is not None


def test_uuid_generator_unique():
    gen = UuidGenerator()
    assert gen.new() != gen.new()


def test_password_hash_and_verify():
    hasher = PasswordService()
    hashed = hasher.hash_password("secret-pass")
    assert hasher.verify_password("secret-pass", hashed) is True
    assert hasher.verify_password("wrong", hashed) is False


def test_enums_iterable():
    for enum_cls in (
        CompanyStatus,
        CompanyType,
        CompanyMembershipRole,
        CompanyMembershipStatus,
    ):
        assert len(list(enum_cls)) >= 1
