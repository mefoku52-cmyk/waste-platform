# ============================================
# FILE: app/main.py
# ============================================
from fastapi import FastAPI

from app.shared.presentation.api_router import api_router
from app.shared.presentation.exception_handlers import register_exception_handlers

app = FastAPI(
    title="Circular Materials Exchange Platform API",
    version="0.1.0",
)

register_exception_handlers(app)
app.include_router(api_router)


# ============================================
# FILE: app/shared/presentation/api_router.py
# ============================================
from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.users.presentation.router import router as users_router
from app.modules.companies.presentation.router import router as companies_router
from app.modules.company_memberships.presentation.router import router as company_memberships_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(companies_router)
api_router.include_router(company_memberships_router)


# ============================================
# FILE: app/shared/domain/exceptions.py
# ============================================
class DomainError(Exception):
    code = "domain_error"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationDomainError(DomainError):
    code = "validation_error"


class NotFoundDomainError(DomainError):
    code = "not_found"


class ConflictDomainError(DomainError):
    code = "conflict"


class UnauthorizedDomainError(DomainError):
    code = "unauthorized"


class ForbiddenDomainError(DomainError):
    code = "forbidden"


class InvalidTransitionDomainError(DomainError):
    code = "invalid_transition"

    def __init__(self, message: str, current_status: str, attempted_status: str, allowed_transitions: list[str]):
        self.current_status = current_status
        self.attempted_status = attempted_status
        self.allowed_transitions = allowed_transitions
        super().__init__(message)


# ============================================
# FILE: app/shared/domain/base.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class AuditFields:
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by_user_id: UUID | None
    updated_by_user_id: UUID | None


# ============================================
# FILE: app/shared/domain/status_transition.py
# ============================================
from app.shared.domain.exceptions import InvalidTransitionDomainError


def ensure_transition(current: str, target: str, allowed: set[str]) -> None:
    if target not in allowed:
        raise InvalidTransitionDomainError(
            message=f"Invalid transition from {current} to {target}",
            current_status=current,
            attempted_status=target,
            allowed_transitions=sorted(list(allowed)),
        )


# ============================================
# FILE: app/shared/application/passwords.py
# ============================================
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordService:
    def hash_password(self, raw_password: str) -> str:
        return pwd_context.hash(raw_password)

    def verify_password(self, raw_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(raw_password, hashed_password)


# ============================================
# FILE: app/shared/application/clock.py
# ============================================
from datetime import datetime, timezone


class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


# ============================================
# FILE: app/shared/application/uuid_generator.py
# ============================================
from uuid import UUID, uuid4


class UuidGenerator:
    def new(self) -> UUID:
        return uuid4()


# ============================================
# FILE: app/shared/application/interfaces.py
# ============================================
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class SessionProvider(Protocol):
    async def __call__(self) -> AsyncSession:
        ...


# ============================================
# FILE: app/shared/infrastructure/db/base.py
# ============================================
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ============================================
# FILE: app/shared/infrastructure/db/session.py
# ============================================
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/cmep")

engine = create_async_engine(DATABASE_URL, future=True, pool_pre_ping=True)
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


# ============================================
# FILE: app/shared/infrastructure/security/jwt_service.py
# ============================================
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_TTL_MINUTES = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15"))
REFRESH_TOKEN_TTL_DAYS = int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30"))


class JwtService:
    def issue_access_token(self, subject: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "access",
            "jti": str(uuid4()),
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), expires_at

    def issue_refresh_token(self, subject: str, family_id: str, extra_claims: dict[str, Any] | None = None) -> tuple[str, str, datetime]:
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_TTL_DAYS)
        jti = str(uuid4())
        payload: dict[str, Any] = {
            "sub": subject,
            "type": "refresh",
            "jti": jti,
            "family_id": family_id,
            "exp": expires_at,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM), jti, expires_at

    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


# ============================================
# FILE: app/shared/presentation/schemas.py
# ============================================
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    correlationId: str | None = None
    details: dict[str, Any] | None = None


class FieldError(BaseModel):
    field: str
    message: str


class ValidationErrorResponse(ErrorResponse):
    fieldErrors: list[FieldError] = []


class InvalidTransitionErrorResponse(ErrorResponse):
    currentStatus: str
    attemptedStatus: str
    allowedTransitions: list[str]


# ============================================
# FILE: app/shared/presentation/exception_handlers.py
# ============================================
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.shared.domain.exceptions import (
    ConflictDomainError,
    ForbiddenDomainError,
    InvalidTransitionDomainError,
    NotFoundDomainError,
    UnauthorizedDomainError,
    ValidationDomainError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundDomainError)
    async def not_found_handler(request: Request, exc: NotFoundDomainError):
        return JSONResponse(status_code=404, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ConflictDomainError)
    async def conflict_handler(request: Request, exc: ConflictDomainError):
        return JSONResponse(status_code=409, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ValidationDomainError)
    async def validation_handler(request: Request, exc: ValidationDomainError):
        return JSONResponse(status_code=422, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(UnauthorizedDomainError)
    async def unauthorized_handler(request: Request, exc: UnauthorizedDomainError):
        return JSONResponse(status_code=401, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(ForbiddenDomainError)
    async def forbidden_handler(request: Request, exc: ForbiddenDomainError):
        return JSONResponse(status_code=403, content={"code": exc.code, "message": exc.message})

    @app.exception_handler(InvalidTransitionDomainError)
    async def invalid_transition_handler(request: Request, exc: InvalidTransitionDomainError):
        return JSONResponse(
            status_code=400,
            content={
                "code": exc.code,
                "message": exc.message,
                "currentStatus": exc.current_status,
                "attemptedStatus": exc.attempted_status,
                "allowedTransitions": exc.allowed_transitions,
            },
        )


# ============================================
# FILE: app/shared/presentation/auth_dependencies.py
# ============================================
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.application.services import GetCurrentAuthContextService
from app.modules.auth.presentation.dependencies import get_auth_service
from app.modules.auth.presentation.schemas import CurrentUserResponse

bearer_scheme = HTTPBearer(auto_error=False)


async def require_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    service: GetCurrentAuthContextService = Depends(get_auth_service),
) -> CurrentUserResponse:
    if credentials is None:
        from app.shared.domain.exceptions import UnauthorizedDomainError
        raise UnauthorizedDomainError("Authentication required")
    return await service.execute(credentials.credentials)


# ============================================
# FILE: app/modules/users/domain/enums.py
# ============================================
from enum import StrEnum


class UserStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


# ============================================
# FILE: app/modules/users/domain/entities.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.users.domain.enums import UserStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True)
class User(AuditFields):
    status: UserStatus
    email: str
    password_hash: str
    first_name: str
    last_name: str
    display_name: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    last_login_at: datetime | None

    def validate(self) -> None:
        if not self.email or "@" not in self.email:
            raise ValidationDomainError("User email must be valid")
        if not self.first_name:
            raise ValidationDomainError("User first_name is required")
        if not self.last_name:
            raise ValidationDomainError("User last_name is required")

    def transition_status(self, to_status: UserStatus) -> None:
        allowed = {
            UserStatus.INVITED: {UserStatus.ACTIVE, UserStatus.DEACTIVATED},
            UserStatus.ACTIVE: {UserStatus.SUSPENDED, UserStatus.DEACTIVATED},
            UserStatus.SUSPENDED: {UserStatus.ACTIVE, UserStatus.DEACTIVATED},
            UserStatus.DEACTIVATED: set(),
        }
        ensure_transition(self.status.value, to_status.value, {s.value for s in allowed[self.status]})
        self.status = to_status


# ============================================
# FILE: app/modules/users/domain/repositories.py
# ============================================
from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.users.domain.entities import User


class UserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, status: str | None, company_id: UUID | None, q: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> None:
        raise NotImplementedError


# ============================================
# FILE: app/modules/users/application/dto.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class UserDTO:
    id: UUID
    status: str
    email: str
    first_name: str
    last_name: str
    display_name: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    last_login_at: datetime | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None


# ============================================
# FILE: app/modules/users/application/mappers.py
# ============================================
from app.modules.users.application.dto import UserDTO
from app.modules.users.domain.entities import User


def to_user_dto(user: User) -> UserDTO:
    return UserDTO(
        id=user.id,
        status=user.status.value,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        phone=user.phone,
        locale=user.locale,
        timezone=user.timezone,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        created_by_user_id=user.created_by_user_id,
        updated_at=user.updated_at,
        updated_by_user_id=user.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/users/application/services.py
# ============================================
from uuid import UUID

from app.modules.users.application.dto import UserDTO
from app.modules.users.application.mappers import to_user_dto
from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.modules.users.domain.repositories import UserRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import ConflictDomainError, NotFoundDomainError


class CreateUserService:
    def __init__(self, repo: UserRepository, uuid_generator: UuidGenerator, clock: Clock):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(
        self,
        *,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        display_name: str | None,
        phone: str | None,
        locale: str | None,
        timezone: str | None,
        actor_user_id: UUID | None,
    ) -> UserDTO:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ConflictDomainError("User with this email already exists")
        now = self.clock.now()
        user = User(
            id=self.uuid_generator.new(),
            status=UserStatus.ACTIVE,
            email=email.lower().strip(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            display_name=display_name,
            phone=phone,
            locale=locale,
            timezone=timezone,
            last_login_at=None,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        user.validate()
        await self.repo.add(user)
        return to_user_dto(user)


class GetUserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def execute(self, user_id: UUID) -> UserDTO:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundDomainError("User not found")
        return to_user_dto(user)


class ListUsersService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def execute(self, *, status: str | None, company_id: UUID | None, q: str | None, page: int, page_size: int) -> tuple[list[UserDTO], int]:
        users, total = await self.repo.list(status=status, company_id=company_id, q=q, page=page, page_size=page_size)
        return [to_user_dto(user) for user in users], total


class UpdateUserService:
    def __init__(self, repo: UserRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self,
        *,
        user_id: UUID,
        first_name: str | None,
        last_name: str | None,
        display_name: str | None,
        phone: str | None,
        locale: str | None,
        timezone: str | None,
        actor_user_id: UUID | None,
    ) -> UserDTO:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundDomainError("User not found")
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if display_name is not None:
            user.display_name = display_name
        if phone is not None:
            user.phone = phone
        if locale is not None:
            user.locale = locale
        if timezone is not None:
            user.timezone = timezone
        user.updated_at = self.clock.now()
        user.updated_by_user_id = actor_user_id
        user.validate()
        await self.repo.update(user)
        return to_user_dto(user)


class TransitionUserStatusService:
    def __init__(self, repo: UserRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(self, *, user_id: UUID, to_status: str, actor_user_id: UUID | None) -> UserDTO:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundDomainError("User not found")
        user.transition_status(UserStatus(to_status))
        user.updated_at = self.clock.now()
        user.updated_by_user_id = actor_user_id
        await self.repo.update(user)
        return to_user_dto(user)


# ============================================
# FILE: app/modules/users/infrastructure/models.py
# ============================================
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locale: Mapped[str | None] = mapped_column(String(32), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ============================================
# FILE: app/modules/users/infrastructure/mappers.py
# ============================================
from uuid import UUID

from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserStatus
from app.modules.users.infrastructure.models import UserModel


def to_domain(model: UserModel) -> User:
    return User(
        id=UUID(model.id),
        status=UserStatus(model.status),
        email=model.email,
        password_hash=model.password_hash,
        first_name=model.first_name,
        last_name=model.last_name,
        display_name=model.display_name,
        phone=model.phone,
        locale=model.locale,
        timezone=model.timezone,
        last_login_at=model.last_login_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: User) -> UserModel:
    return UserModel(
        id=str(entity.id),
        status=entity.status.value,
        email=entity.email,
        password_hash=entity.password_hash,
        first_name=entity.first_name,
        last_name=entity.last_name,
        display_name=entity.display_name,
        phone=entity.phone,
        locale=entity.locale,
        timezone=entity.timezone,
        last_login_at=entity.last_login_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )


# ============================================
# FILE: app/modules/users/infrastructure/repositories.py
# ============================================
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.entities import User
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.infrastructure.mappers import to_domain, to_model
from app.modules.users.infrastructure.models import UserModel
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user: User) -> None:
        self.session.add(to_model(user))
        await self.session.commit()

    async def get_by_id(self, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(UserModel.id == str(user_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower().strip())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list(self, *, status: str | None, company_id: UUID | None, q: str | None, page: int, page_size: int) -> tuple[list[User], int]:
        stmt = select(UserModel)
        count_stmt = select(func.count()).select_from(UserModel)

        if company_id:
            membership_subquery = select(CompanyMembershipModel.user_id).where(CompanyMembershipModel.company_id == str(company_id))
            stmt = stmt.where(UserModel.id.in_(membership_subquery))
            count_stmt = count_stmt.where(UserModel.id.in_(membership_subquery))

        if status:
            stmt = stmt.where(UserModel.status == status)
            count_stmt = count_stmt.where(UserModel.status == status)

        if q:
            pattern = f"%{q}%"
            filter_expr = or_(
                UserModel.email.ilike(pattern),
                UserModel.first_name.ilike(pattern),
                UserModel.last_name.ilike(pattern),
            )
            stmt = stmt.where(filter_expr)
            count_stmt = count_stmt.where(filter_expr)

        stmt = stmt.order_by(UserModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()

        return [to_domain(row) for row in rows], int(total)

    async def update(self, user: User) -> None:
        model = await self.session.get(UserModel, str(user.id))
        if model is None:
            return
        model.status = user.status.value
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.display_name = user.display_name
        model.phone = user.phone
        model.locale = user.locale
        model.timezone = user.timezone
        model.last_login_at = user.last_login_at
        model.updated_at = user.updated_at
        model.updated_by_user_id = str(user.updated_by_user_id) if user.updated_by_user_id else None
        await self.session.commit()


# ============================================
# FILE: app/modules/users/presentation/schemas.py
# ============================================
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    firstName: str
    lastName: str
    displayName: str | None = None
    phone: str | None = None
    locale: str | None = None
    timezone: str | None = None


class UserUpdateRequest(BaseModel):
    firstName: str | None = None
    lastName: str | None = None
    displayName: str | None = None
    phone: str | None = None
    locale: str | None = None
    timezone: str | None = None


class UserStatusTransitionRequest(BaseModel):
    toStatus: str


class UserData(BaseModel):
    id: UUID
    status: str
    email: EmailStr
    firstName: str
    lastName: str
    displayName: str | None
    phone: str | None
    locale: str | None
    timezone: str | None
    lastLoginAt: datetime | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class UserResponse(BaseModel):
    data: UserData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedUsersResponse(BaseModel):
    items: list[UserData]
    meta: PaginationMeta


# ============================================
# FILE: app/modules/users/presentation/mappers.py
# ============================================
from app.modules.users.application.dto import UserDTO
from app.modules.users.presentation.schemas import UserData


def to_user_data(dto: UserDTO) -> UserData:
    return UserData(
        id=dto.id,
        status=dto.status,
        email=dto.email,
        firstName=dto.first_name,
        lastName=dto.last_name,
        displayName=dto.display_name,
        phone=dto.phone,
        locale=dto.locale,
        timezone=dto.timezone,
        lastLoginAt=dto.last_login_at,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/users/presentation/dependencies.py
# ============================================
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.application.services import (
    CreateUserService,
    GetUserService,
    ListUsersService,
    TransitionUserStatusService,
    UpdateUserService,
)
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_create_user_service(repo: SqlAlchemyUserRepository = Depends(get_user_repo)) -> CreateUserService:
    return CreateUserService(repo=repo, uuid_generator=UuidGenerator(), clock=Clock())


def get_get_user_service(repo: SqlAlchemyUserRepository = Depends(get_user_repo)) -> GetUserService:
    return GetUserService(repo=repo)


def get_list_users_service(repo: SqlAlchemyUserRepository = Depends(get_user_repo)) -> ListUsersService:
    return ListUsersService(repo=repo)


def get_update_user_service(repo: SqlAlchemyUserRepository = Depends(get_user_repo)) -> UpdateUserService:
    return UpdateUserService(repo=repo, clock=Clock())


def get_transition_user_status_service(repo: SqlAlchemyUserRepository = Depends(get_user_repo)) -> TransitionUserStatusService:
    return TransitionUserStatusService(repo=repo, clock=Clock())


def get_password_service() -> PasswordService:
    return PasswordService()


# ============================================
# FILE: app/modules/users/presentation/router.py
# ============================================
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.users.presentation.dependencies import (
    get_create_user_service,
    get_get_user_service,
    get_list_users_service,
    get_password_service,
    get_transition_user_status_service,
    get_update_user_service,
)
from app.modules.users.presentation.mappers import to_user_data
from app.modules.users.presentation.schemas import (
    PaginatedUsersResponse,
    PaginationMeta,
    UserCreateRequest,
    UserResponse,
    UserStatusTransitionRequest,
    UserUpdateRequest,
)
from app.shared.application.passwords import PasswordService
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedUsersResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    companyId: UUID | None = None,
    q: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_users_service),
):
    items, total = await service.execute(status=status, company_id=companyId, q=q, page=page, page_size=pageSize)
    return PaginatedUsersResponse(
        items=[to_user_data(item) for item in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_user_service),
    password_service: PasswordService = Depends(get_password_service),
):
    dto = await service.execute(
        email=payload.email,
        password_hash=password_service.hash_password(payload.password),
        first_name=payload.firstName,
        last_name=payload.lastName,
        display_name=payload.displayName,
        phone=payload.phone,
        locale=payload.locale,
        timezone=payload.timezone,
        actor_user_id=current_user.user.id,
    )
    return UserResponse(data=to_user_data(dto))


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_user_service),
):
    dto = await service.execute(user_id)
    return UserResponse(data=to_user_data(dto))


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_user_service),
):
    dto = await service.execute(
        user_id=user_id,
        first_name=payload.firstName,
        last_name=payload.lastName,
        display_name=payload.displayName,
        phone=payload.phone,
        locale=payload.locale,
        timezone=payload.timezone,
        actor_user_id=current_user.user.id,
    )
    return UserResponse(data=to_user_data(dto))


@router.patch("/{user_id}/status", response_model=UserResponse)
async def transition_user_status(
    user_id: UUID,
    payload: UserStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_user_status_service),
):
    dto = await service.execute(user_id=user_id, to_status=payload.toStatus, actor_user_id=current_user.user.id)
    return UserResponse(data=to_user_data(dto))


# ============================================
# FILE: app/modules/auth/domain/entities.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.shared.domain.base import AuditFields


@dataclass(slots=True)
class RefreshSession(AuditFields):
    user_id: UUID
    token_family_id: str
    refresh_token_jti: str
    refresh_token_hash: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_jti: str | None
    reuse_detected_at: datetime | None


# ============================================
# FILE: app/modules/auth/domain/repositories.py
# ============================================
from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.auth.domain.entities import RefreshSession


class RefreshSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        raise NotImplementedError

    @abstractmethod
    async def get_active_by_user_id(self, user_id: UUID) -> list[RefreshSession]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, session: RefreshSession) -> None:
        raise NotImplementedError

    @abstractmethod
    async def revoke_family(self, family_id: str, revoked_at) -> None:
        raise NotImplementedError


# ============================================
# FILE: app/modules/auth/application/dto.py
# ============================================
from dataclasses import dataclass

from app.modules.users.application.dto import UserDTO


@dataclass(slots=True)
class AuthTokenPairDTO:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


@dataclass(slots=True)
class CurrentAuthContextDTO:
    user: UserDTO
    role_codes: list[str]
    memberships: list[dict]


# ============================================
# FILE: app/modules/auth/application/services.py
# ============================================
import hashlib
from datetime import datetime, timezone
from uuid import UUID

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
        user = await self.user_repo.get_by_email(email.lower().strip())
        if not user:
            raise UnauthorizedDomainError("Invalid credentials")
        if not self.password_service.verify_password(password, user.password_hash):
            raise UnauthorizedDomainError("Invalid credentials")
        if user.status != user.status.ACTIVE:
            raise UnauthorizedDomainError("User is not active")

        family_id = str(self.uuid_generator.new())
        access_token, access_expires_at = self.jwt_service.issue_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email},
        )
        refresh_token, refresh_jti, refresh_expires_at = self.jwt_service.issue_refresh_token(
            subject=str(user.id),
            family_id=family_id,
        )
        now = self.clock.now()
        refresh_entity = RefreshSession(
            id=self.uuid_generator.new(),
            user_id=user.id,
            token_family_id=family_id,
            refresh_token_jti=refresh_jti,
            refresh_token_hash=self._hash_token(refresh_token),
            expires_at=refresh_expires_at,
            revoked_at=None,
            replaced_by_jti=None,
            reuse_detected_at=None,
            created_at=now,
            created_by_user_id=user.id,
            updated_at=now,
            updated_by_user_id=user.id,
        )
        user.last_login_at = now
        user.updated_at = now
        user.updated_by_user_id = user.id
        await self.refresh_repo.add(refresh_entity)
        await self.user_repo.update(user)
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
            id=UUID(payload["jti"]) if False else self._new_uuid(),
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

    def _new_uuid(self):
        from uuid import uuid4
        return uuid4()


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


# ============================================
# FILE: app/modules/auth/infrastructure/models.py
# ============================================
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class RefreshSessionModel(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_family_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    refresh_token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_jti: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reuse_detected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ============================================
# FILE: app/modules/auth/infrastructure/mappers.py
# ============================================
from uuid import UUID

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.infrastructure.models import RefreshSessionModel


def to_domain(model: RefreshSessionModel) -> RefreshSession:
    return RefreshSession(
        id=UUID(model.id),
        user_id=UUID(model.user_id),
        token_family_id=model.token_family_id,
        refresh_token_jti=model.refresh_token_jti,
        refresh_token_hash=model.refresh_token_hash,
        expires_at=model.expires_at,
        revoked_at=model.revoked_at,
        replaced_by_jti=model.replaced_by_jti,
        reuse_detected_at=model.reuse_detected_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: RefreshSession) -> RefreshSessionModel:
    return RefreshSessionModel(
        id=str(entity.id),
        user_id=str(entity.user_id),
        token_family_id=entity.token_family_id,
        refresh_token_jti=entity.refresh_token_jti,
        refresh_token_hash=entity.refresh_token_hash,
        expires_at=entity.expires_at,
        revoked_at=entity.revoked_at,
        replaced_by_jti=entity.replaced_by_jti,
        reuse_detected_at=entity.reuse_detected_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )


# ============================================
# FILE: app/modules/auth/infrastructure/repositories.py
# ============================================
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import RefreshSession
from app.modules.auth.domain.repositories import RefreshSessionRepository
from app.modules.auth.infrastructure.mappers import to_domain, to_model
from app.modules.auth.infrastructure.models import RefreshSessionModel


class SqlAlchemyRefreshSessionRepository(RefreshSessionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, session_entity: RefreshSession) -> None:
        self.session.add(to_model(session_entity))
        await self.session.commit()

    async def get_by_jti(self, jti: str) -> RefreshSession | None:
        stmt = select(RefreshSessionModel).where(RefreshSessionModel.refresh_token_jti == jti)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def get_active_by_user_id(self, user_id: UUID) -> list[RefreshSession]:
        stmt = select(RefreshSessionModel).where(
            RefreshSessionModel.user_id == str(user_id),
            RefreshSessionModel.revoked_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def update(self, session_entity: RefreshSession) -> None:
        model = await self.session.get(RefreshSessionModel, str(session_entity.id))
        if model is None:
            return
        model.revoked_at = session_entity.revoked_at
        model.replaced_by_jti = session_entity.replaced_by_jti
        model.reuse_detected_at = session_entity.reuse_detected_at
        model.updated_at = session_entity.updated_at
        model.updated_by_user_id = str(session_entity.updated_by_user_id) if session_entity.updated_by_user_id else None
        await self.session.commit()

    async def revoke_family(self, family_id: str, revoked_at) -> None:
        stmt = (
            update(RefreshSessionModel)
            .where(RefreshSessionModel.token_family_id == family_id, RefreshSessionModel.revoked_at.is_(None))
            .values(revoked_at=revoked_at, updated_at=revoked_at)
        )
        await self.session.execute(stmt)
        await self.session.commit()


# ============================================
# FILE: app/modules/auth/presentation/schemas.py
# ============================================
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.modules.users.presentation.schemas import UserData


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refreshToken: str


class LogoutRequest(BaseModel):
    refreshToken: str | None = None


class AuthTokenPairResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str
    expiresIn: int


class MembershipContext(BaseModel):
    id: UUID
    companyId: UUID
    membershipRole: str
    status: str
    isPrimaryContact: bool


class CurrentUserResponse(BaseModel):
    user: UserData
    roleCodes: list[str]
    memberships: list[MembershipContext]


# ============================================
# FILE: app/modules/auth/presentation/dependencies.py
# ============================================
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.application.services import (
    GetCurrentAuthContextService,
    LoginService,
    LogoutService,
    RefreshTokenService,
)
from app.modules.auth.infrastructure.repositories import SqlAlchemyRefreshSessionRepository
from app.modules.company_memberships.infrastructure.repositories import SqlAlchemyCompanyMembershipRepository
from app.modules.users.infrastructure.repositories import SqlAlchemyUserRepository
from app.shared.application.clock import Clock
from app.shared.application.passwords import PasswordService
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session
from app.shared.infrastructure.security.jwt_service import JwtService


def get_refresh_session_repo(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyRefreshSessionRepository:
    return SqlAlchemyRefreshSessionRepository(session)


def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
) -> GetCurrentAuthContextService:
    user_repo = SqlAlchemyUserRepository(session)
    membership_repo = SqlAlchemyCompanyMembershipRepository(session)
    return GetCurrentAuthContextService(
        user_repo=user_repo,
        membership_repo=membership_repo,
        jwt_service=JwtService(),
    )


def get_login_service(session: AsyncSession = Depends(get_db_session)) -> LoginService:
    return LoginService(
        user_repo=SqlAlchemyUserRepository(session),
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        membership_repo=SqlAlchemyCompanyMembershipRepository(session),
        password_service=PasswordService(),
        jwt_service=JwtService(),
        uuid_generator=UuidGenerator(),
        clock=Clock(),
    )


def get_refresh_token_service(session: AsyncSession = Depends(get_db_session)) -> RefreshTokenService:
    return RefreshTokenService(
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        jwt_service=JwtService(),
        clock=Clock(),
    )


def get_logout_service(session: AsyncSession = Depends(get_db_session)) -> LogoutService:
    return LogoutService(
        refresh_repo=SqlAlchemyRefreshSessionRepository(session),
        jwt_service=JwtService(),
        clock=Clock(),
    )


# ============================================
# FILE: app/modules/auth/presentation/router.py
# ============================================
from fastapi import APIRouter, Depends

from app.modules.auth.presentation.dependencies import (
    get_auth_service,
    get_login_service,
    get_logout_service,
    get_refresh_token_service,
)
from app.modules.auth.presentation.schemas import (
    AuthTokenPairResponse,
    CurrentUserResponse,
    LoginRequest,
    LogoutRequest,
    MembershipContext,
    RefreshTokenRequest,
)
from app.modules.users.presentation.mappers import to_user_data
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=AuthTokenPairResponse)
async def login(payload: LoginRequest, service=Depends(get_login_service)):
    dto = await service.execute(email=payload.email, password=payload.password)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post("/refresh", response_model=AuthTokenPairResponse)
async def refresh_token(payload: RefreshTokenRequest, service=Depends(get_refresh_token_service)):
    dto = await service.execute(refresh_token=payload.refreshToken)
    return AuthTokenPairResponse(
        accessToken=dto.access_token,
        refreshToken=dto.refresh_token,
        tokenType=dto.token_type,
        expiresIn=dto.expires_in,
    )


@router.post("/logout", status_code=204)
async def logout(payload: LogoutRequest, service=Depends(get_logout_service)):
    await service.execute(refresh_token=payload.refreshToken)
    return None


@router.get("/me", response_model=CurrentUserResponse)
async def me(current_user=Depends(require_current_user), service=Depends(get_auth_service)):
    context = await service.execute.__self__.execute if False else current_user
    return CurrentUserResponse(
        user=to_user_data(context.user),
        roleCodes=context.role_codes,
        memberships=[
            MembershipContext(
                id=item["id"],
                companyId=item["companyId"],
                membershipRole=item["membershipRole"],
                status=item["status"],
                isPrimaryContact=item["isPrimaryContact"],
            )
            for item in context.memberships
        ],
    )


# ============================================
# FILE: app/modules/companies/domain/enums.py
# ============================================
from enum import StrEnum


class CompanyStatus(StrEnum):
    DRAFT = "draft"
    VERIFICATION_SUBMITTED = "verification_submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"


class CompanyType(StrEnum):
    SELLER = "seller"
    BUYER = "buyer"
    SELLER_BUYER = "seller_buyer"
    LOGISTICS_PARTNER = "logistics_partner"


# ============================================
# FILE: app/modules/companies/domain/entities.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True)
class Company(AuditFields):
    status: CompanyStatus
    legal_name: str
    trading_name: str | None
    registration_number: str
    tax_identifier: str | None
    company_type: CompanyType
    email: str | None
    phone: str | None
    website_url: str | None
    country_code: str
    address_line_1: str
    address_line_2: str | None
    city: str
    postal_code: str
    latitude: float | None
    longitude: float | None
    seller_capability: bool
    buyer_capability: bool
    logistics_capability: bool
    verification_submitted_at: datetime | None
    verification_reviewed_at: datetime | None
    verification_reviewed_by_user_id: UUID | None
    verified_at: datetime | None
    verified_by_user_id: UUID | None
    rejected_at: datetime | None
    rejected_by_user_id: UUID | None

    def validate(self) -> None:
        if not self.legal_name:
            raise ValidationDomainError("Company legal_name is required")
        if not self.registration_number:
            raise ValidationDomainError("Company registration_number is required")
        if len(self.country_code) != 2:
            raise ValidationDomainError("Company country_code must have ISO length 2")
        if not any([self.seller_capability, self.buyer_capability, self.logistics_capability]):
            raise ValidationDomainError("At least one company capability must be enabled")

    def transition_status(self, to_status: CompanyStatus) -> None:
        allowed = {
            CompanyStatus.DRAFT: {CompanyStatus.VERIFICATION_SUBMITTED, CompanyStatus.INACTIVE},
            CompanyStatus.VERIFICATION_SUBMITTED: {CompanyStatus.VERIFIED, CompanyStatus.REJECTED, CompanyStatus.DRAFT},
            CompanyStatus.VERIFIED: {CompanyStatus.SUSPENDED, CompanyStatus.INACTIVE},
            CompanyStatus.REJECTED: {CompanyStatus.DRAFT, CompanyStatus.VERIFICATION_SUBMITTED, CompanyStatus.INACTIVE},
            CompanyStatus.SUSPENDED: {CompanyStatus.VERIFIED, CompanyStatus.INACTIVE},
            CompanyStatus.INACTIVE: set(),
        }
        ensure_transition(self.status.value, to_status.value, {s.value for s in allowed[self.status]})
        self.status = to_status


# ============================================
# FILE: app/modules/companies/domain/repositories.py
# ============================================
from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.companies.domain.entities import Company


class CompanyRepository(ABC):
    @abstractmethod
    async def add(self, company: Company) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, company_id: UUID) -> Company | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        *,
        status: str | None,
        company_type: str | None,
        seller_capability: bool | None,
        buyer_capability: bool | None,
        logistics_capability: bool | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Company], int]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, company: Company) -> None:
        raise NotImplementedError


# ============================================
# FILE: app/modules/companies/application/dto.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class CompanyDTO:
    id: UUID
    status: str
    legal_name: str
    trading_name: str | None
    registration_number: str
    tax_identifier: str | None
    company_type: str
    email: str | None
    phone: str | None
    website_url: str | None
    country_code: str
    address_line_1: str
    address_line_2: str | None
    city: str
    postal_code: str
    latitude: float | None
    longitude: float | None
    seller_capability: bool
    buyer_capability: bool
    logistics_capability: bool
    verification_submitted_at: datetime | None
    verification_reviewed_at: datetime | None
    verification_reviewed_by_user_id: UUID | None
    verified_at: datetime | None
    verified_by_user_id: UUID | None
    rejected_at: datetime | None
    rejected_by_user_id: UUID | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None


# ============================================
# FILE: app/modules/companies/application/mappers.py
# ============================================
from app.modules.companies.application.dto import CompanyDTO
from app.modules.companies.domain.entities import Company


def to_company_dto(company: Company) -> CompanyDTO:
    return CompanyDTO(
        id=company.id,
        status=company.status.value,
        legal_name=company.legal_name,
        trading_name=company.trading_name,
        registration_number=company.registration_number,
        tax_identifier=company.tax_identifier,
        company_type=company.company_type.value,
        email=company.email,
        phone=company.phone,
        website_url=company.website_url,
        country_code=company.country_code,
        address_line_1=company.address_line_1,
        address_line_2=company.address_line_2,
        city=company.city,
        postal_code=company.postal_code,
        latitude=company.latitude,
        longitude=company.longitude,
        seller_capability=company.seller_capability,
        buyer_capability=company.buyer_capability,
        logistics_capability=company.logistics_capability,
        verification_submitted_at=company.verification_submitted_at,
        verification_reviewed_at=company.verification_reviewed_at,
        verification_reviewed_by_user_id=company.verification_reviewed_by_user_id,
        verified_at=company.verified_at,
        verified_by_user_id=company.verified_by_user_id,
        rejected_at=company.rejected_at,
        rejected_by_user_id=company.rejected_by_user_id,
        created_at=company.created_at,
        created_by_user_id=company.created_by_user_id,
        updated_at=company.updated_at,
        updated_by_user_id=company.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/companies/application/services.py
# ============================================
from uuid import UUID

from app.modules.companies.application.dto import CompanyDTO
from app.modules.companies.application.mappers import to_company_dto
from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.modules.companies.domain.repositories import CompanyRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


class CreateCompanyService:
    def __init__(self, repo: CompanyRepository, uuid_generator: UuidGenerator, clock: Clock):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(
        self,
        *,
        legal_name: str,
        trading_name: str | None,
        registration_number: str,
        tax_identifier: str | None,
        company_type: str,
        email: str | None,
        phone: str | None,
        website_url: str | None,
        country_code: str,
        address_line_1: str,
        address_line_2: str | None,
        city: str,
        postal_code: str,
        latitude: float | None,
        longitude: float | None,
        seller_capability: bool,
        buyer_capability: bool,
        logistics_capability: bool,
        actor_user_id: UUID | None,
    ) -> CompanyDTO:
        now = self.clock.now()
        company = Company(
            id=self.uuid_generator.new(),
            status=CompanyStatus.DRAFT,
            legal_name=legal_name,
            trading_name=trading_name,
            registration_number=registration_number,
            tax_identifier=tax_identifier,
            company_type=CompanyType(company_type),
            email=email,
            phone=phone,
            website_url=website_url,
            country_code=country_code.upper(),
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            postal_code=postal_code,
            latitude=latitude,
            longitude=longitude,
            seller_capability=seller_capability,
            buyer_capability=buyer_capability,
            logistics_capability=logistics_capability,
            verification_submitted_at=None,
            verification_reviewed_at=None,
            verification_reviewed_by_user_id=None,
            verified_at=None,
            verified_by_user_id=None,
            rejected_at=None,
            rejected_by_user_id=None,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        company.validate()
        await self.repo.add(company)
        return to_company_dto(company)


class GetCompanyService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    async def execute(self, company_id: UUID) -> CompanyDTO:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundDomainError("Company not found")
        return to_company_dto(company)


class ListCompaniesService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    async def execute(
        self,
        *,
        status: str | None,
        company_type: str | None,
        seller_capability: bool | None,
        buyer_capability: bool | None,
        logistics_capability: bool | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[CompanyDTO], int]:
        companies, total = await self.repo.list(
            status=status,
            company_type=company_type,
            seller_capability=seller_capability,
            buyer_capability=buyer_capability,
            logistics_capability=logistics_capability,
            q=q,
            page=page,
            page_size=page_size,
        )
        return [to_company_dto(company) for company in companies], total


class UpdateCompanyService:
    def __init__(self, repo: CompanyRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self,
        *,
        company_id: UUID,
        legal_name: str | None,
        trading_name: str | None,
        tax_identifier: str | None,
        email: str | None,
        phone: str | None,
        website_url: str | None,
        address_line_1: str | None,
        address_line_2: str | None,
        city: str | None,
        postal_code: str | None,
        latitude: float | None,
        longitude: float | None,
        actor_user_id: UUID | None,
    ) -> CompanyDTO:
        company = await self.repo.get_by_id(company_id)
        if not company:
            raise NotFoundDomainError("Company not found")
        if legal_name is not None:
            company.legal_name = legal_name
        if trading_name is not None:
            company.trading_name = trading_name
        if tax_identifier is not None:
            company.tax_identifier = tax_identifier
        if email is not None:
            company.email = email
        if phone is not None:
            company.phone = phone
        if website_url is not None:
            company.website_url = website_url
        if address_line_1 is not None:
            company.address_line_1 = address_line_1
        if address_line_2 is not None:
            company.address_line_2 = address_line_2
        if city is not None:
            company.city = city
        if postal_code is not None:
            company.postal_code = postal_code
        if latitude is not None:
            company.latitude = latitude
        if longitude is not None:
            company.longitude = longitude
        company.updated_at = self.clock.now()
        company.updated_by_user_id = actor_user_id
        company.validate()
        await self.repo.update(company)
        return to_company_dto(company)


# ============================================
# FILE: app/modules/companies/infrastructure/models.py
# ============================================
from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyModel(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trading_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    registration_number: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    tax_identifier: Mapped[str | None] = mapped_column(String(128), nullable=True)
    company_type: Mapped[str] = mapped_column(String(32), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(64), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    seller_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    buyer_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    logistics_capability: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verification_submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_reviewed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_reviewed_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    verified_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    rejected_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ============================================
# FILE: app/modules/companies/infrastructure/mappers.py
# ============================================
from uuid import UUID

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.enums import CompanyStatus, CompanyType
from app.modules.companies.infrastructure.models import CompanyModel


def to_domain(model: CompanyModel) -> Company:
    return Company(
        id=UUID(model.id),
        status=CompanyStatus(model.status),
        legal_name=model.legal_name,
        trading_name=model.trading_name,
        registration_number=model.registration_number,
        tax_identifier=model.tax_identifier,
        company_type=CompanyType(model.company_type),
        email=model.email,
        phone=model.phone,
        website_url=model.website_url,
        country_code=model.country_code,
        address_line_1=model.address_line_1,
        address_line_2=model.address_line_2,
        city=model.city,
        postal_code=model.postal_code,
        latitude=model.latitude,
        longitude=model.longitude,
        seller_capability=model.seller_capability,
        buyer_capability=model.buyer_capability,
        logistics_capability=model.logistics_capability,
        verification_submitted_at=model.verification_submitted_at,
        verification_reviewed_at=model.verification_reviewed_at,
        verification_reviewed_by_user_id=UUID(model.verification_reviewed_by_user_id) if model.verification_reviewed_by_user_id else None,
        verified_at=model.verified_at,
        verified_by_user_id=UUID(model.verified_by_user_id) if model.verified_by_user_id else None,
        rejected_at=model.rejected_at,
        rejected_by_user_id=UUID(model.rejected_by_user_id) if model.rejected_by_user_id else None,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: Company) -> CompanyModel:
    return CompanyModel(
        id=str(entity.id),
        status=entity.status.value,
        legal_name=entity.legal_name,
        trading_name=entity.trading_name,
        registration_number=entity.registration_number,
        tax_identifier=entity.tax_identifier,
        company_type=entity.company_type.value,
        email=entity.email,
        phone=entity.phone,
        website_url=entity.website_url,
        country_code=entity.country_code,
        address_line_1=entity.address_line_1,
        address_line_2=entity.address_line_2,
        city=entity.city,
        postal_code=entity.postal_code,
        latitude=entity.latitude,
        longitude=entity.longitude,
        seller_capability=entity.seller_capability,
        buyer_capability=entity.buyer_capability,
        logistics_capability=entity.logistics_capability,
        verification_submitted_at=entity.verification_submitted_at,
        verification_reviewed_at=entity.verification_reviewed_at,
        verification_reviewed_by_user_id=str(entity.verification_reviewed_by_user_id) if entity.verification_reviewed_by_user_id else None,
        verified_at=entity.verified_at,
        verified_by_user_id=str(entity.verified_by_user_id) if entity.verified_by_user_id else None,
        rejected_at=entity.rejected_at,
        rejected_by_user_id=str(entity.rejected_by_user_id) if entity.rejected_by_user_id else None,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )


# ============================================
# FILE: app/modules/companies/infrastructure/repositories.py
# ============================================
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.domain.entities import Company
from app.modules.companies.domain.repositories import CompanyRepository
from app.modules.companies.infrastructure.mappers import to_domain, to_model
from app.modules.companies.infrastructure.models import CompanyModel


class SqlAlchemyCompanyRepository(CompanyRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, company: Company) -> None:
        self.session.add(to_model(company))
        await self.session.commit()

    async def get_by_id(self, company_id):
        stmt = select(CompanyModel).where(CompanyModel.id == str(company_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list(
        self,
        *,
        status,
        company_type,
        seller_capability,
        buyer_capability,
        logistics_capability,
        q,
        page,
        page_size,
    ):
        stmt = select(CompanyModel)
        count_stmt = select(func.count()).select_from(CompanyModel)

        if status:
            stmt = stmt.where(CompanyModel.status == status)
            count_stmt = count_stmt.where(CompanyModel.status == status)
        if company_type:
            stmt = stmt.where(CompanyModel.company_type == company_type)
            count_stmt = count_stmt.where(CompanyModel.company_type == company_type)
        if seller_capability is not None:
            stmt = stmt.where(CompanyModel.seller_capability == seller_capability)
            count_stmt = count_stmt.where(CompanyModel.seller_capability == seller_capability)
        if buyer_capability is not None:
            stmt = stmt.where(CompanyModel.buyer_capability == buyer_capability)
            count_stmt = count_stmt.where(CompanyModel.buyer_capability == buyer_capability)
        if logistics_capability is not None:
            stmt = stmt.where(CompanyModel.logistics_capability == logistics_capability)
            count_stmt = count_stmt.where(CompanyModel.logistics_capability == logistics_capability)
        if q:
            pattern = f"%{q}%"
            expr = or_(
                CompanyModel.legal_name.ilike(pattern),
                CompanyModel.trading_name.ilike(pattern),
                CompanyModel.registration_number.ilike(pattern),
            )
            stmt = stmt.where(expr)
            count_stmt = count_stmt.where(expr)

        stmt = stmt.order_by(CompanyModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        rows = (await self.session.execute(stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return [to_domain(row) for row in rows], int(total)

    async def update(self, company: Company) -> None:
        model = await self.session.get(CompanyModel, str(company.id))
        if model is None:
            return
        model.status = company.status.value
        model.legal_name = company.legal_name
        model.trading_name = company.trading_name
        model.tax_identifier = company.tax_identifier
        model.email = company.email
        model.phone = company.phone
        model.website_url = company.website_url
        model.address_line_1 = company.address_line_1
        model.address_line_2 = company.address_line_2
        model.city = company.city
        model.postal_code = company.postal_code
        model.latitude = company.latitude
        model.longitude = company.longitude
        model.updated_at = company.updated_at
        model.updated_by_user_id = str(company.updated_by_user_id) if company.updated_by_user_id else None
        await self.session.commit()


# ============================================
# FILE: app/modules/companies/presentation/schemas.py
# ============================================
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class CompanyCreateRequest(BaseModel):
    legalName: str
    tradingName: str | None = None
    registrationNumber: str
    taxIdentifier: str | None = None
    companyType: str
    email: str | None = None
    phone: str | None = None
    websiteUrl: HttpUrl | None = None
    countryCode: str
    addressLine1: str
    addressLine2: str | None = None
    city: str
    postalCode: str
    latitude: float | None = None
    longitude: float | None = None
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool


class CompanyUpdateRequest(BaseModel):
    legalName: str | None = None
    tradingName: str | None = None
    taxIdentifier: str | None = None
    email: str | None = None
    phone: str | None = None
    websiteUrl: HttpUrl | None = None
    addressLine1: str | None = None
    addressLine2: str | None = None
    city: str | None = None
    postalCode: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CompanyData(BaseModel):
    id: UUID
    status: str
    legalName: str
    tradingName: str | None
    registrationNumber: str
    taxIdentifier: str | None
    companyType: str
    email: str | None
    phone: str | None
    websiteUrl: str | None
    countryCode: str
    addressLine1: str
    addressLine2: str | None
    city: str
    postalCode: str
    latitude: float | None
    longitude: float | None
    sellerCapability: bool
    buyerCapability: bool
    logisticsCapability: bool
    verificationSubmittedAt: datetime | None
    verificationReviewedAt: datetime | None
    verificationReviewedByUserId: UUID | None
    verifiedAt: datetime | None
    verifiedByUserId: UUID | None
    rejectedAt: datetime | None
    rejectedByUserId: UUID | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class CompanyResponse(BaseModel):
    data: CompanyData


class PaginationMeta(BaseModel):
    page: int
    pageSize: int
    total: int


class PaginatedCompaniesResponse(BaseModel):
    items: list[CompanyData]
    meta: PaginationMeta


# ============================================
# FILE: app/modules/companies/presentation/mappers.py
# ============================================
from app.modules.companies.application.dto import CompanyDTO
from app.modules.companies.presentation.schemas import CompanyData


def to_company_data(dto: CompanyDTO) -> CompanyData:
    return CompanyData(
        id=dto.id,
        status=dto.status,
        legalName=dto.legal_name,
        tradingName=dto.trading_name,
        registrationNumber=dto.registration_number,
        taxIdentifier=dto.tax_identifier,
        companyType=dto.company_type,
        email=dto.email,
        phone=dto.phone,
        websiteUrl=dto.website_url,
        countryCode=dto.country_code,
        addressLine1=dto.address_line_1,
        addressLine2=dto.address_line_2,
        city=dto.city,
        postalCode=dto.postal_code,
        latitude=dto.latitude,
        longitude=dto.longitude,
        sellerCapability=dto.seller_capability,
        buyerCapability=dto.buyer_capability,
        logisticsCapability=dto.logistics_capability,
        verificationSubmittedAt=dto.verification_submitted_at,
        verificationReviewedAt=dto.verification_reviewed_at,
        verificationReviewedByUserId=dto.verification_reviewed_by_user_id,
        verifiedAt=dto.verified_at,
        verifiedByUserId=dto.verified_by_user_id,
        rejectedAt=dto.rejected_at,
        rejectedByUserId=dto.rejected_by_user_id,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/companies/presentation/dependencies.py
# ============================================
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.companies.application.services import (
    CreateCompanyService,
    GetCompanyService,
    ListCompaniesService,
    UpdateCompanyService,
)
from app.modules.companies.infrastructure.repositories import SqlAlchemyCompanyRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_company_repo(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyCompanyRepository:
    return SqlAlchemyCompanyRepository(session)


def get_create_company_service(repo: SqlAlchemyCompanyRepository = Depends(get_company_repo)) -> CreateCompanyService:
    return CreateCompanyService(repo=repo, uuid_generator=UuidGenerator(), clock=Clock())


def get_get_company_service(repo: SqlAlchemyCompanyRepository = Depends(get_company_repo)) -> GetCompanyService:
    return GetCompanyService(repo=repo)


def get_list_companies_service(repo: SqlAlchemyCompanyRepository = Depends(get_company_repo)) -> ListCompaniesService:
    return ListCompaniesService(repo=repo)


def get_update_company_service(repo: SqlAlchemyCompanyRepository = Depends(get_company_repo)) -> UpdateCompanyService:
    return UpdateCompanyService(repo=repo, clock=Clock())


# ============================================
# FILE: app/modules/companies/presentation/router.py
# ============================================
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.modules.companies.presentation.dependencies import (
    get_create_company_service,
    get_get_company_service,
    get_list_companies_service,
    get_update_company_service,
)
from app.modules.companies.presentation.mappers import to_company_data
from app.modules.companies.presentation.schemas import (
    CompanyCreateRequest,
    CompanyResponse,
    CompanyUpdateRequest,
    PaginatedCompaniesResponse,
    PaginationMeta,
)
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=PaginatedCompaniesResponse)
async def list_companies(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=25, ge=1, le=100),
    status: str | None = None,
    companyType: str | None = None,
    sellerCapability: bool | None = None,
    buyerCapability: bool | None = None,
    logisticsCapability: bool | None = None,
    q: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_companies_service),
):
    items, total = await service.execute(
        status=status,
        company_type=companyType,
        seller_capability=sellerCapability,
        buyer_capability=buyerCapability,
        logistics_capability=logisticsCapability,
        q=q,
        page=page,
        page_size=pageSize,
    )
    return PaginatedCompaniesResponse(
        items=[to_company_data(item) for item in items],
        meta=PaginationMeta(page=page, pageSize=pageSize, total=total),
    )


@router.post("", response_model=CompanyResponse, status_code=201)
async def create_company(
    payload: CompanyCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_company_service),
):
    dto = await service.execute(
        legal_name=payload.legalName,
        trading_name=payload.tradingName,
        registration_number=payload.registrationNumber,
        tax_identifier=payload.taxIdentifier,
        company_type=payload.companyType,
        email=payload.email,
        phone=payload.phone,
        website_url=str(payload.websiteUrl) if payload.websiteUrl else None,
        country_code=payload.countryCode,
        address_line_1=payload.addressLine1,
        address_line_2=payload.addressLine2,
        city=payload.city,
        postal_code=payload.postalCode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        seller_capability=payload.sellerCapability,
        buyer_capability=payload.buyerCapability,
        logistics_capability=payload.logisticsCapability,
        actor_user_id=current_user.user.id,
    )
    return CompanyResponse(data=to_company_data(dto))


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    current_user=Depends(require_current_user),
    service=Depends(get_get_company_service),
):
    dto = await service.execute(company_id)
    return CompanyResponse(data=to_company_data(dto))


@router.patch("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    payload: CompanyUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_company_service),
):
    dto = await service.execute(
        company_id=company_id,
        legal_name=payload.legalName,
        trading_name=payload.tradingName,
        tax_identifier=payload.taxIdentifier,
        email=payload.email,
        phone=payload.phone,
        website_url=str(payload.websiteUrl) if payload.websiteUrl else None,
        address_line_1=payload.addressLine1,
        address_line_2=payload.addressLine2,
        city=payload.city,
        postal_code=payload.postalCode,
        latitude=payload.latitude,
        longitude=payload.longitude,
        actor_user_id=current_user.user.id,
    )
    return CompanyResponse(data=to_company_data(dto))


# ============================================
# FILE: app/modules/company_memberships/domain/enums.py
# ============================================
from enum import StrEnum


class CompanyMembershipStatus(StrEnum):
    INVITED = "invited"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REMOVED = "removed"


class CompanyMembershipRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    COMPLIANCE_CONTACT = "compliance_contact"
    SALES_CONTACT = "sales_contact"
    LOGISTICS_CONTACT = "logistics_contact"
    VIEWER = "viewer"


# ============================================
# FILE: app/modules/company_memberships/domain/entities.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
from app.shared.domain.base import AuditFields
from app.shared.domain.exceptions import ValidationDomainError
from app.shared.domain.status_transition import ensure_transition


@dataclass(slots=True)
class CompanyMembership(AuditFields):
    status: CompanyMembershipStatus
    company_id: UUID
    user_id: UUID
    membership_role: CompanyMembershipRole
    is_primary_contact: bool
    invited_at: datetime | None
    joined_at: datetime | None
    left_at: datetime | None

    def validate(self) -> None:
        if not self.company_id:
            raise ValidationDomainError("Membership company_id is required")
        if not self.user_id:
            raise ValidationDomainError("Membership user_id is required")

    def transition_status(self, to_status: CompanyMembershipStatus) -> None:
        allowed = {
            CompanyMembershipStatus.INVITED: {CompanyMembershipStatus.ACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.ACTIVE: {CompanyMembershipStatus.INACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.INACTIVE: {CompanyMembershipStatus.ACTIVE, CompanyMembershipStatus.REMOVED},
            CompanyMembershipStatus.REMOVED: set(),
        }
        ensure_transition(self.status.value, to_status.value, {s.value for s in allowed[self.status]})
        self.status = to_status


# ============================================
# FILE: app/modules/company_memberships/domain/repositories.py
# ============================================
from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.company_memberships.domain.entities import CompanyMembership


class CompanyMembershipRepository(ABC):
    @abstractmethod
    async def add(self, membership: CompanyMembership) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, membership_id: UUID) -> CompanyMembership | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_company_id(self, company_id: UUID, status: str | None = None) -> list[CompanyMembership]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[CompanyMembership]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, membership: CompanyMembership) -> None:
        raise NotImplementedError


# ============================================
# FILE: app/modules/company_memberships/application/dto.py
# ============================================
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class CompanyMembershipDTO:
    id: UUID
    status: str
    company_id: UUID
    user_id: UUID
    membership_role: str
    is_primary_contact: bool
    invited_at: datetime | None
    joined_at: datetime | None
    left_at: datetime | None
    created_at: datetime
    created_by_user_id: UUID | None
    updated_at: datetime
    updated_by_user_id: UUID | None


# ============================================
# FILE: app/modules/company_memberships/application/mappers.py
# ============================================
from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.domain.entities import CompanyMembership


def to_membership_dto(entity: CompanyMembership) -> CompanyMembershipDTO:
    return CompanyMembershipDTO(
        id=entity.id,
        status=entity.status.value,
        company_id=entity.company_id,
        user_id=entity.user_id,
        membership_role=entity.membership_role.value,
        is_primary_contact=entity.is_primary_contact,
        invited_at=entity.invited_at,
        joined_at=entity.joined_at,
        left_at=entity.left_at,
        created_at=entity.created_at,
        created_by_user_id=entity.created_by_user_id,
        updated_at=entity.updated_at,
        updated_by_user_id=entity.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/company_memberships/application/services.py
# ============================================
from uuid import UUID

from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.application.mappers import to_membership_dto
from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
from app.modules.company_memberships.domain.repositories import CompanyMembershipRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.domain.exceptions import NotFoundDomainError


class CreateCompanyMembershipService:
    def __init__(self, repo: CompanyMembershipRepository, uuid_generator: UuidGenerator, clock: Clock):
        self.repo = repo
        self.uuid_generator = uuid_generator
        self.clock = clock

    async def execute(
        self,
        *,
        company_id: UUID,
        user_id: UUID,
        membership_role: str,
        is_primary_contact: bool,
        actor_user_id: UUID | None,
    ) -> CompanyMembershipDTO:
        now = self.clock.now()
        membership = CompanyMembership(
            id=self.uuid_generator.new(),
            status=CompanyMembershipStatus.ACTIVE,
            company_id=company_id,
            user_id=user_id,
            membership_role=CompanyMembershipRole(membership_role),
            is_primary_contact=is_primary_contact,
            invited_at=now,
            joined_at=now,
            left_at=None,
            created_at=now,
            created_by_user_id=actor_user_id,
            updated_at=now,
            updated_by_user_id=actor_user_id,
        )
        membership.validate()
        await self.repo.add(membership)
        return to_membership_dto(membership)


class ListCompanyMembershipsService:
    def __init__(self, repo: CompanyMembershipRepository):
        self.repo = repo

    async def execute(self, *, company_id: UUID, status: str | None) -> list[CompanyMembershipDTO]:
        items = await self.repo.list_by_company_id(company_id, status)
        return [to_membership_dto(item) for item in items]


class UpdateCompanyMembershipService:
    def __init__(self, repo: CompanyMembershipRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(
        self,
        *,
        membership_id: UUID,
        membership_role: str | None,
        is_primary_contact: bool | None,
        actor_user_id: UUID | None,
    ) -> CompanyMembershipDTO:
        membership = await self.repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundDomainError("Company membership not found")
        if membership_role is not None:
            membership.membership_role = CompanyMembershipRole(membership_role)
        if is_primary_contact is not None:
            membership.is_primary_contact = is_primary_contact
        membership.updated_at = self.clock.now()
        membership.updated_by_user_id = actor_user_id
        await self.repo.update(membership)
        return to_membership_dto(membership)


class TransitionCompanyMembershipStatusService:
    def __init__(self, repo: CompanyMembershipRepository, clock: Clock):
        self.repo = repo
        self.clock = clock

    async def execute(self, *, membership_id: UUID, to_status: str, actor_user_id: UUID | None) -> CompanyMembershipDTO:
        membership = await self.repo.get_by_id(membership_id)
        if not membership:
            raise NotFoundDomainError("Company membership not found")
        membership.transition_status(CompanyMembershipStatus(to_status))
        membership.updated_at = self.clock.now()
        membership.updated_by_user_id = actor_user_id
        await self.repo.update(membership)
        return to_membership_dto(membership)


# ============================================
# FILE: app/modules/company_memberships/infrastructure/models.py
# ============================================
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.infrastructure.db.base import Base


class CompanyMembershipModel(Base):
    __tablename__ = "company_memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    membership_role: Mapped[str] = mapped_column(String(64), nullable=False)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, nullable=False)
    invited_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    joined_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    left_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ============================================
# FILE: app/modules/company_memberships/infrastructure/mappers.py
# ============================================
from uuid import UUID

from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.enums import CompanyMembershipRole, CompanyMembershipStatus
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel


def to_domain(model: CompanyMembershipModel) -> CompanyMembership:
    return CompanyMembership(
        id=UUID(model.id),
        status=CompanyMembershipStatus(model.status),
        company_id=UUID(model.company_id),
        user_id=UUID(model.user_id),
        membership_role=CompanyMembershipRole(model.membership_role),
        is_primary_contact=model.is_primary_contact,
        invited_at=model.invited_at,
        joined_at=model.joined_at,
        left_at=model.left_at,
        created_at=model.created_at,
        created_by_user_id=UUID(model.created_by_user_id) if model.created_by_user_id else None,
        updated_at=model.updated_at,
        updated_by_user_id=UUID(model.updated_by_user_id) if model.updated_by_user_id else None,
    )


def to_model(entity: CompanyMembership) -> CompanyMembershipModel:
    return CompanyMembershipModel(
        id=str(entity.id),
        status=entity.status.value,
        company_id=str(entity.company_id),
        user_id=str(entity.user_id),
        membership_role=entity.membership_role.value,
        is_primary_contact=entity.is_primary_contact,
        invited_at=entity.invited_at,
        joined_at=entity.joined_at,
        left_at=entity.left_at,
        created_at=entity.created_at,
        created_by_user_id=str(entity.created_by_user_id) if entity.created_by_user_id else None,
        updated_at=entity.updated_at,
        updated_by_user_id=str(entity.updated_by_user_id) if entity.updated_by_user_id else None,
    )


# ============================================
# FILE: app/modules/company_memberships/infrastructure/repositories.py
# ============================================
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_memberships.domain.entities import CompanyMembership
from app.modules.company_memberships.domain.repositories import CompanyMembershipRepository
from app.modules.company_memberships.infrastructure.mappers import to_domain, to_model
from app.modules.company_memberships.infrastructure.models import CompanyMembershipModel


class SqlAlchemyCompanyMembershipRepository(CompanyMembershipRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, membership: CompanyMembership) -> None:
        self.session.add(to_model(membership))
        await self.session.commit()

    async def get_by_id(self, membership_id: UUID) -> CompanyMembership | None:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.id == str(membership_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return to_domain(model) if model else None

    async def list_by_company_id(self, company_id: UUID, status: str | None = None) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.company_id == str(company_id))
        if status:
            stmt = stmt.where(CompanyMembershipModel.status == status)
        stmt = stmt.order_by(CompanyMembershipModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def list_by_user_id(self, user_id: UUID) -> list[CompanyMembership]:
        stmt = select(CompanyMembershipModel).where(CompanyMembershipModel.user_id == str(user_id))
        stmt = stmt.order_by(CompanyMembershipModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [to_domain(item) for item in result.scalars().all()]

    async def update(self, membership: CompanyMembership) -> None:
        model = await self.session.get(CompanyMembershipModel, str(membership.id))
        if model is None:
            return
        model.status = membership.status.value
        model.membership_role = membership.membership_role.value
        model.is_primary_contact = membership.is_primary_contact
        model.invited_at = membership.invited_at
        model.joined_at = membership.joined_at
        model.left_at = membership.left_at
        model.updated_at = membership.updated_at
        model.updated_by_user_id = str(membership.updated_by_user_id) if membership.updated_by_user_id else None
        await self.session.commit()


# ============================================
# FILE: app/modules/company_memberships/presentation/schemas.py
# ============================================
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyMembershipCreateRequest(BaseModel):
    userId: UUID
    membershipRole: str
    isPrimaryContact: bool = False


class CompanyMembershipUpdateRequest(BaseModel):
    membershipRole: str | None = None
    isPrimaryContact: bool | None = None


class CompanyMembershipStatusTransitionRequest(BaseModel):
    toStatus: str


class CompanyMembershipData(BaseModel):
    id: UUID
    status: str
    companyId: UUID
    userId: UUID
    membershipRole: str
    isPrimaryContact: bool
    invitedAt: datetime | None
    joinedAt: datetime | None
    leftAt: datetime | None
    createdAt: datetime
    createdByUserId: UUID | None
    updatedAt: datetime
    updatedByUserId: UUID | None


class CompanyMembershipResponse(BaseModel):
    data: CompanyMembershipData


class PaginatedCompanyMembershipsResponse(BaseModel):
    items: list[CompanyMembershipData]
    meta: dict


# ============================================
# FILE: app/modules/company_memberships/presentation/mappers.py
# ============================================
from app.modules.company_memberships.application.dto import CompanyMembershipDTO
from app.modules.company_memberships.presentation.schemas import CompanyMembershipData


def to_membership_data(dto: CompanyMembershipDTO) -> CompanyMembershipData:
    return CompanyMembershipData(
        id=dto.id,
        status=dto.status,
        companyId=dto.company_id,
        userId=dto.user_id,
        membershipRole=dto.membership_role,
        isPrimaryContact=dto.is_primary_contact,
        invitedAt=dto.invited_at,
        joinedAt=dto.joined_at,
        leftAt=dto.left_at,
        createdAt=dto.created_at,
        createdByUserId=dto.created_by_user_id,
        updatedAt=dto.updated_at,
        updatedByUserId=dto.updated_by_user_id,
    )


# ============================================
# FILE: app/modules/company_memberships/presentation/dependencies.py
# ============================================
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company_memberships.application.services import (
    CreateCompanyMembershipService,
    ListCompanyMembershipsService,
    TransitionCompanyMembershipStatusService,
    UpdateCompanyMembershipService,
)
from app.modules.company_memberships.infrastructure.repositories import SqlAlchemyCompanyMembershipRepository
from app.shared.application.clock import Clock
from app.shared.application.uuid_generator import UuidGenerator
from app.shared.infrastructure.db.session import get_db_session


def get_membership_repo(session: AsyncSession = Depends(get_db_session)) -> SqlAlchemyCompanyMembershipRepository:
    return SqlAlchemyCompanyMembershipRepository(session)


def get_create_membership_service(repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo)) -> CreateCompanyMembershipService:
    return CreateCompanyMembershipService(repo=repo, uuid_generator=UuidGenerator(), clock=Clock())


def get_list_memberships_service(repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo)) -> ListCompanyMembershipsService:
    return ListCompanyMembershipsService(repo=repo)


def get_update_membership_service(repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo)) -> UpdateCompanyMembershipService:
    return UpdateCompanyMembershipService(repo=repo, clock=Clock())


def get_transition_membership_status_service(repo: SqlAlchemyCompanyMembershipRepository = Depends(get_membership_repo)) -> TransitionCompanyMembershipStatusService:
    return TransitionCompanyMembershipStatusService(repo=repo, clock=Clock())


# ============================================
# FILE: app/modules/company_memberships/presentation/router.py
# ============================================
from uuid import UUID

from fastapi import APIRouter, Depends

from app.modules.company_memberships.presentation.dependencies import (
    get_create_membership_service,
    get_list_memberships_service,
    get_transition_membership_status_service,
    get_update_membership_service,
)
from app.modules.company_memberships.presentation.mappers import to_membership_data
from app.modules.company_memberships.presentation.schemas import (
    CompanyMembershipCreateRequest,
    CompanyMembershipResponse,
    CompanyMembershipStatusTransitionRequest,
    CompanyMembershipUpdateRequest,
)
from app.shared.presentation.auth_dependencies import require_current_user

router = APIRouter(tags=["company-memberships"])


@router.get("/companies/{company_id}/memberships")
async def list_company_memberships(
    company_id: UUID,
    status: str | None = None,
    current_user=Depends(require_current_user),
    service=Depends(get_list_memberships_service),
):
    items = await service.execute(company_id=company_id, status=status)
    return {
        "items": [to_membership_data(item).model_dump() for item in items],
        "meta": {"page": 1, "pageSize": len(items), "total": len(items)},
    }


@router.post("/companies/{company_id}/memberships", response_model=CompanyMembershipResponse, status_code=201)
async def create_company_membership(
    company_id: UUID,
    payload: CompanyMembershipCreateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_create_membership_service),
):
    dto = await service.execute(
        company_id=company_id,
        user_id=payload.userId,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch("/company-memberships/{membership_id}", response_model=CompanyMembershipResponse)
async def update_company_membership(
    membership_id: UUID,
    payload: CompanyMembershipUpdateRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_update_membership_service),
):
    dto = await service.execute(
        membership_id=membership_id,
        membership_role=payload.membershipRole,
        is_primary_contact=payload.isPrimaryContact,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))


@router.patch("/company-memberships/{membership_id}/status", response_model=CompanyMembershipResponse)
async def transition_company_membership_status(
    membership_id: UUID,
    payload: CompanyMembershipStatusTransitionRequest,
    current_user=Depends(require_current_user),
    service=Depends(get_transition_membership_status_service),
):
    dto = await service.execute(
        membership_id=membership_id,
        to_status=payload.toStatus,
        actor_user_id=current_user.user.id,
    )
    return CompanyMembershipResponse(data=to_membership_data(dto))
