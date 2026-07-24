#!/bin/sh
set -e

echo "[ResolveHub] Running database migrations (alembic upgrade head)..."
alembic upgrade head

echo "[ResolveHub] Database migrations complete! Starting server..."
exec uvicorn resolvehub.app.main:app --host 0.0.0.0 --port 8000
