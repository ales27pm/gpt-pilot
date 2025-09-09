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

# Start frontend in background if a frontend project exists
if [ -d frontend ] && [ -f frontend/package.json ]; then
  (
    cd frontend
    if [ ! -d node_modules ]; then
      npm install
    fi
    npm run dev
  ) &
  FRONTEND_PID=$!
  echo "Frontend started (PID $FRONTEND_PID)"
else
  echo "No frontend found. Starting backend only."
fi

python3 main.py "$@"
