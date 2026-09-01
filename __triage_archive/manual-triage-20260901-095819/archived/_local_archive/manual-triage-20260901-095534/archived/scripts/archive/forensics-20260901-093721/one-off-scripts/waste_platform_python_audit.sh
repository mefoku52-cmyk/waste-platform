#!/data/data/com.termux/files/usr/bin/bash

set +e

PROJECT="$HOME/waste-platform"

echo "============================================================"
echo " WASTE PLATFORM - PYTHON DEPENDENCY AUDIT"
echo "============================================================"
echo
echo "Projekt: $PROJECT"
echo "Dátum:   $(date)"
echo

cd "$PROJECT" || exit 1

echo
echo "=== 1. PYTHON ==="
python --version
python -m pip --version

echo
echo "=== 2. PROJEKTOVÉ SÚBORY ==="
find . -maxdepth 3 -type f \
    \( -name 'requirements*.txt' \
    -o -name 'pyproject.toml' \
    -o -name 'setup.py' \
    -o -name 'setup.cfg' \
    -o -name 'Pipfile' \
    -o -name 'poetry.lock' \
    -o -name 'uv.lock' \
    \) \
    -print 2>/dev/null

echo
echo "=== 3. GIT ==="
git status --short 2>/dev/null
echo
git branch --show-current 2>/dev/null
echo
git log -1 --oneline 2>/dev/null

echo
echo "=== 4. PYTHON SÚBORY ==="
find . -type f -name '*.py' \
    -not -path './.git/*' \
    -not -path './venv/*' \
    -not -path './.venv/*' \
    | sort | head -200

echo
echo "=== 5. IMPORTY V PROJEKTE ==="

python - <<'PY'
import ast
import pathlib
import collections

root = pathlib.Path(".")
imports = collections.Counter()

for path in root.rglob("*.py"):
    if any(part in {".git", "venv", ".venv", "__pycache__"} for part in path.parts):
        continue

    try:
        tree = ast.parse(path.read_text(errors="ignore"))
    except Exception:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports[n.name.split(".")[0]] += 1

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports[node.module.split(".")[0]] += 1

for name, count in imports.most_common():
    print(f"{name:35} {count}")
PY

echo
echo "=== 6. PIP CHECK ==="
python -m pip check

echo
echo "=== 7. PYTHON BALÍKY ==="
python -m pip list --format=columns

echo
echo "=== 8. ENVIRONMENT ==="
env | grep -E '^(PYTHON|PATH|VIRTUAL_ENV|PIP)' | sort

echo
echo "============================================================"
echo " AUDIT HOTOVÝ - NIČ SA NEINŠTALOVALO ANI NEODSTRAŇOVALO"
echo "============================================================"
