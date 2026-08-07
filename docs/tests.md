# ============================================
# FILE: app/tests/conftest.py
# ============================================
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

# ============================================
# FILE: app/tests/unit/users/test_user_entity.py
# ============================================
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.shared.domain.exceptions import InvalidTransitionDomainError, ValidationDomainError


def build_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="user@example.com",
        password_hash="hashed",
        first_name="John",
        last_name="Doe",
        display_name=None,
        phone=None,
        locale="sk",
        timezone="Europe/Bratislava",
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )


def test_user_validate_accepts_valid_user():
    user = build_user()
    user.validate()


def test_user_validate_rejects_invalid_email():
    user = build_user()
    user.email = "invalid-email"

    with pytest.raises(ValidationDomainError):
        user.validate()


def test_user_transition_active_to_suspended():
    user = build_user()

    user.transition_status(UserStatus.SUSPENDED)

    assert user.status == UserStatus.SUSPENDED


def test_user_transition_deactivated_is_terminal():
    user = build_user()
    user.status = UserStatus.DEACTIVATED

    with pytest.raises(InvalidTransitionDomainError):
        user.transition_status(UserStatus.ACTIVE)

# ============================================
# FILE: app/tests/unit/companies/test_company_entity.py
# ============================================
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.shared.domain.exceptions import InvalidTransitionDomainError, ValidationDomainError


def build_company() -> Company:
    now = datetime.now(timezone.utc)
    return Company(
        id=uuid4(),
        status=CompanyStatus.DRAFT,
        legal_name="Acme Recycling s.r.o.",
        trading_name="Acme Recycling",
        registration_number="12345678",
        tax_identifier="SK1234567890",
        company_type=CompanyType.SELLER_BUYER,
        email="info@acme.test",
        phone="+421900000000",
        website_url="https://acme.test",
        country_code="SK",
        address_line_1="Main 1",
        address_line_2=None,
        city="Presov",
        postal_code="08001",
        latitude=None,
        longitude=None,
        seller_capability=True,
        buyer_capability=True,
        logistics_capability=False,
        verification_submitted_at=None,
        verification_reviewed_at=None,
        verification_reviewed_by_user_id=None,
        verified_at=None,
        verified_by_user_id=None,
        rejected_at=None,
        rejected_by_user_id=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )


def test_company_validate_requires_capability():
    company = build_company()
    company.seller_capability = False
    company.buyer_capability = False
    company.logistics_capability = False

    with pytest.raises(ValidationDomainError):
        company.validate()


def test_company_transition_draft_to_verification_submitted():
    company = build_company()

    company.transition_status(CompanyStatus.VERIFICATION_SUBMITTED)

    assert company.status == CompanyStatus.VERIFICATION_SUBMITTED


def test_company_transition_verified_to_draft_is_invalid():
    company = build_company()
    company.status = CompanyStatus.VERIFIED

    with pytest.raises(InvalidTransitionDomainError):
        company.transition_status(CompanyStatus.DRAFT)

# ============================================
# FILE: app/tests/unit/auth/test_refresh_session_entity.py
# ============================================
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.modules.auth.domain.entities import RefreshSession


def test_refresh_session_entity_fields_are_assignable():
    now = datetime.now(timezone.utc)
    entity = RefreshSession(
        id=uuid4(),
        user_id=uuid4(),
        token_family_id="family-1",
        refresh_token_jti="jti-1",
        refresh_token_hash="hash-1",
        expires_at=now + timedelta(days=30),
        revoked_at=None,
        replaced_by_jti=None,
        reuse_detected_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )

    assert entity.token_family_id == "family-1"
    assert entity.revoked_at is None

# ============================================
# FILE: app/tests/unit/users/test_user_services.py
# ============================================
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.modules.users.application.services import CreateUserService, GetUserService, TransitionUserStatusService
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import ConflictDomainError, NotFoundDomainError


class FakeUserRepository:
    def __init__(self):
        self.by_id = {}
        self.by_email = {}

    async def add(self, user):
        self.by_id[user.id] = user
        self.by_email[user.email] = user

    async def get_by_id(self, user_id):
        return self.by_id.get(user_id)

    async def get_by_email(self, email):
        return self.by_email.get(email)

    async def list(self, *, status, company_id, q, page, page_size):
        return list(self.by_id.values()), len(self.by_id)

    async def update(self, user):
        self.by_id[user.id] = user
        self.by_email[user.email] = user


class FixedClock(Clock):
    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


class FixedUuidGenerator(UuidGenerator):
    def __init__(self, value):
        self._value = value

    def new(self):
        return self._value


@pytest.mark.asyncio
async def test_create_user_service_creates_user():
    now = datetime.now(timezone.utc)
    user_id = uuid4()
    repo = FakeUserRepository()
    service = CreateUserService(repo=repo, uuid_generator=FixedUuidGenerator(user_id), clock=FixedClock(now))

    result = await service.execute(
        email="new@example.com",
        password_hash="hashed",
        first_name="New",
        last_name="User",
        display_name=None,
        phone=None,
        locale="sk",
        timezone="Europe/Bratislava",
        actor_user_id=None,
    )

    assert result.id == user_id
    assert result.email == "new@example.com"
    assert result.status == "active"


@pytest.mark.asyncio
async def test_create_user_service_rejects_duplicate_email():
    now = datetime.now(timezone.utc)
    repo = FakeUserRepository()
    existing = User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="existing@example.com",
        password_hash="hashed",
        first_name="Existing",
        last_name="User",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )
    await repo.add(existing)

    service = CreateUserService(repo=repo, uuid_generator=FixedUuidGenerator(uuid4()), clock=FixedClock(now))

    with pytest.raises(ConflictDomainError):
        await service.execute(
            email="existing@example.com",
            password_hash="hashed",
            first_name="A",
            last_name="B",
            display_name=None,
            phone=None,
            locale=None,
            timezone=None,
            actor_user_id=None,
        )


@pytest.mark.asyncio
async def test_get_user_service_raises_for_missing_user():
    repo = FakeUserRepository()
    service = GetUserService(repo=repo)

    with pytest.raises(NotFoundDomainError):
        await service.execute(uuid4())


@pytest.mark.asyncio
async def test_transition_user_status_service_updates_status():
    now = datetime.now(timezone.utc)
    repo = FakeUserRepository()
    user = User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="a@example.com",
        password_hash="hashed",
        first_name="A",
        last_name="B",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )
    await repo.add(user)

    service = TransitionUserStatusService(repo=repo, clock=FixedClock(now))

    result = await service.execute(user_id=user.id, to_status="suspended", actor_user_id=None)

    assert result.status == "suspended"

# ============================================
# FILE: app/tests/unit/companies/test_company_services.py
# ============================================
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.modules.companies.application.services import CreateCompanyService, GetCompanyService
from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


class FakeCompanyRepository:
    def __init__(self):
        self.by_id = {}

    async def add(self, company):
        self.by_id[company.id] = company

    async def get_by_id(self, company_id):
        return self.by_id.get(company_id)

    async def list(self, **kwargs):
        values = list(self.by_id.values())
        return values, len(values)

    async def update(self, company):
        self.by_id[company.id] = company


class FixedClock(Clock):
    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


class FixedUuidGenerator(UuidGenerator):
    def __init__(self, value):
        self._value = value

    def new(self):
        return self._value


@pytest.mark.asyncio
async def test_create_company_service_creates_draft_company():
    now = datetime.now(timezone.utc)
    company_id = uuid4()
    repo = FakeCompanyRepository()
    service = CreateCompanyService(repo=repo, uuid_generator=FixedUuidGenerator(company_id), clock=FixedClock(now))

    result = await service.execute(
        legal_name="Acme",
        trading_name="Acme",
        registration_number="123",
        tax_identifier=None,
        company_type="seller_buyer",
        email="info@acme.test",
        phone=None,
        website_url=None,
        country_code="sk",
        address_line_1="Main 1",
        address_line_2=None,
        city="Presov",
        postal_code="08001",
        latitude=None,
        longitude=None,
        seller_capability=True,
        buyer_capability=True,
        logistics_capability=False,
        actor_user_id=None,
    )

    assert result.id == company_id
    assert result.status == "draft"
    assert result.country_code == "SK"


@pytest.mark.asyncio
async def test_get_company_service_raises_when_missing():
    repo = FakeCompanyRepository()
    service = GetCompanyService(repo=repo)

    with pytest.raises(NotFoundDomainError):
        await service.execute(uuid4())

# ============================================
# FILE: app/tests/unit/auth/test_auth_services.py
# ============================================
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.modules.auth.application.services import GetCurrentAuthContextService, LoginService, LogoutService, RefreshTokenService
from app.modules.auth.domain.entities import RefreshSession
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import UnauthorizedDomainError


class FakeUserRepository:
    def __init__(self, user=None):
        self.user = user

    async def add(self, user):
        self.user = user

    async def get_by_id(self, user_id):
        if self.user and self.user.id == user_id:
            return self.user
        return None

    async def get_by_email(self, email):
        if self.user and self.user.email == email:
            return self.user
        return None

    async def list(self, **kwargs):
        return ([self.user] if self.user else []), 1 if self.user else 0

    async def update(self, user):
        self.user = user


class FakeRefreshRepository:
    def __init__(self):
        self.sessions = {}

    async def add(self, session):
        self.sessions[session.refresh_token_jti] = session

    async def get_by_jti(self, jti):
        return self.sessions.get(jti)

    async def get_active_by_user_id(self, user_id):
        return [s for s in self.sessions.values() if s.user_id == user_id and s.revoked_at is None]

    async def update(self, session):
        self.sessions[session.refresh_token_jti] = session

    async def revoke_family(self, family_id, revoked_at):
        for session in self.sessions.values():
            if session.token_family_id == family_id and session.revoked_at is None:
                session.revoked_at = revoked_at
                session.updated_at = revoked_at


class FakeMembership:
    def __init__(self, id, company_id):
        from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
        self.id = id
        self.company_id = company_id
        self.membership_role = CompanyMembershipRole.ADMIN
        self.status = CompanyMembershipStatus.ACTIVE
        self.is_primary_contact = True


class FakeMembershipRepository:
    async def list_by_user_id(self, user_id):
        return [FakeMembership(uuid4(), uuid4())]


class FixedClock(Clock):
    def __init__(self, now):
        self._now = now

    def now(self):
        return self._now


class SequencedUuidGenerator(UuidGenerator):
    def __init__(self, values):
        self.values = list(values)

    def new(self):
        return self.values.pop(0)


class FakeJwtService:
    def issue_access_token(self, subject, extra_claims=None):
        return "access-token", datetime.now(timezone.utc) + timedelta(minutes=15)

    def issue_refresh_token(self, subject, family_id, extra_claims=None):
        return "refresh-token", "refresh-jti", datetime.now(timezone.utc) + timedelta(days=30)

    def decode(self, token):
        if token == "refresh-token":
          return {"sub": str(self.user_id), "type": "refresh", "jti": "refresh-jti", "family_id": "family-id"}
        if token == "access-token":
          return {"sub": str(self.user_id), "type": "access", "jti": "access-jti"}
        raise UnauthorizedDomainError("Invalid token")

    def set_user_id(self, user_id):
        self.user_id = user_id


@pytest.mark.asyncio
async def test_login_service_returns_token_pair():
    now = datetime.now(timezone.utc)
    password_service = PasswordService()
    user = User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="user@example.com",
        password_hash=password_service.hash_password("password123"),
        first_name="John",
        last_name="Doe",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )
    user_repo = FakeUserRepository(user)
    refresh_repo = FakeRefreshRepository()
    jwt_service = FakeJwtService()
    jwt_service.set_user_id(user.id)

    service = LoginService(
        user_repo=user_repo,
        refresh_repo=refresh_repo,
        membership_repo=FakeMembershipRepository(),
        password_service=password_service,
        jwt_service=jwt_service,
        uuid_generator=SequencedUuidGenerator([uuid4(), uuid4()]),
        clock=FixedClock(now),
    )

    result = await service.execute(email="user@example.com", password="password123")

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"
    assert result.token_type == "Bearer"


@pytest.mark.asyncio
async def test_login_service_rejects_bad_password():
    now = datetime.now(timezone.utc)
    password_service = PasswordService()
    user = User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="user@example.com",
        password_hash=password_service.hash_password("password123"),
        first_name="John",
        last_name="Doe",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )
    user_repo = FakeUserRepository(user)
    jwt_service = FakeJwtService()
    jwt_service.set_user_id(user.id)

    service = LoginService(
        user_repo=user_repo,
        refresh_repo=FakeRefreshRepository(),
        membership_repo=FakeMembershipRepository(),
        password_service=password_service,
        jwt_service=jwt_service,
        uuid_generator=SequencedUuidGenerator([uuid4(), uuid4()]),
        clock=FixedClock(now),
    )

    with pytest.raises(UnauthorizedDomainError):
        await service.execute(email="user@example.com", password="wrongpass")


@pytest.mark.asyncio
async def test_get_current_auth_context_service_returns_memberships():
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        status=UserStatus.ACTIVE,
        email="user@example.com",
        password_hash="hashed",
        first_name="John",
        last_name="Doe",
        display_name=None,
        phone=None,
        locale=None,
        timezone=None,
        last_login_at=None,
        created_at=now,
        created_by_user_id=None,
        updated_at=now,
        updated_by_user_id=None,
    )
    jwt_service = FakeJwtService()
    jwt_service.set_user_id(user.id)

    service = GetCurrentAuthContextService(
        user_repo=FakeUserRepository(user),
        membership_repo=FakeMembershipRepository(),
        jwt_service=jwt_service,
    )

    result = await service.execute("access-token")

    assert result.user.email == "user@example.com"
    assert len(result.memberships) == 1


@pytest.mark.asyncio
async def test_logout_service_revokes_refresh_family():
    jwt_service = FakeJwtService()
    user_id = uuid4()
    jwt_service.set_user_id(user_id)
    refresh_repo = FakeRefreshRepository()
    now = datetime.now(timezone.utc)

    session = RefreshSession(
        id=uuid4(),
        user_id=user_id,
        token_family_id="family-id",
        refresh_token_jti="refresh-jti",
        refresh_token_hash="hash",
        expires_at=now + timedelta(days=30),
        revoked_at=None,
        replaced_by_jti=None,
        reuse_detected_at=None,
        created_at=now,
        created_by_user_id=user_id,
        updated_at=now,
        updated_by_user_id=user_id,
    )
    await refresh_repo.add(session)

    service = LogoutService(refresh_repo=refresh_repo, jwt_service=jwt_service, clock=FixedClock(now))
    await service.execute(refresh_token="refresh-token")

    assert refresh_repo.sessions["refresh-jti"].revoked_at == now


@pytest.mark.asyncio
async def test_refresh_token_service_rotates_refresh_token():
    now = datetime.now(timezone.utc)
    refresh_repo = FakeRefreshRepository()
    jwt_service = FakeJwtService()
    user_id = uuid4()
    jwt_service.set_user_id(user_id)

    original = RefreshSession(
        id=uuid4(),
        user_id=user_id,
        token_family_id="family-id",
        refresh_token_jti="refresh-jti",
        refresh_token_hash=LoginService._hash_token("refresh-token"),
        expires_at=now + timedelta(days=30),
        revoked_at=None,
        replaced_by_jti=None,
        reuse_detected_at=None,
        created_at=now,
        created_by_user_id=user_id,
        updated_at=now,
        updated_by_user_id=user_id,
    )
    await refresh_repo.add(original)

    service = RefreshTokenService(
        refresh_repo=refresh_repo,
        jwt_service=jwt_service,
        clock=FixedClock(now),
    )

    result = await service.execute(refresh_token="refresh-token")

    assert result.access_token == "access-token"
    assert result.refresh_token == "refresh-token"
    assert refresh_repo.sessions["refresh-jti"].revoked_at == now

# ============================================
# FILE: app/tests/integration/test_users_api.py
# ============================================
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.main import app


class FakeAuthContext:
    def __init__(self):
        user_id = uuid4()
        self.user = type("CurrentUser", (), {"id": user_id, "email": "admin@example.com", "first_name": "Admin", "last_name": "User"})()
        self.role_codes = ["platform_admin"]
        self.memberships = []


@pytest.mark.asyncio
async def test_get_users_returns_paginated_shape(async_client, monkeypatch):
    from app.shared.presentation.auth_dependencies import require_current_user
    from app.modules.users.presentation.dependencies import get_list_users_service

    async def override_current_user():
        return FakeAuthContext()

    class StubService:
        async def execute(self, *, status, company_id, q, page, page_size):
            now = datetime.now(timezone.utc)
            dto = type(
                "UserDTOStub",
                (),
                {
                    "id": uuid4(),
                    "status": "active",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": None,
                    "phone": None,
                    "locale": "sk",
                    "timezone": "Europe/Bratislava",
                    "last_login_at": None,
                    "created_at": now,
                    "created_by_user_id": None,
                    "updated_at": now,
                    "updated_by_user_id": None,
                },
            )()
            return [dto], 1

    app.dependency_overrides[require_current_user] = override_current_user
    app.dependency_overrides[get_list_users_service] = lambda: StubService()

    response = await async_client.get("/api/v1/users")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 1
    assert payload["items"]["email"] == "user@example.com"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_user_returns_201(async_client):
    from app.shared.presentation.auth_dependencies import require_current_user
    from app.modules.users.presentation.dependencies import get_create_user_service, get_password_service

    async def override_current_user():
        return FakeAuthContext()

    class StubPasswordService:
        def hash_password(self, raw_password):
            return f"hashed::{raw_password}"

    class StubService:
        async def execute(self, **kwargs):
            now = datetime.now(timezone.utc)
            return type(
                "UserDTOStub",
                (),
                {
                    "id": uuid4(),
                    "status": "active",
                    "email": kwargs["email"],
                    "first_name": kwargs["first_name"],
                    "last_name": kwargs["last_name"],
                    "display_name": kwargs["display_name"],
                    "phone": kwargs["phone"],
                    "locale": kwargs["locale"],
                    "timezone": kwargs["timezone"],
                    "last_login_at": None,
                    "created_at": now,
                    "created_by_user_id": kwargs["actor_user_id"],
                    "updated_at": now,
                    "updated_by_user_id": kwargs["actor_user_id"],
                },
            )()

    app.dependency_overrides[require_current_user] = override_current_user
    app.dependency_overrides[get_create_user_service] = lambda: StubService()
    app.dependency_overrides[get_password_service] = lambda: StubPasswordService()

    response = await async_client.post(
        "/api/v1/users",
        json={
            "email": "new@example.com",
            "password": "password123",
            "firstName": "New",
            "lastName": "User",
            "displayName": "New User",
            "phone": "+421900000000",
            "locale": "sk",
            "timezone": "Europe/Bratislava",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["email"] == "new@example.com"
    assert payload["data"]["firstName"] == "New"

    app.dependency_overrides.clear()

# ============================================
# FILE: app/tests/integration/test_companies_api.py
# ============================================
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.main import app


class FakeAuthContext:
    def __init__(self):
        user_id = uuid4()
        self.user = type("CurrentUser", (), {"id": user_id, "email": "admin@example.com", "first_name": "Admin", "last_name": "User"})()
        self.role_codes = ["platform_admin"]
        self.memberships = []


@pytest.mark.asyncio
async def test_get_companies_returns_paginated_shape(async_client):
    from app.shared.presentation.auth_dependencies import require_current_user
    from app.modules.companies.presentation.dependencies import get_list_companies_service

    async def override_current_user():
        return FakeAuthContext()

    class StubService:
        async def execute(self, **kwargs):
            now = datetime.now(timezone.utc)
            dto = type(
                "CompanyDTOStub",
                (),
                {
                    "id": uuid4(),
                    "status": "verified",
                    "legal_name": "Acme Recycling",
                    "trading_name": "Acme",
                    "registration_number": "123",
                    "tax_identifier": None,
                    "company_type": "seller_buyer",
                    "email": "info@acme.test",
                    "phone": None,
                    "website_url": None,
                    "country_code": "SK",
                    "address_line_1": "Main 1",
                    "address_line_2": None,
                    "city": "Presov",
                    "postal_code": "08001",
                    "latitude": None,
                    "longitude": None,
                    "seller_capability": True,
                    "buyer_capability": True,
                    "logistics_capability": False,
                    "verification_submitted_at": None,
                    "verification_reviewed_at": None,
                    "verification_reviewed_by_user_id": None,
                    "verified_at": None,
                    "verified_by_user_id": None,
                    "rejected_at": None,
                    "rejected_by_user_id": None,
                    "created_at": now,
                    "created_by_user_id": None,
                    "updated_at": now,
                    "updated_by_user_id": None,
                },
            )()
            return [dto], 1

    app.dependency_overrides[require_current_user] = override_current_user
    app.dependency_overrides[get_list_companies_service] = lambda: StubService()

    response = await async_client.get("/api/v1/companies")

    assert response.status_code == 200
    payload = response.json()
    assert payload["meta"]["total"] == 1
    assert payload["items"]["legalName"] == "Acme Recycling"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_company_returns_201(async_client):
    from app.shared.presentation.auth_dependencies import require_current_user
    from app.modules.companies.presentation.dependencies import get_create_company_service

    async def override_current_user():
        return FakeAuthContext()

    class StubService:
        async def execute(self, **kwargs):
            now = datetime.now(timezone.utc)
            return type(
                "CompanyDTOStub",
                (),
                {
                    "id": uuid4(),
                    "status": "draft",
                    "legal_name": kwargs["legal_name"],
                    "trading_name": kwargs["trading_name"],
                    "registration_number": kwargs["registration_number"],
                    "tax_identifier": kwargs["tax_identifier"],
                    "company_type": kwargs["company_type"],
                    "email": kwargs["email"],
                    "phone": kwargs["phone"],
                    "website_url": kwargs["website_url"],
                    "country_code": kwargs["country_code"].upper(),
                    "address_line_1": kwargs["address_line_1"],
                    "address_line_2": kwargs["address_line_2"],
                    "city": kwargs["city"],
                    "postal_code": kwargs["postal_code"],
                    "latitude": kwargs["latitude"],
                    "longitude": kwargs["longitude"],
                    "seller_capability": kwargs["seller_capability"],
                    "buyer_capability": kwargs["buyer_capability"],
                    "logistics_capability": kwargs["logistics_capability"],
                    "verification_submitted_at": None,
                    "verification_reviewed_at": None,
                    "verification_reviewed_by_user_id": None,
                    "verified_at": None,
                    "verified_by_user_id": None,
                    "rejected_at": None,
                    "rejected_by_user_id": None,
                    "created_at": now,
                    "created_by_user_id": kwargs["actor_user_id"],
                    "updated_at": now,
                    "updated_by_user_id": kwargs["actor_user_id"],
                },
            )()

    app.dependency_overrides[require_current_user] = override_current_user
    app.dependency_overrides[get_create_company_service] = lambda: StubService()

    response = await async_client.post(
        "/api/v1/companies",
        json={
            "legalName": "Acme Recycling",
            "tradingName": "Acme",
            "registrationNumber": "12345678",
            "taxIdentifier": "SK123",
            "companyType": "seller_buyer",
            "email": "info@acme.test",
            "phone": "+421900000000",
            "websiteUrl": "https://acme.test",
            "countryCode": "sk",
            "addressLine1": "Main 1",
            "addressLine2": null,
            "city": "Presov",
            "postalCode": "08001",
            "latitude": null,
            "longitude": null,
            "sellerCapability": true,
            "buyerCapability": true,
            "logisticsCapability": false
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["data"]["status"] == "draft"
    assert payload["data"]["legalName"] == "Acme Recycling"

    app.dependency_overrides.clear()

# ============================================
# FILE: app/tests/integration/test_auth_api.py
# ============================================
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.main import app


@pytest.mark.asyncio
async def test_login_endpoint_returns_tokens(async_client):
    from app.modules.auth.presentation.dependencies import get_login_service

    class StubService:
        async def execute(self, *, email, password):
            return type(
                "AuthTokenPairDTOStub",
                (),
                {
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "token_type": "Bearer",
                    "expires_in": 900,
                },
            )()

    app.dependency_overrides[get_login_service] = lambda: StubService()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accessToken"] == "access-token"
    assert payload["refreshToken"] == "refresh-token"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_refresh_endpoint_returns_rotated_tokens(async_client):
    from app.modules.auth.presentation.dependencies import get_refresh_token_service

    class StubService:
        async def execute(self, *, refresh_token):
            return type(
                "AuthTokenPairDTOStub",
                (),
                {
                    "access_token": "new-access-token",
                    "refresh_token": "new-refresh-token",
                    "token_type": "Bearer",
                    "expires_in": 900,
                },
            )()

    app.dependency_overrides[get_refresh_token_service] = lambda: StubService()

    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": "old-refresh-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accessToken"] == "new-access-token"
    assert payload["refreshToken"] == "new-refresh-token"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logout_endpoint_returns_204(async_client):
    from app.modules.auth.presentation.dependencies import get_logout_service

    class StubService:
        async def execute(self, *, refresh_token):
            return None

    app.dependency_overrides[get_logout_service] = lambda: StubService()

    response = await async_client.post(
        "/api/v1/auth/logout",
        json={"refreshToken": "refresh-token"},
    )

    assert response.status_code == 204

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_me_endpoint_returns_current_context(async_client):
    from app.shared.presentation.auth_dependencies import require_current_user

    class FakeAuthContext:
        def __init__(self):
            user_id = uuid4()
            now = datetime.now(timezone.utc)
            self.user = type(
                "UserDTOStub",
                (),
                {
                    "id": user_id,
                    "status": "active",
                    "email": "user@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "display_name": None,
                    "phone": None,
                    "locale": "sk",
                    "timezone": "Europe/Bratislava",
                    "last_login_at": None,
                    "created_at": now,
                    "created_by_user_id": None,
                    "updated_at": now,
                    "updated_by_user_id": None,
                },
            )()
            self.role_codes = ["platform_admin"]
            self.memberships = [
                {
                    "id": uuid4(),
                    "companyId": uuid4(),
                    "membershipRole": "admin",
                    "status": "active",
                    "isPrimaryContact": True,
                }
            ]

    async def override_current_user():
        return FakeAuthContext()

    app.dependency_overrides[require_current_user] = override_current_user

    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer access-token"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["email"] == "user@example.com"
    assert payload["roleCodes"] == ["platform_admin"]
    assert len(payload["memberships"]) == 1

    app.dependency_overrides.clear()

# ============================================
# FILE: apps/web/package.json
# ============================================
{
  "name": "@cmep/web",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev --port 3001",
    "build": "next build",
    "start": "next start --port 3001",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.9.0",
    "@tanstack/react-query": "^5.59.0",
    "@tanstack/react-query-devtools": "^5.59.0",
    "clsx": "^2.1.1",
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-hook-form": "^7.53.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.1",
    "@testing-library/user-event": "^14.5.2",
    "@types/node": "^22.8.1",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.2",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.1",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vitest": "^2.1.3"
  }
}

# ============================================
# FILE: apps/web/vitest.config.ts
# ============================================
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/__tests__/setup.ts"]
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src")
    }
  }
});

# ============================================
# FILE: apps/web/src/__tests__/setup.ts
# ============================================
import "@testing-library/jest-dom";
import { vi } from "vitest";

Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn()
  }))
});

# ============================================
# FILE: apps/web/src/__tests__/test-utils.tsx
# ============================================
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactElement } from "react";
import { render } from "@testing-library/react";

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0
      },
      mutations: {
        retry: false
      }
    }
  });
}

export function renderWithQueryClient(ui: ReactElement) {
  const queryClient = createTestQueryClient();

  return {
    queryClient,
    ...render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
  };
}

# ============================================
# FILE: apps/web/src/__tests__/auth/token-store.test.ts
# ============================================
import { beforeEach, describe, expect, it } from "vitest";

import { clearTokens, getAccessToken, getRefreshToken, setTokens } from "@/lib/auth/token-store";

describe("token-store", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("stores and retrieves tokens", () => {
    setTokens({
      accessToken: "access-token",
      refreshToken: "refresh-token"
    });

    expect(getAccessToken()).toBe("access-token");
    expect(getRefreshToken()).toBe("refresh-token");
  });

  it("clears tokens", () => {
    setTokens({
      accessToken: "access-token",
      refreshToken: "refresh-token"
    });

    clearTokens();

    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/use-login.test.tsx
# ============================================
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClientProvider } from "@tanstack/react-query";

import { createTestQueryClient } from "@/__tests__/test-utils";
import { useLogin } from "@/features/auth/hooks/use-login";

vi.mock("@/features/auth/api", () => ({
  login: vi.fn(async () => ({
    accessToken: "access-token",
    refreshToken: "refresh-token",
    tokenType: "Bearer",
    expiresIn: 900
  }))
}));

describe("useLogin", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("stores tokens after successful login", async () => {
    const queryClient = createTestQueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useLogin(), { wrapper });

    result.current.mutate({ email: "user@example.com", password: "password123" });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
      expect(window.localStorage.getItem("cmep_access_token")).toBe("access-token");
      expect(window.localStorage.getItem("cmep_refresh_token")).toBe("refresh-token");
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/use-current-user.test.tsx
# ============================================
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { QueryClientProvider } from "@tanstack/react-query";

import { createTestQueryClient } from "@/__tests__/test-utils";
import { useCurrentUser } from "@/features/auth/hooks/use-current-user";

vi.mock("@/features/auth/api", () => ({
  getCurrentUser: vi.fn(async () => ({
    user: {
      id: "u1",
      status: "active",
      email: "user@example.com",
      firstName: "John",
      lastName: "Doe",
      createdAt: "2026-01-01T00:00:00Z",
      updatedAt: "2026-01-01T00:00:00Z"
    },
    roleCodes: ["platform_admin"],
    memberships: []
  }))
}));

describe("useCurrentUser", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem("cmep_access_token", "access-token");
  });

  it("fetches current user when access token exists", async () => {
    const queryClient = createTestQueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCurrentUser(), { wrapper });

    await waitFor(() => {
      expect(result.current.data?.user.email).toBe("user@example.com");
      expect(result.current.isSuccess).toBe(true);
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/login-form.test.tsx
# ============================================
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/features/auth/components/login-form";

const mutateAsync = vi.fn(async () => undefined);
const replace = vi.fn();

vi.mock("@/features/auth/hooks/use-login", () => ({
  useLogin: () => ({
    mutateAsync,
    isPending: false,
    error: null
  })
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

describe("LoginForm", () => {
  it("submits login form values", async () => {
    const user = userEvent.setup();
    render(<LoginForm />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(mutateAsync).toHaveBeenCalledWith({
      email: "user@example.com",
      password: "password123"
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/register-form.test.tsx
# ============================================
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { RegisterForm } from "@/features/auth/components/register-form";

const mutateAsync = vi.fn(async () => undefined);
const replace = vi.fn();

vi.mock("@/features/auth/hooks/use-register", () => ({
  useRegister: () => ({
    mutateAsync,
    isPending: false,
    error: null
  })
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

describe("RegisterForm", () => {
  it("submits registration form values", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText("First name"), "John");
    await user.type(screen.getByLabelText("Last name"), "Doe");
    await user.type(screen.getByLabelText("Email"), "john@example.com");
    await user.type(screen.getByLabelText("Password"), "password123");
    await user.click(screen.getByRole("button", { name: "Create account" }));

    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        email: "john@example.com",
        password: "password123",
        firstName: "John",
        lastName: "Doe"
      })
    );
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/use-logout.test.tsx
# ============================================
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { createTestQueryClient } from "@/__tests__/test-utils";
import { useLogout } from "@/features/auth/hooks/use-logout";

const replace = vi.fn();

vi.mock("@/features/auth/api", () => ({
  logout: vi.fn(async () => undefined)
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

describe("useLogout", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.localStorage.setItem("cmep_access_token", "access-token");
    window.localStorage.setItem("cmep_refresh_token", "refresh-token");
    replace.mockReset();
  });

  it("clears tokens and redirects to login", async () => {
    const queryClient = createTestQueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useLogout(), { wrapper });
    result.current.mutate();

    await waitFor(() => {
      expect(window.localStorage.getItem("cmep_access_token")).toBeNull();
      expect(window.localStorage.getItem("cmep_refresh_token")).toBeNull();
      expect(replace).toHaveBeenCalledWith("/login");
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/listings/use-listings.test.tsx
# ============================================
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { createTestQueryClient } from "@/__tests__/test-utils";
import { useListings } from "@/features/listings/hooks/use-listings";

vi.mock("@/features/listings/api", () => ({
  getListings: vi.fn(async () => ({
    items: [
      {
        id: "l1",
        status: "published",
        materialCategory: "plastics",
        materialSubtype: "PET",
        quantity: 100,
        unit: "kg",
        originLocation: "Presov",
        priceModel: "fixed",
        sellerCompanyId: "c1",
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-01T00:00:00Z"
      }
    ],
    meta: {
      page: 1,
      pageSize: 20,
      total: 1
    }
  }))
}));

describe("useListings", () => {
  it("fetches listing collection", async () => {
    const queryClient = createTestQueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useListings({ page: 1, pageSize: 20 }), { wrapper });

    await waitFor(() => {
      expect(result.current.data?.items.materialSubtype).toBe("PET");
      expect(result.current.data?.meta.total).toBe(1);
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/listings/listings-table.test.tsx
# ============================================
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ListingsTable } from "@/features/listings/components/listings-table";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>
}));

describe("ListingsTable", () => {
  it("renders listing rows", () => {
    render(
      <ListingsTable
        rows={[
          {
            id: "l1",
            status: "published",
            materialCategory: "plastics",
            materialSubtype: "PET",
            quantity: 100,
            unit: "kg",
            purityIndicator: "95%",
            contaminationNotes: "",
            originLocation: "Presov",
            pickupTerms: "",
            deliveryTerms: "",
            availabilityStart: null,
            availabilityEnd: null,
            priceModel: "fixed",
            sellerCompanyId: "c1",
            createdAt: "2026-01-01T00:00:00Z",
            updatedAt: "2026-01-01T00:00:00Z"
          }
        ]}
      />
    );

    expect(screen.getByText("plastics")).toBeInTheDocument();
    expect(screen.getByText("PET")).toBeInTheDocument();
    expect(screen.getByText("100 kg")).toBeInTheDocument();
    expect(screen.getByText("Detail")).toBeInTheDocument();
  });
});

# ============================================
# FILE: apps/web/src/__tests__/listings/listing-form.test.tsx
# ============================================
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ListingForm } from "@/features/listings/components/listing-form";

const push = vi.fn();
const replace = vi.fn();
const back = vi.fn();
const createMutateAsync = vi.fn(async () => ({ data: { id: "listing-1" } }));
const updateMutateAsync = vi.fn(async () => ({ data: { id: "listing-1" } }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push,
    replace,
    back
  })
}));

vi.mock("@/features/listings/hooks/use-create-listing", () => ({
  useCreateListing: () => ({
    mutateAsync: createMutateAsync,
    isPending: false,
    error: null
  })
}));

vi.mock("@/features/listings/hooks/use-update-listing", () => ({
  useUpdateListing: () => ({
    mutateAsync: updateMutateAsync,
    isPending: false,
    error: null
  })
}));

describe("ListingForm", () => {
  it("submits create listing form", async () => {
    const user = userEvent.setup();

    render(<ListingForm mode="create" />);

    await user.type(screen.getByLabelText("Material category"), "plastics");
    await user.type(screen.getByLabelText("Material subtype"), "PET");
    await user.type(screen.getByLabelText("Quantity"), "100");
    await user.type(screen.getByLabelText("Unit"), "kg");
    await user.type(screen.getByLabelText("Price model"), "fixed");
    await user.type(screen.getByLabelText("Seller company ID"), "company-1");
    await user.type(screen.getByLabelText("Origin location"), "Presov");
    await user.click(screen.getByRole("button", { name: "Create listing" }));

    expect(createMutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        materialCategory: "plastics",
        materialSubtype: "PET",
        quantity: 100,
        unit: "kg",
        priceModel: "fixed",
        sellerCompanyId: "company-1",
        originLocation: "Presov"
      })
    );
    expect(replace).toHaveBeenCalledWith("/listings/listing-1");
  });
});

# ============================================
# FILE: apps/web/src/__tests__/companies/use-companies.test.tsx
# ============================================
import { waitFor } from "@testing-library/react";
import { renderHook } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";

import { createTestQueryClient } from "@/__tests__/test-utils";
import { useCompanies } from "@/features/companies/hooks/use-companies";

vi.mock("@/features/companies/api", () => ({
  getCompanies: vi.fn(async () => ({
    items: [
      {
        id: "c1",
        status: "verified",
        legalName: "Acme Recycling",
        tradingName: "Acme",
        registrationNumber: "12345678",
        companyType: "seller_buyer",
        countryCode: "SK",
        addressLine1: "Main 1",
        city: "Presov",
        postalCode: "08001",
        sellerCapability: true,
        buyerCapability: true,
        logisticsCapability: false,
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-01T00:00:00Z"
      }
    ],
    meta: {
      page: 1,
      pageSize: 20,
      total: 1
    }
  }))
}));

describe("useCompanies", () => {
  it("fetches company collection", async () => {
    const queryClient = createTestQueryClient();
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useCompanies({ page: 1, pageSize: 20 }), { wrapper });

    await waitFor(() => {
      expect(result.current.data?.items.legalName).toBe("Acme Recycling");
      expect(result.current.data?.meta.total).toBe(1);
    });
  });
});

# ============================================
# FILE: apps/web/src/__tests__/companies/companies-table.test.tsx
# ============================================
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CompaniesTable } from "@/features/companies/components/companies-table";

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a>
}));

describe("CompaniesTable", () => {
  it("renders company rows", () => {
    render(
      <CompaniesTable
        rows={[
          {
            id: "c1",
            status: "verified",
            legalName: "Acme Recycling",
            tradingName: "Acme",
            registrationNumber: "12345678",
            taxIdentifier: null,
            companyType: "seller_buyer",
            email: "info@acme.test",
            phone: null,
            websiteUrl: null,
            countryCode: "SK",
            addressLine1: "Main 1",
            addressLine2: null,
            city: "Presov",
            postalCode: "08001",
            latitude: null,
            longitude: null,
            sellerCapability: true,
            buyerCapability: true,
            logisticsCapability: false,
            verificationSubmittedAt: null,
            verificationReviewedAt: null,
            verificationReviewedByUserId: null,
            verifiedAt: null,
            verifiedByUserId: null,
            rejectedAt: null,
            rejectedByUserId: null,
            createdAt: "2026-01-01T00:00:00Z",
            createdByUserId: null,
            updatedAt: "2026-01-01T00:00:00Z",
            updatedByUserId: null
          }
        ]}
      />
    );

    expect(screen.getByText("Acme Recycling")).toBeInTheDocument();
    expect(screen.getByText("12345678")).toBeInTheDocument();
    expect(screen.getByText("seller_buyer")).toBeInTheDocument();
    expect(screen.getByText("Detail")).toBeInTheDocument();
  });
});

# ============================================
# FILE: apps/web/src/__tests__/auth/use-auth-required.test.tsx
# ============================================
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { useAuthRequired } from "@/features/auth/hooks/use-auth-required";

const replace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

vi.mock("@/features/auth/hooks/use-current-user", () => ({
  useCurrentUser: vi.fn(() => ({
    isError: false,
    data: undefined
  }))
}));

describe("useAuthRequired", () => {
  beforeEach(() => {
    replace.mockReset();
    window.localStorage.clear();
  });

  it("redirects to login when token is missing", async () => {
    renderHook(() => useAuthRequired());

    await waitFor(() => {
      expect(replace).toHaveBeenCalledWith("/login");
    });
  });
});
