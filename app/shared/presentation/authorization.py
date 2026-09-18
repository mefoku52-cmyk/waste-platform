"""Single source of truth for platform-admin and tenant (company) authorization.

Pred tymto modulom bola logika "je admin" duplikovana na niekolkych miestach
(`shared.presentation.auth_dependencies`, `companies.presentation.router`) a v
kazdej kopia sa lisila (napr. natvrdo porovnanie s `admin@cmep.dev` namiesto
`settings.PLATFORM_ADMIN_EMAILS`). Tento modul ju zjednocuje.

Dve oddelene urovne opravneni (viz poziadavka na oddelenie platform-admin od
tenant/company ADMIN):

* **platform admin** — globalny operator platformy. Riadi sa vyhradne
  `settings.PLATFORM_ADMIN_EMAILS` a rezervovanou rolu `platform_admin`.
  **Nesmie** sa odvodzovat z firemneho clenstva: `role_codes` vznikaju len z
  `company_memberships.membership_role`, takze tenant rola `admin` je rola
  spravcu firmy — nie operatora platformy. (Presne toto bola escalated
  opravnenie chyba: firemny ADMIN ziskal platform-admin prava.)
* **company admin** — tenant-level spravca. Odvodeny z `membership_role`
  (`owner`, `admin`) v ramci konkretnej firmy.
"""

from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.shared.domain.exceptions import ForbiddenDomainError

# Rezervovane globalne roly. `admin` tu ZAMERNE nie je — v tomto modeli je to
# tenant rola (`CompanyMembershipRole.ADMIN`).
PLATFORM_ADMIN_ROLE_CODES = frozenset({"platform_admin"})
COMPANY_ADMIN_ROLES = frozenset({"owner", "admin"})

_ADMIN_EMAIL_CACHE: tuple[str, frozenset[str]] | None = None


def _platform_admin_emails() -> frozenset[str]:
    """Parsovane `PLATFORM_ADMIN_EMAILS` s cache podla aktualnej hodnoty."""
    global _ADMIN_EMAIL_CACHE

    raw = str(getattr(settings, "PLATFORM_ADMIN_EMAILS", "") or "")
    cached = _ADMIN_EMAIL_CACHE
    if cached is not None and cached[0] == raw:
        return cached[1]

    parsed = frozenset(item.strip().lower() for item in raw.split(",") if item.strip())
    _ADMIN_EMAIL_CACHE = (raw, parsed)
    return parsed


def _member_field(member: Any, *names: str) -> Any:
    """Precitaj pole z dict- alebo objektoveho clenstva."""
    if isinstance(member, dict):
        for name in names:
            if name in member:
                return member[name]
        return None
    for name in names:
        value = getattr(member, name, None)
        if value is not None:
            return value
    return None


def current_user_id(current_user: Any) -> str | None:
    """ID prihlaseneho usera napriec DTO/entita tvarmi."""
    user = getattr(current_user, "user", None)
    if user is not None:
        value = getattr(user, "id", None)
        if value is not None:
            return str(value)
    value = getattr(current_user, "id", None)
    return str(value) if value is not None else None


def current_user_email(current_user: Any) -> str:
    user = getattr(current_user, "user", None)
    if user is not None:
        return str(getattr(user, "email", "") or "").lower().strip()
    return str(getattr(current_user, "email", "") or "").lower().strip()


def role_codes(current_user: Any) -> set[str]:
    codes = getattr(current_user, "roleCodes", None)
    if codes is None:
        codes = getattr(current_user, "role_codes", None)
    return {str(code).lower() for code in (codes or [])}


def is_platform_admin(current_user: Any) -> bool:
    """Platform admin = email v allowliste ALEBO rezervovana globalna rola."""
    if current_user is None:
        return False
    if current_user_email(current_user) in _platform_admin_emails():
        return True
    return bool(role_codes(current_user) & PLATFORM_ADMIN_ROLE_CODES)


def memberships(current_user: Any) -> list[Any]:
    return list(getattr(current_user, "memberships", None) or [])


def membership_company_ids(current_user: Any) -> list[str]:
    """Company IDs, ktorych je user clenom (stringova forma pre porovnavanie)."""
    ids: list[str] = []
    for member in memberships(current_user):
        cid = _member_field(member, "companyId", "company_id")
        if cid is not None:
            ids.append(str(cid))
    return ids


def membership_role_in_company(current_user: Any, company_id: Any) -> str | None:
    target = str(company_id)
    for member in memberships(current_user):
        cid = _member_field(member, "companyId", "company_id")
        if cid is not None and str(cid) == target:
            role = _member_field(member, "membershipRole", "membership_role")
            return str(role).lower() if role is not None else None
    return None


def is_company_member(current_user: Any, company_id: Any) -> bool:
    if company_id is None:
        return False
    return str(company_id) in membership_company_ids(current_user)


def is_company_admin(current_user: Any, company_id: Any) -> bool:
    """Tenant admin — `owner`/`admin` v danej firme. Platform admin to nie je."""
    role = membership_role_in_company(current_user, company_id)
    return role in COMPANY_ADMIN_ROLES


def require_platform_admin(current_user: Any) -> Any:
    if not is_platform_admin(current_user):
        raise ForbiddenDomainError("Platform admin access required")
    return current_user


def require_company_member(current_user: Any, company_id: Any, *, action: str = "access") -> None:
    """Pusti platform admina alebo clena danej firmy."""
    if is_platform_admin(current_user):
        return
    if not is_company_member(current_user, company_id):
        raise ForbiddenDomainError(f"You do not have {action} to this company")


def require_company_admin(current_user: Any, company_id: Any, *, action: str = "manage") -> None:
    """Pusti platform admina alebo tenant admina (owner/admin) danej firmy."""
    if is_platform_admin(current_user):
        return
    if not is_company_admin(current_user, company_id):
        raise ForbiddenDomainError(f"You do not have {action} rights for this company")
