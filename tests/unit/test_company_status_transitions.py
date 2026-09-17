"""Unit tests for company status admin gating."""

from app.modules.companies.presentation.router import _is_admin


class _U:
    def __init__(self, email=None, roles=None):
        self.email = email
        self.roleCodes = roles or []


class _CU:
    def __init__(self, user=None, roles=None, email=None):
        self.user = user
        self.roleCodes = roles or []
        if email and user is None:
            self.email = email


def test_is_admin_email_match(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "admin@x.sk", raising=False)
    cu = _CU(user=_U(email="admin@x.sk"))
    assert _is_admin(cu) is True


def test_is_admin_email_miss(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "admin@x.sk", raising=False)
    cu = _CU(user=_U(email="other@y.sk"))
    assert _is_admin(cu) is False


def test_is_admin_role_admin(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "admin@x.sk", raising=False)
    cu = _CU(user=_U(email="other@y.sk"), roles=["admin"])
    assert _is_admin(cu) is True


def test_is_admin_role_platform_admin(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "admin@x.sk", raising=False)
    cu = _CU(user=_U(email="other@y.sk"), roles=["platform_admin"])
    assert _is_admin(cu) is True


def test_is_admin_no_email_no_roles(monkeypatch):
    from app.core import config as cfg

    monkeypatch.setattr(cfg.settings, "PLATFORM_ADMIN_EMAILS", "admin@x.sk", raising=False)
    cu = _CU()
    assert _is_admin(cu) is False
