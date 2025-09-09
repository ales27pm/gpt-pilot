#!/bin/bash

if [ -z "$SSH_KEY_B64" ]; then
  echo "Environment variable SSH_KEY_B64 is not set. Exiting."
  exit 1
fi

echo "$SSH_KEY_B64" | base64 -d >> /home/devuser/.ssh/authorized_keys
chmod 600 /home/devuser/.ssh/authorized_keys

export MONGO_DB_DATA=$PYTHAGORA_DATA_DIR/mongodata
mkdir -p $MONGO_DB_DATA

mongod --dbpath "$MONGO_DB_DATA" --bind_ip_all >> $MONGO_DB_DATA/mongo_logs.txt 2>&1 &

export DB_DIR=$PYTHAGORA_DATA_DIR/database

chown -R devuser: $PYTHAGORA_DATA_DIR
su - devuser -c "mkdir -p $DB_DIR"

set -e

REQ_FILE="$(dirname "$0")/requirements.txt"
if [ -f "$REQ_FILE" ]; then
  if ! python3 -m pip install --no-cache-dir -r "$REQ_FILE"; then
    echo "Warning: pip install failed; continuing startup" >&2
  fi
else
  echo "Info: requirements.txt not found at $REQ_FILE; skipping dependency installation"
fi

LOG_DIR="/var/log/init"
mkdir -p "$LOG_DIR"
chmod 750 "$LOG_DIR"
: > "$LOG_DIR/on-event-extension-install.log"
chmod 640 "$LOG_DIR/on-event-extension-install.log"
nohup su - devuser -c 'cd /var/init_data/ && ./on-event-extension-install.sh' >>"$LOG_DIR/on-event-extension-install.log" 2>&1 &

echo "Starting ssh server..."

/usr/sbin/sshd -D
