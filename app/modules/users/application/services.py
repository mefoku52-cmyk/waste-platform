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
            status=UserStatus.PENDING_VERIFICATION,
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

    async def execute(
        self,
        *,
        status: str | None,
        company_id: UUID | None,
        q: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[UserDTO], int]:
        users, total = await self.repo.list(
            status=status, company_id=company_id, q=q, page=page, page_size=page_size
        )
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

    async def execute(
        self, *, user_id: UUID, to_status: str, actor_user_id: UUID | None
    ) -> UserDTO:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundDomainError("User not found")
        user.transition_status(UserStatus(to_status))
        user.updated_at = self.clock.now()
        user.updated_by_user_id = actor_user_id
        await self.repo.update(user)
        return to_user_dto(user)


class DeleteUserService:
    """Platform-admin only — tvrdo zmaze usera z DB + kompletny cleanup.

    Kontrola "nemozes zmazat sam seba" je v routeri, aby videl current_user.

    Preco komplexny cleanup:
      DB nema FK constraints na users.id, takze prosty DELETE by zanechal
      orphan zaznamy v 18 tabulkach. Tento service spravi v jednej transakcii:
        1. DELETE osobnych zaznamov (sessions, 2FA, notifikacie, pohlady)
        2. DELETE membershipov (user uz nie je clenom)
        3. UPDATE historickych zaznamov -> user referencia na NULL
        4. DELETE usera

    Ak hocijaky krok zlyha, transakcia sa rollback-ne a DB ostane nezmenena.
    """

    def __init__(self, session):
        self.session = session

    async def execute(self, *, user_id: UUID) -> None:
        from sqlalchemy import text

        uid = str(user_id)

        # 1. Over, ci user existuje
        exists = (
            await self.session.execute(text("SELECT 1 FROM users WHERE id = :uid"), {"uid": uid})
        ).scalar_one_or_none()
        if not exists:
            raise NotFoundDomainError("User not found")

        try:
            # 2. DELETE osobnych zaznamov
            for sql in [
                "DELETE FROM user_2fa WHERE user_id = :uid",
                "DELETE FROM refresh_sessions WHERE user_id = :uid",
                "DELETE FROM ai_conversations WHERE user_id = :uid",
                "DELETE FROM notifications WHERE user_id = :uid",
                "DELETE FROM listing_views WHERE user_id = :uid",
                "DELETE FROM activity_events WHERE actor_user_id = :uid",
                "DELETE FROM company_memberships WHERE user_id = :uid",
            ]:
                await self.session.execute(text(sql), {"uid": uid})

            # 3. Anonymizuj historicke zaznamy (NULL namiesto user_id)
            for sql in [
                "UPDATE chat_threads SET initiator_user_id = NULL WHERE initiator_user_id = :uid",
                "UPDATE chat_threads SET recipient_user_id = NULL WHERE recipient_user_id = :uid",
                "UPDATE chat_threads SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE chat_messages SET sender_user_id = NULL WHERE sender_user_id = :uid",
                "UPDATE chat_messages SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE admin_audit_entries SET actor_user_id = NULL WHERE actor_user_id = :uid",
                "UPDATE companies SET verified_by_user_id = NULL WHERE verified_by_user_id = :uid",
                "UPDATE companies SET rejected_by_user_id = NULL WHERE rejected_by_user_id = :uid",
                "UPDATE companies SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE listings SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE inquiries SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE documents SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE compliance_records SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE analytics_events SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE users SET created_by_user_id = NULL WHERE created_by_user_id = :uid",
                "UPDATE users SET updated_by_user_id = NULL WHERE updated_by_user_id = :uid",
            ]:
                await self.session.execute(text(sql), {"uid": uid})

            # 4. Zmaz usera
            await self.session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": uid})

            # 5. Commit (jedna atomicka transakcia)
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise
