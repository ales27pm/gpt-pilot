#!/usr/bin/env bash
set -euo pipefail

# Run GPT Pilot using the configured Python environment
# and start the frontend if available.

cleanup() {
  if [[ -n "${FRONTEND_PID:-}" ]]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [ -d venv ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

start_frontend() {
  (
    cd frontend
    if ! command -v npm >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1; then
      echo "Node.js and npm are required for the frontend. Skipping frontend."
      return
    fi
    NODE_VERSION=$(node -v | sed 's/v//')
    NODE_MAJOR=${NODE_VERSION%%.*}
    if [ "$NODE_MAJOR" -lt 18 ]; then
      echo "Node.js 18+ is required for the frontend (found $NODE_VERSION). Skipping frontend."
      return
    fi
    if [ ! -d node_modules ]; then
      if [ -f package-lock.json ]; then
        npm ci
      else
        npm install
      fi
    fi
    npm run dev
  ) &
  FRONTEND_PID=$!
  echo "Frontend started (PID $FRONTEND_PID)"
}

if [ -d frontend ] && [ -f frontend/package.json ]; then
  start_frontend
else
  echo "No frontend found. Starting backend only."
fi

python3 main.py "$@"
