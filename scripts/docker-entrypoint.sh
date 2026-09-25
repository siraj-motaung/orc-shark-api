#!/usr/bin/env sh

set -eu

python3 -m alembic upgrade head
python3 -m scripts.create_admin

exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
