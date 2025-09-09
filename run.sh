#!/usr/bin/env bash
set -e

# Run GPT Pilot using the configured Python environment
if [ -d venv ]; then
  source venv/bin/activate
fi

python3 main.py "$@"
