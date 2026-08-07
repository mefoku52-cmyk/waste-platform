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
