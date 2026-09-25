#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

cd "$PROJECT_ROOT"

echo "==> Setting up virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "==> Virtual environment created."
else
    echo "==> Virtual environment already exists."
fi

PYTHON="$VENV_DIR/bin/python"

echo "==> Upgrading pip..."

"$PYTHON" -m pip install --upgrade pip

echo "==> Installing dependencies..."

"$PYTHON" -m pip install -r requirements.txt

echo "==> Installation complete."

echo
echo "To activate the virtual environment manually:"
echo "source venv/bin/activate"
