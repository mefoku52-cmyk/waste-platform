"""Tests for pure helpers in project_read."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.agent_platform.infrastructure.tools import project_read
from app.modules.agent_platform.infrastructure.tools.project_read import (
    ProjectPathDenied,
    _is_text_file,
    _resolve_under_root,
)


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(project_read, "_ALLOWED_ROOT", tmp_path.resolve())
    return tmp_path


def test_resolve_empty_raises() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("")


def test_resolve_nul_byte() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("a\x00b")


def test_resolve_backslash() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("a\\b")


def test_resolve_too_long() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("a" * 1025)


def test_resolve_url_encoded_traversal() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("a%2eb")


def test_resolve_parent_ref() -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root("../secret")


def test_resolve_denied_dir(root: Path) -> None:
    with pytest.raises(ProjectPathDenied):
        _resolve_under_root(".git/config")


def test_resolve_ok(root: Path) -> None:
    (root / "app").mkdir()
    (root / "app" / "main.py").write_text("x")
    p = _resolve_under_root("app/main.py")
    assert p == (root / "app" / "main.py").resolve()


def test_resolve_strips_leading_slash(root: Path) -> None:
    (root / "app").mkdir()
    p = _resolve_under_root("/app")
    assert p == (root / "app").resolve()


def test_is_text_file() -> None:
    assert _is_text_file(Path("foo.py")) is True
    assert _is_text_file(Path("Dockerfile")) is True
    assert _is_text_file(Path("foo.bin")) is False
    assert _is_text_file(Path("README")) is True
