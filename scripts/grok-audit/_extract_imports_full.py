import ast
import pathlib
import sys

root = pathlib.Path("app")
stdlib = set(getattr(sys, "stdlib_module_names", []))
all_imports = {}
syntax_errors = []

if root.exists():
    for py_file in root.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError as e:
            syntax_errors.append(f"{py_file}: {e}")
            continue
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue
                if node.module:
                    imports.add(node.module.split(".")[0])
        all_imports[str(py_file)] = sorted(imports)

print("=== IMPORTY PODLA SUBOROV ===")
for path in sorted(all_imports):
    print(f"[SUBOR] {path}")
    for mod in all_imports[path]:
        print(f"  - {mod}")

external = sorted({
    mod
    for mods in all_imports.values()
    for mod in mods
    if mod not in stdlib and mod != "app"
})
print("\n=== EXTERNE IMPORTY UNIKATNE ===")
for mod in external:
    print(mod)

print("\n=== SYNTAX CHYBY ===")
if syntax_errors:
    for err in syntax_errors:
        print(err)
else:
    print("ZIADNE")
