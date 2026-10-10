"""READ-ONLY direct project file tools.

Nezávislé od OpenList. Priamy prístup k ~/waste-platform cez Python.
Bezpečnostný model:
- ALLOWED_ROOT pevne definovaný (nie konfigurovateľný z promptu).
- Path traversal zakázaný (resolve() + relative_to containment check).
- Symlinky mimo koreňa odmietnuté (resolve() nasleduje symlink pred checkom).
- Zakázané adresáre (.git, node_modules, ...) odmietnuté aj pri čítaní.
- Iba TEXT súbory, max 1 MB / 100k znakov.
- Iba read/list. Žiadny write/delete/move.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult


def _detect_repo_root() -> Path:
    """Nájdi koreň repa bezpečne naprieč prostrediami (Termux / Render / Docker).

    Priorita:
    1. PROJECT_READ_ROOT env (explicit override).
    2. Stúp z tohto súboru nahor, kým nenájdeš marker (pyproject.toml + app/).
    """
    env_root = os.getenv("PROJECT_READ_ROOT", "").strip()
    if env_root:
        return Path(env_root).resolve()

    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "app").is_dir():
            return parent
    # Fallback — 5 úrovní nahor (project_read.py → tools → infrastructure → agent_platform → modules → app → root)
    return here.parents[5] if len(here.parents) > 5 else here.parent


_ALLOWED_ROOT = _detect_repo_root().resolve()

_MAX_FILE_BYTES = 1_048_576  # 1 MB
_MAX_CONTENT_CHARS = 100_000
_MAX_LIST_ENTRIES = 200

# Rozšírenia ktoré považujeme za textové (bezpečné na čítanie)
_TEXT_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".env.example",
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".sh",
    ".bash",
    ".dockerfile",
    ".mako",
    ".jinja",
    ".j2",
}

_DENIED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".next",
    ".venv",
    "venv",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".turbo",
    ".cache",
    "coverage",
    "htmlcov",
}


class ProjectPathDenied(Exception):
    pass


def _resolve_under_root(path: str) -> Path:
    if not path or path.strip() == "":
        raise ProjectPathDenied("empty_path")
    if "\x00" in path:
        raise ProjectPathDenied("nul_byte")
    if "\\" in path:
        raise ProjectPathDenied("backslash_not_allowed")
    if len(path) > 1024:
        raise ProjectPathDenied("path_too_long")
    if "%2e" in path.lower():
        raise ProjectPathDenied("url_encoded_traversal")
    if ".." in Path(path).parts:
        raise ProjectPathDenied("parent_ref")
    if path.startswith("/"):
        path = path.lstrip("/")

    parts = [p for p in Path(path).parts if p not in ("", ".")]
    if any(part in _DENIED_DIRS for part in parts):
        raise ProjectPathDenied("denied_directory")

    candidate = (_ALLOWED_ROOT / path).resolve()
    try:
        candidate.relative_to(_ALLOWED_ROOT)
    except ValueError:
        # Zahŕňa symlinky, ktoré ukazujú mimo koreňa, aj sibling-prefix
        # adresáre (napr. /repo-evil vedľa /repo).
        raise ProjectPathDenied("outside_root") from None
    return candidate


def _is_text_file(p: Path) -> bool:
    ext = p.suffix.lower()
    if ext in _TEXT_EXTS:
        return True
    # Allow dotfiles without extension only if known
    return p.name in {"Dockerfile", "Makefile", ".gitignore", ".editorconfig", "README"}


class ProjectReadHandler:
    """READ-ONLY project tools. Not connected to OpenList."""

    async def handle(self, request: ToolRequest) -> ToolResult:
        name = request.tool_name
        args = request.arguments or {}
        try:
            if name == "project_read_file":
                return await self._read(request, args)
            if name == "project_list_dir":
                return await self._list(request, args)
        except ProjectPathDenied as e:
            return ToolResult(
                request_id=request.request_id,
                tool_name=name,
                success=False,
                error_code="PATH_DENIED",
                error_message=str(e),
            )
        except FileNotFoundError:
            return ToolResult(
                request_id=request.request_id,
                tool_name=name,
                success=False,
                error_code="NOT_FOUND",
                error_message="not_found",
            )
        except PermissionError as e:
            return ToolResult(
                request_id=request.request_id,
                tool_name=name,
                success=False,
                error_code="PERMISSION",
                error_message=str(e),
            )
        except Exception as e:
            return ToolResult(
                request_id=request.request_id,
                tool_name=name,
                success=False,
                error_code="TOOL_ERROR",
                error_message=type(e).__name__,
            )
        return ToolResult(
            request_id=request.request_id,
            tool_name=name,
            success=False,
            error_code="UNKNOWN_TOOL",
            error_message="unknown_tool",
        )

    async def _read(self, request: ToolRequest, args: dict) -> ToolResult:
        path = str(args.get("path") or "")
        target = _resolve_under_root(path)
        if not target.is_file():
            raise FileNotFoundError(path)
        if not _is_text_file(target):
            raise PermissionError("not_a_text_file")
        size = target.stat().st_size
        if size > _MAX_FILE_BYTES:
            raise PermissionError(f"file_too_large:{size}")
        content = target.read_text(encoding="utf-8", errors="replace")
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={
                "path": str(target.relative_to(_ALLOWED_ROOT)),
                "size": size,
                "content": content[:_MAX_CONTENT_CHARS],
                "truncated": size > _MAX_CONTENT_CHARS,
            },
        )

    async def _list(self, request: ToolRequest, args: dict) -> ToolResult:
        path = str(args.get("path") or "").strip()
        if path in ("", "."):
            path = "."  # prázdny / "." = koreň projektu (viď tool schema)
        target = _resolve_under_root(path)
        if not target.exists():
            raise FileNotFoundError(path)
        if not target.is_dir():
            raise PermissionError("not_a_directory")

        entries: list[dict[str, Any]] = []
        try:
            for child in sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name)):
                if len(entries) >= _MAX_LIST_ENTRIES:
                    break
                if child.name in _DENIED_DIRS:
                    continue
                entries.append(
                    {
                        "name": child.name,
                        "is_dir": child.is_dir(),
                        "size": child.stat().st_size if child.is_file() else 0,
                    }
                )
        except PermissionError:
            raise
        return ToolResult(
            request_id=request.request_id,
            tool_name=request.tool_name,
            success=True,
            data={
                "path": str(target.relative_to(_ALLOWED_ROOT)) or ".",
                "entries": entries,
                "count": len(entries),
            },
        )
