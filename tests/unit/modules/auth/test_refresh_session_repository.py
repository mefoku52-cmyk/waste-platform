"""Placeholder pre PostgresRefreshSessionRepository.

Repo je nedokonceny (chybaju metody get_active_by_user_id, revoke_family,
mapper pouziva nespravne atributy). Refresh flow funguje cez JWT + Redis,
tento repo sa nikde nepouziva. TODO: dokoncit alebo zmazat.

Tracked: vid TODO komentar v app/modules/auth/infrastructure/repositories.py
"""

import pytest


@pytest.mark.skip(reason="PostgresRefreshSessionRepository je nedokonceny (viď TODO v kode)")
def test_placeholder_until_repo_is_finished():
    pass
