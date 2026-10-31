from app.core.config import Settings


def _settings(**overrides):
    return Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="strong-test-secret-value-with-more-than-32-chars",
        DATABASE_URL="postgresql+asyncpg://user:pass@127.0.0.1/test_db",
        **overrides,
    )


def test_rate_limiting_defaults_enabled_outside_development(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    assert _settings().rate_limit.enabled is True


def test_explicit_rate_limit_disable_remains_an_operator_override(monkeypatch):
    monkeypatch.delenv("RATE_LIMIT_ENABLED", raising=False)
    assert _settings(RATE_LIMIT_ENABLED=False).rate_limit.enabled is False
