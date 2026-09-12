#!/usr/bin/env python3
"""Skript na kontrolu importov a štruktúry projektu."""

import ast
import os


def check_imports(directory: str) -> dict[str, list[str]]:
    """Kontrola importov v Python súboroch."""
    imports = {}

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    tree = ast.parse(content)
                    imports[filepath] = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                imports[filepath].append(alias.name)
                        elif isinstance(node, ast.ImportFrom):
                            module = node.module or ""
                            for alias in node.names:
                                imports[filepath].append(f"{module}.{alias.name}")
                except Exception as e:
                    print(f"Chyba pri spracovaní {filepath}: {e}")

    return imports


def check_missing_modules(imports: dict[str, list[str]]) -> set[str]:
    """Kontrola chýbajúcich modulov."""
    missing = set()
    for filepath, modules in imports.items():
        for module in modules:
            try:
                __import__(module.split(".")[0])
            except ImportError:
                missing.add(module)
    return missing


def main():
    """Hlavná funkcia."""
    backend_dir = "backend/app"

    if not os.path.exists(backend_dir):
        print(f"Adresár {backend_dir} neexistuje")
        return

    # Kontrola štruktúry
    print("Kontrola štruktúry projektu...")
    required_dirs = [
        "api/v1",
        "core",
        "models",
        "schemas",
        "services",
        "repositories",
        "utils",
    ]
    for dir_path in required_dirs:
        full_path = os.path.join(backend_dir, dir_path)
        if os.path.exists(full_path):
            print(f"✓ {dir_path}")
        else:
            print(f"✗ {dir_path} - CHÝBA")

    # Kontrola importov
    print("\nKontrola importov...")
    imports = check_imports(backend_dir)
    missing = check_missing_modules(imports)

    if missing:
        print("Chýbajúce moduly:")
        for module in sorted(missing):
            print(f"  - {module}")
    else:
        print("Všetky importy sú v poriadku")

    # Kontrola __init__.py súborov
    print("\nKontrola __init__.py súborov...")
    for root, _, files in os.walk(backend_dir):
        if "__init__.py" not in files:
            init_path = os.path.join(root, "__init__.py")
            with open(init_path, "w") as f:
                f.write('"""Package initialization."""\n')
            print(f"Vytvorený {init_path}")


if __name__ == "__main__":
    main()
