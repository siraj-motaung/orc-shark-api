#!/usr/bin/env sh

set -eu

python -m alembic upgrade head
python -m scripts.create_admin

exec python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
