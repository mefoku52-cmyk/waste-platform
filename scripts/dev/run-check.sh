#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

cd "$HOME/waste-platform"

echo "== repo root =="
pwd
echo

echo "== key project files =="
find . -maxdepth 3 \( \
  -name "package.json" -o \
  -name "docker-compose.yml" -o \
  -name "compose.yaml" -o \
  -name "requirements.txt" -o \
  -name "pyproject.toml" -o \
  -name "vite.config.*" -o \
  -name "next.config.*" \
\) | sort
echo

echo "== git status --short =="
git status --short || true
echo

echo "== python version =="
python --version 2>&1 || true
echo

echo "== node version =="
node --version 2>&1 || true
echo

echo "== npm version =="
npm --version 2>&1 || true
