#!/data/data/com.termux/files/usr/bin/bash

set +e

PROJECT="$HOME/waste-platform"
cd "$PROJECT" || exit 1

OUT="waste_platform_diagnosis_$(date +%Y%m%d-%H%M%S).txt"

exec > >(tee "$OUT") 2>&1

echo "============================================================"
echo " WASTE PLATFORM - DEEP DIAGNOSTIC"
echo "============================================================"
echo "Project: $PROJECT"
echo "Date:    $(date)"
echo

echo "============================================================"
echo "1. PYTHON"
echo "============================================================"

python --version
python -m pip --version
which python
which pip

echo
python - <<'PY'
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("sys.path:")
for p in sys.path:
    print(" ", p)
PY

echo
echo "============================================================"
echo "2. PROJECT STRUCTURE"
echo "============================================================"

find . -maxdepth 2 -type d \
  -not -path './.git*' \
  -not -path './app.backup*' \
  -not -path './.fix-backup*' \
  -not -path './.schema-authority-backup*' \
  | sort

echo
echo "============================================================"
echo "3. DEPENDENCY FILES"
echo "============================================================"

for f in \
    requirements.txt \
    app/requirements.txt \
    pyproject.toml \
    setup.py \
    setup.cfg \
    pytest.ini \
    alembic.ini
do
    if [ -f "$f" ]; then
        echo
        echo "----- $f -----"
        sed -n '1,260p' "$f"
    fi
done

echo
echo "============================================================"
echo "4. ACTIVE PYTHON FILES"
echo "============================================================"

find app \
  -type f \
  -name '*.py' \
  -not -path '*/__pycache__/*' \
  | sort

echo
echo "============================================================"
echo "5. ACTIVE IMPORTS - app ONLY"
echo "============================================================"

python - <<'PY'
import ast
import pathlib
from collections import Counter

root = pathlib.Path("app")
imports = Counter()

for path in root.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue

    try:
        source = path.read_text(errors="ignore")
        tree = ast.parse(source, filename=str(path))
    except Exception as e:
        print("PARSE ERROR:", path, e)
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports[n.name.split(".")[0]] += 1

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports[node.module.split(".")[0]] += 1

print("IMPORT                         COUNT")
print("-" * 45)

for name, count in imports.most_common():
    print(f"{name:30} {count}")
PY

echo
echo "============================================================"
echo "6. PYTHON SYNTAX CHECK"
echo "============================================================"

python - <<'PY'
import ast
import pathlib

root = pathlib.Path("app")
errors = 0
files = 0

for path in root.rglob("*.py"):
    if "__pycache__" in path.parts:
        continue

    files += 1

    try:
        ast.parse(
            path.read_text(errors="ignore"),
            filename=str(path)
        )
    except Exception as e:
        errors += 1
        print("[SYNTAX ERROR]", path)
        print(" ", e)

print()
print("Python files:", files)
print("Syntax errors:", errors)
PY

echo
echo "============================================================"
echo "7. APP IMPORT"
echo "============================================================"

python - <<'PY'
import importlib

mods = [
    "app",
    "app.main",
]

for mod in mods:
    try:
        m = importlib.import_module(mod)
        print("[OK]  ", mod, getattr(m, "__file__", ""))
    except Exception as e:
        print("[FAIL]", mod)
        print(type(e).__name__ + ":", e)
PY

echo
echo "============================================================"
echo "8. MAIN / FASTAPI ENTRYPOINTS"
echo "============================================================"

find app -type f -name '*.py' \
  -not -path '*/__pycache__/*' \
  -print0 |
while IFS= read -r -d '' f; do
    if grep -qE \
      'FastAPI|uvicorn|create_app|app *=' \
      "$f" 2>/dev/null; then

        echo
        echo "----- $f -----"
        grep -nE \
          'FastAPI|uvicorn|create_app|app *=|include_router' \
          "$f" 2>/dev/null | head -100
    fi
done

echo
echo "============================================================"
echo "9. DATABASE CONFIGURATION"
echo "============================================================"

grep -RniE \
  'DATABASE_URL|DATABASE_URI|postgres|postgresql|sqlite|asyncpg|psycopg|create_engine|create_async_engine' \
  app \
  --include='*.py' \
  --exclude-dir='__pycache__' \
  2>/dev/null \
  | head -300

echo
echo "============================================================"
echo "10. ALEMBIC"
echo "============================================================"

if command -v alembic >/dev/null 2>&1; then
    alembic current 2>&1
    echo
    alembic heads 2>&1
    echo
    alembic history --verbose 2>&1 | head -200
else
    echo "alembic command not found"
fi

echo
echo "============================================================"
echo "11. PYTEST DISCOVERY"
echo "============================================================"

if command -v pytest >/dev/null 2>&1; then
    pytest --collect-only -q 2>&1 | tail -100
else
    echo "pytest command not found"
fi

echo
echo "============================================================"
echo "12. PIP CHECK"
echo "============================================================"

python -m pip check

echo
echo "============================================================"
echo "13. CRITICAL PACKAGE VERSIONS"
echo "============================================================"

python - <<'PY'
import importlib.metadata as md

packages = [
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "alembic",
    "asyncpg",
    "psycopg2-binary",
    "uvicorn",
    "typer",
    "click",
    "httpx",
    "aiohttp",
    "cryptography",
    "pyOpenSSL",
    "redis",
    "pytest",
]

for name in packages:
    try:
        print(f"{name:25} {md.version(name)}")
    except md.PackageNotFoundError:
        print(f"{name:25} NOT INSTALLED")
PY

echo
echo "============================================================"
echo "14. GIT STATUS"
echo "============================================================"

git status --short

echo
echo "============================================================"
echo "15. CURRENT COMMIT"
echo "============================================================"

git log -1 --oneline
git branch --show-current

echo
echo "============================================================"
echo "16. POTENTIALLY DANGEROUS / DUPLICATE CONFIGS"
echo "============================================================"

find . \
  -type f \
  \( \
    -name '.env' \
    -o -name '.env.*' \
    -o -name '*config*.py' \
    -o -name '*settings*.py' \
    -o -name 'main.py' \
  \) \
  -not -path './.git/*' \
  -not -path './app.backup*/*' \
  -not -path './.fix-backup*/*' \
  -not -path './.schema-authority-backup*/*' \
  | sort

echo
echo "============================================================"
echo "17. RESULT"
echo "============================================================"

echo "Diagnosis saved to:"
echo "$PROJECT/$OUT"

echo
echo "IMPORTANT:"
echo "Nothing was installed."
echo "Nothing was removed."
echo "Nothing was modified."

echo
echo "============================================================"
