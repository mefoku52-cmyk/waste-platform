#!/data/data/com.termux/files/usr/bin/bash
set -eu

export PGPASSWORD='recyclehub'

psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U recyclehub \
  -d postgres \
  -v ON_ERROR_STOP=1 \
  -c "CREATE DATABASE recyclehub OWNER recyclehub;" 2>&1 || {
    echo "Database may already exist; continuing"
}

pg_isready -h 127.0.0.1 -p 5432
psql \
  -h 127.0.0.1 \
  -p 5432 \
  -U recyclehub \
  -d recyclehub \
  -c 'select current_database(), current_user;'
