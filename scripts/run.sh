#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

cd "$PROJECT_ROOT"

echo "==> Setting up virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

echo "==> Activating virtual environment..."

source "$VENV_DIR/bin/activate"

echo "==> Installing dependencies..."

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Checking environment configuration..."

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "==> Creating .env from .env.example..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
else
    echo "==> .env already exists, keeping existing configuration."
fi

echo "==> Starting PostgreSQL..."

docker compose up -d postgres

echo "==> Running database migrations..."

python -m alembic upgrade head

echo "==> Creating admin user..."

python -m scripts.create_admin

echo "==> Starting FastAPI..."

python -m uvicorn app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload
