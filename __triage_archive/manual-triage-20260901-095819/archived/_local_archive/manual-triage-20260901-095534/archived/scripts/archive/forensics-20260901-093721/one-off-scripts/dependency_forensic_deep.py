#!/usr/bin/env python3

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path


ROOT = Path.cwd()
APP = ROOT / "app"


def module_exists(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ModuleNotFoundError, AttributeError, ValueError):
        return False


def is_project_module(module: str) -> bool:
    parts = module.split(".")
    path = APP.joinpath(*parts)

    return (
        path.with_suffix(".py").exists()
        or path.is_dir()
    )


def inspect_file(path: Path) -> list[tuple[str, str, int]]:
    results = []

    try:
        source = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        tree = ast.parse(source, filename=str(path))
    except Exception:
        return results

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                results.append(
                    (
                        "import",
                        alias.name,
                        node.lineno,
                    )
                )

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                results.append(
                    (
                        "from",
                        node.module,
                        node.lineno,
                    )
                )

    return results


def main() -> None:

    print("=" * 78)
    print(" WASTE PLATFORM - DEEP IMPORT FORENSIC")
    print("=" * 78)

    print()
    print("ROOT:")
    print(ROOT)

    print()
    print("PYTHON:")
    print(sys.version)

    imports: dict[str, list[str]] = {}

    for path in APP.rglob("*.py"):

        relative = path.relative_to(ROOT)

        for kind, module, lineno in inspect_file(path):

            imports.setdefault(module, []).append(
                f"{relative}:{lineno}"
            )

    print()
    print("=" * 78)
    print(" 1. IMPORT RESOLUTION")
    print("=" * 78)

    for module in sorted(imports):

        top = module.split(".", 1)[0]

        if top in sys.stdlib_module_names:
            status = "STDLIB"

        elif is_project_module(module):
            status = "PROJECT"

        elif module_exists(module):
            status = "INSTALLED"

        else:
            status = "UNRESOLVED"

        print(
            f"{status:12} "
            f"{module:45} "
            f"{len(imports[module]):4} refs"
        )

    print()
    print("=" * 78)
    print(" 2. UNRESOLVED IMPORT LOCATIONS")
    print("=" * 78)

    unresolved = []

    for module in sorted(imports):

        top = module.split(".", 1)[0]

        if top in sys.stdlib_module_names:
            continue

        if is_project_module(module):
            continue

        if module_exists(module):
            continue

        unresolved.append(module)

        print()
        print(f"[UNRESOLVED] {module}")

        for location in imports[module][:20]:
            print(f"    {location}")

    print()
    print("=" * 78)
    print(" 3. RELATIVE IMPORTS")
    print("=" * 78)

    relative_count = 0

    for path in APP.rglob("*.py"):

        try:
            tree = ast.parse(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                ),
                filename=str(path),
            )
        except Exception:
            continue

        for node in ast.walk(tree):

            if isinstance(node, ast.ImportFrom):

                if node.level > 0:

                    relative_count += 1

                    print(
                        f"{path.relative_to(ROOT)}:"
                        f"{node.lineno} "
                        f"level={node.level} "
                        f"module={node.module}"
                    )

    print()
    print(
        f"Relative imports: {relative_count}"
    )

    print()
    print("=" * 78)
    print(" 4. DIRECT app.main IMPORT")
    print("=" * 78)

    try:

        import app.main  # noqa: F401

        print("[OK] app.main import")

    except Exception as exc:

        print("[FAIL] app.main import")
        print(
            f"{type(exc).__name__}: {exc}"
        )

    print()
    print("=" * 78)
    print(" 5. PYTHON PATH")
    print("=" * 78)

    for entry in sys.path:
        print(entry or "<EMPTY>")

    print()
    print("=" * 78)
    print(" SUMMARY")
    print("=" * 78)

    print(
        f"Total unique imports : {len(imports)}"
    )

    print(
        f"Unresolved imports   : {len(unresolved)}"
    )

    if unresolved:
        print()
        print(
            "WARNING: unresolved imports exist."
        )
    else:
        print()
        print(
            "OK: no unresolved imports detected."
        )

    print()
    print("=" * 78)
    print(" DONE")
    print("=" * 78)


if __name__ == "__main__":
    main()
