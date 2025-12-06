#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"

cd "$BACKEND_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not installed. Please install it and rerun this script."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
  echo "Missing backend/.env file. Create one before running the server." >&2
  exit 1
fi

exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
