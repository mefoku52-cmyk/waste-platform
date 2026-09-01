#!/usr/bin/env python3

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path.cwd()
APP = ROOT / "app"

IGNORE = {
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
    return any(part in IGNORE for part in path.parts)


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    return ".".join(rel.parts)


def collect_modules() -> dict[str, Path]:
    result: dict[str, Path] = {}

    for path in APP.rglob("*.py"):
        if ignored(path):
            continue

        mod = module_name(path)

        if path.name == "__init__.py":
            mod = ".".join(path.relative_to(ROOT).parent.parts)

        result[mod] = path

    return result


def resolve_relative(
    current: str,
    level: int,
    imported: str | None,
) -> str:
    parts = current.split(".")

    # Current module -> package
    if current.endswith("__init__"):
        package = parts
    else:
        package = parts[:-1]

    if level > len(package):
        return ""

    base = package[: len(package) - level + 1]

    if imported:
        base += imported.split(".")

    return ".".join(base)


def main() -> None:
    print("=" * 78)
    print(" WASTE PLATFORM - IMPORT REPAIR PLAN")
    print("=" * 78)
    print()
    print("ROOT:")
    print(ROOT)
    print()

    modules = collect_modules()

    print(f"Project modules discovered: {len(modules)}")
    print()

    problems: list[tuple[str, str, str, str]] = []

    for path in APP.rglob("*.py"):
        if ignored(path):
            continue

        current = module_name(path)

        if path.name == "__init__.py":
            current = ".".join(path.relative_to(ROOT).parent.parts)

        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        except Exception:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.ImportFrom):

                if node.level:
                    resolved = resolve_relative(
                        current,
                        node.level,
                        node.module,
                    )

                    if resolved and resolved in modules:
                        continue

                    if resolved:
                        problems.append(
                            (
                                "RELATIVE",
                                str(path.relative_to(ROOT)),
                                node.module or "",
                                resolved,
                            )
                        )

                else:
                    if not node.module:
                        continue

                    name = node.module

                    if name in modules:
                        continue

                    # Only report suspicious project-local imports.
                    if name in {
                        "application",
                        "dependencies",
                        "domain",
                        "domain.entities",
                        "domain.enums",
                        "domain.repositories",
                        "dto",
                        "entities",
                        "enums",
                        "infrastructure",
                        "infrastructure.repositories",
                        "mappers",
                        "models",
                        "repositories",
                        "router",
                        "schemas",
                        "service",
                        "services",
                        "session",
                    }:
                        problems.append(
                            (
                                "ABSOLUTE",
                                str(path.relative_to(ROOT)),
                                name,
                                "",
                            )
                        )

    print("=" * 78)
    print(" SUSPICIOUS PROJECT IMPORTS")
    print("=" * 78)

    if not problems:
        print()
        print("OK: no suspicious project imports found.")
    else:
        for kind, file, imported, resolved in problems:
            print()
            print(f"[{kind}] {file}")
            print(f"    import: {imported}")

            if resolved:
                print(f"    resolves to: {resolved}")

                if resolved in modules:
                    print(
                        f"    TARGET: {modules[resolved]}"
                    )
                else:
                    print(
                        "    TARGET: NOT FOUND"
                    )

    print()
    print("=" * 78)
    print(" SUMMARY")
    print("=" * 78)
    print()
    print(f"Suspicious imports: {len(problems)}")

    print()
    print("=" * 78)
    print(" IMPORTANT")
    print("=" * 78)
    print()
    print("This script does NOT modify any file.")
    print("It only produces a repair plan.")
    print()


if __name__ == "__main__":
    main()
