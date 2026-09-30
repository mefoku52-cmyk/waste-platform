from app.modules.auth.infrastructure.repositories import PostgresRefreshSessionRepository


def test_repo_has_missing_methods():
    assert hasattr(PostgresRefreshSessionRepository, "get_active_by_user_id")
    assert hasattr(PostgresRefreshSessionRepository, "revoke_family")
