import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.modules.auth.application.dto import AuthTokenPairDTO, CurrentAuthContextDTO
from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.company_memberships.domain.repositories import CompanyMembershipRepository
from app.modules.users.application.mappers import to_user_dto
from app.modules.users.domain.repositories import UserRepository
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import UnauthorizedDomainError


class LoginService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshSessionRepository,
        membership_repo: CompanyMembershipRepository,
        password_service: PasswordService,
        jwt_service,
        uuid_generator: UuidGenerator,
        clock: Clock,
    ):
        self.user_repo = user_repo
        self.refresh_repo = refresh_repo
        self.membership_repo = membership_repo
        self.password_service = password_service
        self.jwt_service = jwt_service
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(self, *, email: str, password: str) -> AuthTokenPairDTO:
        # DOČASNÝ MOCK – vráti token bez overenia databázy
        user_id = uuid4()
        access_token, access_expires_at = self.jwt_service.issue_access_token(
            subject=str(user_id),
            extra_claims={"email": email},
        )
        refresh_token, refresh_jti, refresh_expires_at = self.jwt_service.issue_refresh_token(
            subject=str(user_id),
            family_id=str(uuid4()),
        )
        expires_in = int((access_expires_at - datetime.now(timezone.utc)).total_seconds())
        return AuthTokenPairDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=max(expires_in, 1),
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


class RefreshTokenService:
    def __init__(
        self,
        refresh_repo: RefreshSessionRepository,
        jwt_service,
        clock: Clock,
    ):
        self.refresh_repo = refresh_repo
        self.jwt_service = jwt_service
        self.clock = clock

    async def execute(self, *, refresh_token: str) -> AuthTokenPairDTO:
        payload = self.jwt_service.decode(refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedDomainError("Invalid refresh token")
        jti = payload["jti"]
        family_id = payload["family_id"]
        sub = payload["sub"]

        session = await self.refresh_repo.get_by_jti(jti)
        if not session:
            raise UnauthorizedDomainError("Refresh session not found")

        token_hash = LoginService._hash_token(refresh_token)
        if session.refresh_token_hash != token_hash:
            await self.refresh_repo.revoke_family(family_id, self.clock.now())
            raise UnauthorizedDomainError("Refresh token reuse detected")

        if session.revoked_at is not None:
            await self.refresh_repo.revoke_family(family_id, self.clock.now())
            raise UnauthorizedDomainError("Refresh token already revoked")

        access_token, access_expires_at = self.jwt_service.issue_access_token(subject=sub)
        new_refresh_token, new_jti, refresh_expires_at = self.jwt_service.issue_refresh_token(subject=sub, family_id=family_id)

        now = self.clock.now()
        session.revoked_at = now
        session.replaced_by_jti = new_jti
        session.updated_at = now
        await self.refresh_repo.update(session)

        replacement = RefreshSession(
            id=uuid4(),
            user_id=UUID(sub),
            token_family_id=family_id,
            refresh_token_jti=new_jti,
            refresh_token_hash=LoginService._hash_token(new_refresh_token),
            expires_at=refresh_expires_at,
            revoked_at=None,
            replaced_by_jti=None,
            reuse_detected_at=None,
            created_at=now,
            created_by_user_id=UUID(sub),
            updated_at=now,
            updated_by_user_id=UUID(sub),
        )
        await self.refresh_repo.add(replacement)

        expires_in = int((access_expires_at - datetime.now(timezone.utc)).total_seconds())
        return AuthTokenPairDTO(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=max(expires_in, 1),
        )


class LogoutService:
    def __init__(self, refresh_repo: RefreshSessionRepository, jwt_service, clock: Clock):
        self.refresh_repo = refresh_repo
        self.jwt_service = jwt_service
        self.clock = clock

    async def execute(self, *, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        payload = self.jwt_service.decode(refresh_token)
        if payload.get("type") != "refresh":
            return
        await self.refresh_repo.revoke_family(payload["family_id"], self.clock.now())


class GetCurrentAuthContextService:
    def __init__(
        self,
        user_repo: UserRepository,
        membership_repo: CompanyMembershipRepository,
        jwt_service,
    ):
        self.user_repo = user_repo
        self.membership_repo = membership_repo
        self.jwt_service = jwt_service

    async def execute(self, access_token: str) -> CurrentAuthContextDTO:
        payload = self.jwt_service.decode(access_token)
        if payload.get("type") != "access":
            raise UnauthorizedDomainError("Invalid access token")
        user = await self.user_repo.get_by_id(UUID(payload["sub"]))
        if not user:
            raise UnauthorizedDomainError("Authenticated user not found")
        memberships = await self.membership_repo.list_by_user_id(user.id)
        return CurrentAuthContextDTO(
            user=to_user_dto(user),
            role_codes=[],
            memberships=[
                {
                    "id": item.id,
                    "companyId": item.company_id,
                    "membershipRole": item.membership_role.value,
                    "status": item.status.value,
                    "isPrimaryContact": item.is_primary_contact,
                }
                for item in memberships
            ],
        )
