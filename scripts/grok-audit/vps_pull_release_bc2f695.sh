#!/usr/bin/env bash
set -eu

export REGISTRY_IMAGE_PREFIX=ghcr.io/mefoku52-cmyk
export IMAGE_TAG=release-bc2f695472636e343506789430a377a9fcc6a3e9

echo "===== RELEASE IDENTITY ====="
echo "REGISTRY_IMAGE_PREFIX=$REGISTRY_IMAGE_PREFIX"
echo "IMAGE_TAG=$IMAGE_TAG"
echo "API=$REGISTRY_IMAGE_PREFIX/cmep-api:$IMAGE_TAG"
echo "WEB=$REGISTRY_IMAGE_PREFIX/cmep-web:$IMAGE_TAG"
echo "WORKER=$REGISTRY_IMAGE_PREFIX/cmep-worker:$IMAGE_TAG"
echo "PWD=$(pwd)"

if [ ! -f docker-compose.yml ] && [ ! -f compose.yml ]; then
  echo "CHYBA: v tomto adresari nie je docker-compose.yml"
  echo "Presun sa na VPS do priečinka s produkčným compose a spusti skript znova."
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "CHYBA: docker tu nie je"
  exit 1
fi

echo "===== PULL ====="
docker compose pull

echo "===== UP ====="
docker compose up -d

echo "===== PS ====="
docker compose ps
