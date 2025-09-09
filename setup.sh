#!/usr/bin/env bash
set -euo pipefail

# Interactive setup script for GPT Pilot

# check for Python 3.9+
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required but not installed. Please install Python 3.9 or newer."
  exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
if ! python3 - <<'PY'
import sys
major, minor = sys.version_info[:2]
if major < 3 or (major == 3 and minor < 9):
    sys.exit(1)
PY
then
  echo "Python 3.9+ is required (found $PYTHON_VERSION)."
  exit 1
fi

# optionally create virtual environment
read -r -p "Create a Python virtual environment? (y/N): " create_venv
if [[ "$create_venv" =~ ^[Yy]$ ]]; then
  python3 -m venv venv
  source venv/bin/activate
fi

# install dependencies
if [ -f requirements.txt ]; then
  echo "Installing Python dependencies..."
  python3 -m pip install -r requirements.txt
fi

# configure config.json
if [ ! -f config.json ]; then
  cp example-config.json config.json
  echo "Created config.json from example-config.json"
fi

read -r -p "LLM provider (openai/anthropic/groq) [openai]: " provider
provider=${provider:-openai}
read -r -p "API key for $provider: " api_key
read -r -p "Base URL for $provider (leave blank for default): " base_url

python3 <<PY
import json, re
file="config.json"
with open(file) as f:
    content = re.sub(r'^\s*//.*$', '', f.read(), flags=re.MULTILINE)
cfg = json.loads(content)

if "llm" not in cfg:
    cfg["llm"]={}
if "${provider}" not in cfg["llm"]:
    cfg["llm"]["${provider}"]={"base_url": None, "api_key": None, "connect_timeout":60.0, "read_timeout":20.0}

cfg["llm"]["${provider}"]["api_key"]="${api_key}"
if "${base_url}" != "":
    cfg["llm"]["${provider}"]["base_url"]="${base_url}"

if "agent" not in cfg:
    cfg["agent"]={}
if "default" not in cfg["agent"]:
    cfg["agent"]["default"]={}
cfg["agent"]["default"]["provider"]="${provider}"

with open(file, 'w') as f:
    json.dump(cfg, f, indent=2)
PY

echo "Setup complete. You can run GPT Pilot using ./run.sh"
