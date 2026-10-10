"""Regression tests pre READ-ONLY project_read / project_list_dir tools.

Kryje: povolené čítanie, výpis, path traversal, symlink únik, denied dirs,
limity veľkosti/počtu, unknown tool. Žiadne write operácie neexistujú.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.modules.agent_platform.domain.tools.tool_request import ToolRequest
from app.modules.agent_platform.infrastructure.tools import project_read
from app.modules.agent_platform.infrastructure.tools.project_read import (
    ProjectReadHandler,
)


def _req(tool_name: str, args: dict) -> ToolRequest:
    return ToolRequest(
        request_id="req-1",
        tool_name=tool_name,
        actor_id="admin-1",
        actor_type="admin",
        arguments=args,
        reason="test",
    )


@pytest.fixture
def repo_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hi')\n")
    (tmp_path / "README.md").write_text("# readme\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("dep\n")
    monkeypatch.setattr(project_read, "_ALLOWED_ROOT", tmp_path.resolve())
    return tmp_path


@pytest.fixture
def handler() -> ProjectReadHandler:
    return ProjectReadHandler()


# ─── povolené operácie ──────────────────────────────────────────────────────


async def test_read_file_ok(handler: ProjectReadHandler, repo_root: Path) -> None:
    result = await handler.handle(_req("project_read_file", {"path": "app/main.py"}))
    assert result.success is True
    assert result.data["content"] == "print('hi')\n"
    assert result.data["path"] == "app/main.py"
    assert result.data["truncated"] is False


async def test_list_dir_ok(handler: ProjectReadHandler, repo_root: Path) -> None:
    result = await handler.handle(_req("project_list_dir", {"path": "app"}))
    assert result.success is True
    names = [e["name"] for e in result.data["entries"]]
    assert names == ["main.py"]


async def test_list_root_hides_denied_dirs(handler: ProjectReadHandler, repo_root: Path) -> None:
    result = await handler.handle(_req("project_list_dir", {"path": "."}))
    assert result.success is True
    names = {e["name"] for e in result.data["entries"]}
    assert ".git" not in names
    assert "node_modules" not in names
    assert "app" in names


async def test_list_empty_path_means_root(handler: ProjectReadHandler, repo_root: Path) -> None:
    """Tool schema hovorí 'Prázdny = koreň' — prázdny argument nesmie padať."""
    result = await handler.handle(_req("project_list_dir", {"path": ""}))
    assert result.success is True
    assert result.data["path"] == "."


async def test_read_leading_slash_is_treated_as_relative(
    handler: ProjectReadHandler, repo_root: Path
) -> None:
    """/etc/passwd nesmie čítať reálne /etc — číta sa len pod koreňom."""
    result = await handler.handle(_req("project_read_file", {"path": "/etc/passwd"}))
    assert result.success is False
    assert result.error_code == "NOT_FOUND"


# ─── path traversal / symlink únik ──────────────────────────────────────────


@pytest.mark.parametrize(
    "evil_path",
    [
        "../etc/passwd",
        "app/../../etc/passwd",
        "..",
        "../",
        "%2e%2e/etc/passwd",
        "a\\b",
        "app/main.py\x00.png",
        "x" * 2000,
    ],
)
async def test_traversal_denied(
    handler: ProjectReadHandler, repo_root: Path, evil_path: str
) -> None:
    result = await handler.handle(_req("project_read_file", {"path": evil_path}))
    assert result.success is False
    assert result.error_code == "PATH_DENIED"


async def test_symlink_file_escape_denied(
    handler: ProjectReadHandler, repo_root: Path, tmp_path_factory
) -> None:
    outside_root = tmp_path_factory.mktemp("outside")
    secret = outside_root / "secret.txt"
    secret.write_text("TOP SECRET")
    link = repo_root / "leak.txt"
    link.symlink_to(secret)

    result = await handler.handle(_req("project_read_file", {"path": "leak.txt"}))
    assert result.success is False
    assert result.error_code == "PATH_DENIED"
    assert result.error_message == "outside_root"


async def test_symlink_dir_escape_denied(
    handler: ProjectReadHandler, repo_root: Path, tmp_path_factory
) -> None:
    outside_root = tmp_path_factory.mktemp("outside_dir")
    (outside_root / "passwd").write_text("root:x:0:0")
    link = repo_root / "etclink"
    link.symlink_to(outside_root)

    result = await handler.handle(_req("project_read_file", {"path": "etclink/passwd"}))
    assert result.success is False
    assert result.error_code == "PATH_DENIED"


async def test_sibling_prefix_dir_escape_denied(
    handler: ProjectReadHandler, repo_root: Path
) -> None:
    """Starý startswith check by pustil /repo-evil vedľa /repo."""
    sibling = repo_root.parent / f"{repo_root.name}-evil"
    sibling.mkdir(exist_ok=True)
    (sibling / "secret.txt").write_text("leaked")
    link = repo_root / "sib"
    link.symlink_to(sibling)
    try:
        result = await handler.handle(_req("project_read_file", {"path": "sib/secret.txt"}))
        assert result.success is False
        assert result.error_code == "PATH_DENIED"
    finally:
        link.unlink(missing_ok=True)


# ─── denied directories (aj pri čítaní, nielen list) ────────────────────────


@pytest.mark.parametrize("path", [".git/config", "node_modules/dep.js"])
async def test_denied_dir_read_denied(
    handler: ProjectReadHandler, repo_root: Path, path: str
) -> None:
    result = await handler.handle(_req("project_read_file", {"path": path}))
    assert result.success is False
    assert result.error_code == "PATH_DENIED"
    assert result.error_message == "denied_directory"


# ─── limity ─────────────────────────────────────────────────────────────────


async def test_non_text_file_denied(handler: ProjectReadHandler, repo_root: Path) -> None:
    (repo_root / "image.png").write_bytes(b"\x89PNG")
    result = await handler.handle(_req("project_read_file", {"path": "image.png"}))
    assert result.success is False
    assert result.error_code == "PERMISSION"
    assert result.error_message == "not_a_text_file"


async def test_oversized_file_denied(handler: ProjectReadHandler, repo_root: Path) -> None:
    big = repo_root / "big.md"
    big.write_text("x" * (project_read._MAX_FILE_BYTES + 1))
    result = await handler.handle(_req("project_read_file", {"path": "big.md"}))
    assert result.success is False
    assert result.error_code == "PERMISSION"
    assert result.error_message.startswith("file_too_large")


async def test_long_content_is_truncated(handler: ProjectReadHandler, repo_root: Path) -> None:
    (repo_root / "long.md").write_text("y" * (project_read._MAX_CONTENT_CHARS + 500))
    result = await handler.handle(_req("project_read_file", {"path": "long.md"}))
    assert result.success is True
    assert len(result.data["content"]) == project_read._MAX_CONTENT_CHARS
    assert result.data["truncated"] is True


async def test_list_caps_entries(handler: ProjectReadHandler, repo_root: Path) -> None:
    many = repo_root / "many"
    many.mkdir()
    for i in range(project_read._MAX_LIST_ENTRIES + 50):
        (many / f"f{i:03d}.py").write_text("x")
    result = await handler.handle(_req("project_list_dir", {"path": "many"}))
    assert result.success is True
    assert result.data["count"] == project_read._MAX_LIST_ENTRIES


# ─── error mapping / nepovolené operácie ────────────────────────────────────


async def test_unknown_tool_rejected(handler: ProjectReadHandler, repo_root: Path) -> None:
    """Neexistujúca write-operácia (project_write_file) nemá handler."""
    result = await handler.handle(_req("project_write_file", {"path": "app/main.py"}))
    assert result.success is False
    assert result.error_code == "UNKNOWN_TOOL"


async def test_write_style_tool_name_not_served(
    handler: ProjectReadHandler, repo_root: Path
) -> None:
    for name in ("project_delete_file", "project_move_file", "project_write_file"):
        result = await handler.handle(_req(name, {"path": "app/main.py"}))
        assert result.success is False
        assert result.error_code == "UNKNOWN_TOOL"


async def test_read_missing_file_not_found(handler: ProjectReadHandler, repo_root: Path) -> None:
    result = await handler.handle(_req("project_read_file", {"path": "app/missing.py"}))
    assert result.success is False
    assert result.error_code == "NOT_FOUND"


async def test_list_on_file_denied(handler: ProjectReadHandler, repo_root: Path) -> None:
    result = await handler.handle(_req("project_list_dir", {"path": "README.md"}))
    assert result.success is False
    assert result.error_code == "PERMISSION"
    assert result.error_message == "not_a_directory"
