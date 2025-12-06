#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required but not installed. Please install Node.js + npm and rerun this script."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  npm install
fi

exec npm run dev -- --host 0.0.0.0 --port 5173
