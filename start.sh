#!/bin/bash
# ─────────────────────────────────────────────────────────────
# OpenJustice Backend — Container Startup Script
#
# 1. Run Alembic migrations to ensure schema is up-to-date
#    before the server accepts traffic.
# 2. Start Uvicorn with production settings.
# ─────────────────────────────────────────────────────────────
set -e

echo "==> Running database migrations..."
alembic upgrade head

echo "==> Starting application server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --access-log
