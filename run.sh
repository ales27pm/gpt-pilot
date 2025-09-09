#!/usr/bin/env bash
set -euo pipefail

# Run GPT Pilot using the configured Python environment
if [ -d venv ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

python3 main.py "$@"
