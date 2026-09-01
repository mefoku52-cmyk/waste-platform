#!/usr/bin/env python3

from __future__ import annotations

import ast
import importlib.metadata as md
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path.cwd()

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

IGNORE_PREFIXES = (
    ".fix-backup-",
    ".schema-authority-backup-",
    "app.backup.",
)


def ignored(path: Path) -> bool:
    parts = path.parts

    for part in parts:
        if part in IGNORE_DIRS:
            return True

        if part.startswith(IGNORE_PREFIXES):
            return True

    return False


def top_level_module(name: str) -> str:
    return name.split(".", 1)[0]


def collect_imports(root: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}

    for path in root.rglob("*.py"):
        if ignored(path):
            continue

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except Exception:
            continue

        imports: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(top_level_module(alias.name))

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(top_level_module(node.module))

        for module in imports:
            result.setdefault(module, []).append(
                str(path.relative_to(ROOT))
            )

    return result


def read_requirements() -> dict[str, list[str]]:
    files = [
        ROOT / "requirements.txt",
        ROOT / "app" / "requirements.txt",
    ]

    result = {}

    for path in files:
        if not path.exists():
            continue

        lines = []

        for raw in path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():

            line = raw.strip()

            if not line or line.startswith("#"):
                continue

            if line.startswith(("-", "git+", "http:", "https:")):
                lines.append(line)
                continue

            match = re.match(
                r"^([A-Za-z0-9_.-]+)",
                line,
            )

            if match:
                lines.append(line)

        result[str(path.relative_to(ROOT))] = lines

    return result


def installed_packages():
    packages = {}

    for dist in md.distributions():
        name = dist.metadata.get("Name")

        if name:
            packages[name.lower().replace("-", "_")] = {
                "name": name,
                "version": dist.version,
            }

    return packages


def main():
    print("=" * 72)
    print(" WASTE PLATFORM - DEPENDENCY FORENSIC AUDIT")
    print("=" * 72)
    print()

    print("ROOT:")
    print(ROOT)

    print()
    print("PYTHON:")
    print(sys.version)

    print()
    print("=== REQUIREMENTS ===")

    requirements = read_requirements()

    for filename, lines in requirements.items():
        print()
        print(filename)
        print("-" * len(filename))

        for line in lines:
            print(" ", line)

    print()
    print("=== PRODUCTION IMPORTS: app/ ===")

    imports = collect_imports(ROOT / "app")

    for module in sorted(imports):
        files = imports[module]

        print(
            f"{module:35} "
            f"{len(files):4} files"
        )

    print()
    print("=== INSTALLED DISTRIBUTIONS ===")

    installed = installed_packages()

    print(f"Installed distributions: {len(installed)}")

    print()
    print("=== IMPORTS WITH INSTALLED PACKAGE MATCH ===")

    stdlib = set(sys.stdlib_module_names)

    matched = []
    missing = []

    for module in sorted(imports):
        if module in stdlib:
            continue

        key = module.lower().replace("-", "_")

        if key in installed:
            matched.append(module)
        else:
            missing.append(module)

    print()
    print("MATCHED:")
    for module in matched:
        pkg = installed[
            module.lower().replace("-", "_")
        ]
        print(
            f"  {module:35} "
            f"{pkg['name']}=={pkg['version']}"
        )

    print()
    print("NOT FOUND AS DISTRIBUTION NAME:")
    for module in missing:
        print(f"  {module}")

    print()
    print("=== PIP CHECK ===")

    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "check",
        ],
        check=False,
    )

    report = {
        "root": str(ROOT),
        "python": sys.version,
        "requirements": requirements,
        "production_imports": {
            module: files
            for module, files in imports.items()
        },
        "installed_distributions": installed,
        "matched_imports": matched,
        "unmatched_imports": missing,
    }

    output = ROOT / "dependency-forensic-report.json"

    output.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(" HOTOVO")
    print("=" * 72)
    print()
    print(f"Report: {output}")


if __name__ == "__main__":
    main()
