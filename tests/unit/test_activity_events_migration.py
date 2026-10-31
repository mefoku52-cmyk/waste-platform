"""Safety tests for the idempotent activity_events migration."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _migration_module():
    path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "b1a2c3d4e5f6_add_activity_events.py"
    )
    spec = spec_from_file_location("activity_events_migration", path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_upgrade_uses_create_if_not_exists(monkeypatch):
    module = _migration_module()
    statements = []
    monkeypatch.setattr(module.op, "execute", statements.append)

    module.upgrade()

    assert len(statements) == 1
    assert "CREATE TABLE IF NOT EXISTS activity_events" in statements[0]


def test_downgrade_does_not_drop_potentially_preexisting_table(monkeypatch):
    module = _migration_module()
    statements = []
    monkeypatch.setattr(module.op, "execute", statements.append)

    module.downgrade()

    assert statements == []
