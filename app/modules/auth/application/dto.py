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


@dataclass(slots=True)
class LoginResult:
    """Vysledok login pokusu.

    Ak requires_2fa=True, access_token/refresh_token su prazdne a
    namiesto nich je two_factor_token (kratkodoby, 5 min).
    """

    requires_2fa: bool = False
    two_factor_token: str | None = None

    # Ak requires_2fa=False, pouziju sa tieto polia:
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 0
