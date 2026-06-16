#!/usr/bin/env bash
# Deploy entrypoint: migrate the schema, then serve.
# LEDGER relies on alembic (no create_all on startup), so the schema must be
# upgraded before uvicorn accepts traffic. alembic/env.py reads DATABASE_URL.
set -euo pipefail

echo "[ledger] alembic upgrade head"
alembic upgrade head

echo "[ledger] starting uvicorn on 0.0.0.0:${PORT:-8765}"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8765}"
