#!/usr/bin/env bash
set -eu
cd "$HOME/waste-platform"
OUT="$HOME/waste-platform/scripts/grok-audit/evidence_pack.txt"

{
echo "===== META ====="
echo "DATE=$(date -Iseconds 2>/dev/null || date)"
echo "PWD=$(pwd)"
echo "USER=$(id -un)"
echo "HOST=$(hostname 2>/dev/null || echo unknown)"
echo "SHELL=$SHELL"
echo "BASH_VERSION=$BASH_VERSION"

echo
echo "===== Q1 SOURCE BOUNDARY ====="
ls -la
echo
echo "--- git ---"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "IN_GIT=yes"
  git rev-parse --show-toplevel
  git remote -v || true
  git branch -vv || true
  git status -sb || true
  git log -5 --oneline --decorate || true
  echo "HEAD_SHA=$(git rev-parse HEAD)"
  echo "HEAD_SUBJECT=$(git log -1 --pretty=%s)"
else
  echo "IN_GIT=no"
fi

echo
echo "===== Q2 TOPOLOGY ====="
find . -type d | grep -v '/node_modules' | grep -v '/.git/' | grep -v '/dist/' | grep -v '/.next/' | awk -F/ 'NF<=4' | sort | head -n 200
echo
echo "--- key files ---"
for f in docker-compose.yml docker-compose.yaml compose.yml compose.yaml Dockerfile Dockerfile.prod .env .env.example .env.production .env.prod package.json pnpm-workspace.yaml turbo.json nx.json README.md README Makefile deploy.sh deploy.yml
do
  if [ -e "$f" ]; then echo "EXISTS $f"; fi
done
if [ -d .github/workflows ]; then echo "EXISTS .github/workflows"; fi

echo
echo "===== Q3 DEPLOY IDENTITY ====="
find . -type f | grep -vi node_modules | grep -vi '/.git/' | grep -iE 'deploy|release|workflow|r75|r76|p0_03_r5' | head -n 80
echo
if [ -d .github/workflows ]; then
  echo "GITHUB_WORKFLOWS=present"
  ls -la .github/workflows
  echo "WORKFLOW_COUNT=$(ls .github/workflows/*.yml .github/workflows/*.yaml 2>/dev/null | wc -l | tr -d ' ')"
else
  echo "GITHUB_WORKFLOWS=absent"
  echo "WORKFLOW_COUNT=0"
fi
if [ -f .gitlab-ci.yml ]; then echo "GITLAB_CI=present"; else echo "GITLAB_CI=absent"; fi

echo
echo "===== Q4 COMPOSE / DOCKER ====="
for c in docker-compose.yml docker-compose.yaml compose.yml compose.yaml compose.prod.yml docker-compose.prod.yml
do
  if [ -f "$c" ]; then
    echo "--- FILE $c ---"
    grep -nE 'image:|ports:|env_file:|environment:|secrets:|container_name:|restart:|0.0.0.0|services:' "$c" | head -n 120 || true
  fi
done
if command -v docker >/dev/null 2>&1; then
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null || echo "DOCKER_PS_UNAVAILABLE"
else
  echo "DOCKER_CLI=absent"
fi

echo
echo "===== Q5 ENV NAMES ONLY ====="
find . -maxdepth 3 -type f | grep -v node_modules | grep '/.env' | while read -r e
do
  count=$(grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' "$e" 2>/dev/null || echo 0)
  keys=$(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$e" 2>/dev/null | cut -d= -f1 | tr '\n' ',')
  echo "ENVFILE=$e KEY_COUNT=$count KEYS=$keys"
done

echo
echo "===== Q6 AUDIT GATES ====="
find . -type f | grep -v node_modules | grep -v '/.git/' | grep -iE 'p0_03|phase_p0|r75|r76|audit_final_map' | head -n 100
echo
find . -type f | grep -v node_modules | grep -v '/.git/' | grep -iE 'p0_03|phase_p0|r75|r76|audit_final_map' | while read -r f
do
  hits=$(grep -E 'RESULT=|VERDICT=|WORKFLOW_COUNT=' "$f" 2>/dev/null | head -n 8 || true)
  if [ -n "$hits" ]; then
    echo "FILE $f"
    echo "$hits"
    echo
  fi
done

echo
echo "===== Q7 PACKAGE.JSON ====="
if [ -f apps/web/package.json ]; then
  echo "FOUND apps/web/package.json"
  grep -E '"name"|"scripts"' -A 20 apps/web/package.json | head -n 40
else
  echo "apps/web/package.json=absent"
  find . -maxdepth 3 -name package.json | grep -v node_modules
fi

echo
echo "===== END ====="
} > "$OUT"

echo "WROTE $OUT"
wc -c "$OUT"
