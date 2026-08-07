import ast
import pathlib
import sys

STDLIB = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else set()

root = pathlib.Path("app")
found = set()

for py_file in root.rglob("*.py"):
    if "__pycache__" in py_file.parts:
        continue
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    except SyntaxError as e:
        print(f"[SYNTAX ERROR] {py_file}: {e}")
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                found.add(node.module.split(".")[0])

external = sorted(m for m in found if m not in STDLIB and m != "app")
for m in external:
    print(m)
