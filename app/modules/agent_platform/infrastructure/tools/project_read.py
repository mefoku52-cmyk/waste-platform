"""READ-ONLY direct project file tools.

Nezávislé od OpenList. Priamy prístup k ~/waste-platform cez Python.
Bezpečnostný model:
- ALLOWED_ROOT pevne definovaný (nie konfigurovateľný z promptu).
- Path traversal zakázaný (resolve() + startswith check).
- Iba TEXT súbory, max 1 MB.
- Iba read/list. Žiadny write/delete/move.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ...domain.tools.tool_request import ToolRequest
from ...domain.tools.tool_result import ToolResult

_ALLOWED_ROOT = Path(
    os.getenv(
        "PROJECT_READ_ROOT",
        str(Path.home() / "waste-platform"),
    )
).resolve()

_MAX_FILE_BYTES = 1_048_576  # 1 MB
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

    candidate = (_ALLOWED_ROOT / path).resolve()
    if not str(candidate).startswith(str(_ALLOWED_ROOT)):
        raise ProjectPathDenied("outside_root")
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
            if name == "project.read_file":
                return await self._read(request, args)
            if name == "project.list_dir":
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
                "content": content[:100_000],
                "truncated": size > 100_000,
            },
        )

    async def _list(self, request: ToolRequest, args: dict) -> ToolResult:
        path = str(args.get("path") or "")
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
