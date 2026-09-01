#!/usr/bin/env python3

from __future__ import annotations

import ast
import importlib
import sys
import traceback
from pathlib import Path


ROOT = Path.cwd()
APP = ROOT / "app"

IGNORE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}


def ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def module_name(path: Path) -> str:
    relative = path.relative_to(ROOT)

    if relative.name == "__init__.py":
        parts = relative.parent.parts
    else:
        parts = relative.with_suffix("").parts

    return ".".join(parts)


def resolve_relative(
    current_module: str,
    level: int,
    imported: str | None,
) -> str:
    package = current_module.split(".")[:-1]

    if level > len(package) + 1:
        return imported or ""

    base = package[: len(package) - (level - 1)]

    if imported:
        return ".".join(base + imported.split("."))
    return ".".join(base)


def collect_imports(path: Path):
    current = module_name(path)

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        tree = ast.parse(
            source,
            filename=str(path),
        )
    except Exception:
        return []

    result = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                result.append(
                    {
                        "module": alias.name,
                        "relative": False,
                        "line": node.lineno,
                    }
                )

        elif isinstance(node, ast.ImportFrom):

            if node.level > 0:
                resolved = resolve_relative(
                    current,
                    node.level,
                    node.module,
                )

                result.append(
                    {
                        "module": resolved,
                        "relative": True,
                        "line": node.lineno,
                    }
                )

            elif node.module:
                result.append(
                    {
                        "module": node.module,
                        "relative": False,
                        "line": node.lineno,
                    }
                )

    return result


def runtime_import(module: str):
    try:
        importlib.import_module(module)
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main():
    print("=" * 78)
    print(" WASTE PLATFORM - RUNTIME IMPORT FORENSIC AUDIT")
    print("=" * 78)

    print()
    print("ROOT:")
    print(ROOT)

    print()
    print("PYTHON:")
    print(sys.version)

    print()
    print("=" * 78)
    print("1. DISCOVERING PROJECT MODULES")
    print("=" * 78)

    project_modules = set()

    for path in APP.rglob("*.py"):

        if ignored(path):
            continue

        try:
            project_modules.add(module_name(path))
        except Exception:
            pass

    print(
        f"Project modules discovered: {len(project_modules)}"
    )

    print()
    print("=" * 78)
    print("2. RUNTIME IMPORT TEST")
    print("=" * 78)

    all_imports = {}
    failures = {}

    for path in APP.rglob("*.py"):

        if ignored(path):
            continue

        for item in collect_imports(path):

            module = item["module"]

            if not module:
                continue

            key = (
                module,
                str(path.relative_to(ROOT)),
                item["line"],
            )

            all_imports[key] = item

    print(
        f"Unique import references: {len(all_imports)}"
    )

    for (
        module,
        filename,
        line,
    ) in sorted(all_imports):

        ok, error = runtime_import(module)

        if ok:
            print(
                f"[OK]       {module}"
                f"  <- {filename}:{line}"
            )

        else:
            failures.setdefault(
                module,
                [],
            ).append(
                {
                    "file": filename,
                    "line": line,
                    "error": error,
                }
            )

    print()
    print("=" * 78)
    print("3. ACTUAL RUNTIME FAILURES")
    print("=" * 78)

    if not failures:
        print()
        print("OK: no runtime import failures detected.")

    else:

        for module in sorted(failures):

            print()
            print(
                f"[BROKEN] {module}"
            )

            for item in failures[module]:

                print(
                    f"    {item['file']}:{item['line']}"
                )

                print(
                    f"    {item['error']}"
                )

    print()
    print("=" * 78)
    print("4. DIRECT app.main TEST")
    print("=" * 78)

    try:
        importlib.import_module("app.main")

        print()
        print("[OK] app.main imports successfully.")

    except Exception as exc:

        print()
        print("[BROKEN] app.main")

        print(
            f"{type(exc).__name__}: {exc}"
        )

        traceback.print_exc()

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)

    print()
    print(
        f"Import references : {len(all_imports)}"
    )

    print(
        f"Failed modules    : {len(failures)}"
    )

    if failures:
        print()
        print(
            "WARNING: real runtime import failures exist."
        )

    else:
        print()
        print(
            "OK: no runtime import failures detected."
        )

    print()
    print("=" * 78)
    print("IMPORTANT")
    print("=" * 78)

    print()
    print("This audit does NOT modify project files.")

    print()
    print("=" * 78)
    print("DONE")
    print("=" * 78)


if __name__ == "__main__":
    main()
