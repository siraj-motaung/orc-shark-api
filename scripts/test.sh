#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
TEST_DB_CONTAINER="orc_shack_test_db"

cd "$PROJECT_ROOT"

echo "==> Setting up virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

echo "==> Installing dependencies..."
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install -r requirements.txt

echo "==> Starting PostgreSQL test database..."

if docker ps --format '{{.Names}}' | grep -q "^${TEST_DB_CONTAINER}$"; then
    echo "PostgreSQL test container is already running."
elif docker ps -a --format '{{.Names}}' | grep -q "^${TEST_DB_CONTAINER}$"; then
    docker start "$TEST_DB_CONTAINER"
else
    docker run \
        --name "$TEST_DB_CONTAINER" \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=orc_shack_test \
        -p 5433:5432 \
        -d postgres:16-alpine
fi

echo "==> Waiting for PostgreSQL..."

until docker exec "$TEST_DB_CONTAINER" pg_isready \
    -U postgres \
    -d orc_shack_test \
    >/dev/null 2>&1
do
    sleep 1
done

echo "PostgreSQL is ready."

echo "==> Running tests..."

# Ensure application-level database checks use the dedicated test database.
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5433/orc_shack_test"

"$PYTHON" -m pytest -vv --tb=short

echo "==> All tests passed."
