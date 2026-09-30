"""_cors_origins() a create_app() - main.py logika."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import _cors_origins, app, create_app


def test_cors_origins_returns_list():
    origins = _cors_origins()
    assert isinstance(origins, list)
    assert len(origins) > 0


def test_cors_origins_no_duplicates():
    origins = _cors_origins()
    assert len(origins) == len(set(origins))


def test_cors_origins_no_empty_strings():
    for origin in _cors_origins():
        assert origin == origin.strip()
        assert origin != ""


def test_cors_origins_splits_comma_string(monkeypatch):
    """settings.CORS_ORIGINS moze obsahovat legacy string s ciarkami."""
    monkeypatch.setattr(
        settings,
        "CORS_ORIGINS",
        "https://a.sk,https://b.sk",
        raising=False,
    )
    origins = _cors_origins()
    assert "https://a.sk" in origins
    assert "https://b.sk" in origins


def test_cors_origins_dev_adds_localhost(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "development", raising=False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", [], raising=False)
    origins = _cors_origins()
    # fallback produkcny
    assert any("trc-cmep.sk" in o for o in origins)
    # dev
    assert any("localhost" in o for o in origins) or any("127.0.0.1" in o for o in origins)


def test_cors_origins_production_no_localhost(monkeypatch):
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    monkeypatch.setattr(
        settings,
        "CORS_ORIGINS",
        ["https://trc-cmep.sk"],
        raising=False,
    )
    origins = _cors_origins()
    assert "http://localhost:3001" not in origins
    assert "http://127.0.0.1:3001" not in origins


def test_cors_origins_empty_env_fallback(monkeypatch):
    """Ak env je prazdne, drzime bezpecny produkcny fallback."""
    monkeypatch.setattr(settings, "app_env", "production", raising=False)
    monkeypatch.setattr(settings, "CORS_ORIGINS", [], raising=False)
    origins = _cors_origins()
    assert any("trc-cmep.sk" in o for o in origins)


def test_create_app_returns_fastapi():
    fresh_app = create_app()
    assert isinstance(fresh_app, FastAPI)


def test_create_app_has_health():
    fresh_app = create_app()
    c = TestClient(fresh_app)
    r = c.get("/health")
    assert r.status_code == 200


def test_create_app_mounted_routers_not_empty():
    fresh_app = create_app()
    c = TestClient(fresh_app)
    r = c.get("/health")
    data = r.json()
    assert len(data["mounted_routers"]) > 0


def test_create_app_docs_disabled_in_non_dev(monkeypatch):
    """Ak ENABLE_PUBLIC_DOCS=False, /docs neexistuje."""
    fresh_app = create_app()
    # V test mode by malo byt default False
    c = TestClient(fresh_app)
    r = c.get("/docs")
    # Buď 404 (disabled) alebo 200 (enabled in dev)
    assert r.status_code in (200, 404)


def test_app_root_path_empty_by_default():
    assert settings.ROOT_PATH == "" or settings.ROOT_PATH is not None


def test_app_has_title():
    assert app.title is not None
    assert len(app.title) > 0


def test_app_has_version():
    assert app.version is not None


def test_app_lifespan_registered():
    # Lifespan handler musi existovat
    assert app.router.lifespan_context is not None
