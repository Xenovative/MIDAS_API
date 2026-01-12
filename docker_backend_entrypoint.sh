#!/usr/bin/env bash
set -euo pipefail

# Ensure uploads directory exists with proper permissions
mkdir -p /app/backend/static/uploads
chmod 755 /app/backend/static/uploads

RUN_INIT_DB=${RUN_INIT_DB:-true}
CREATE_DEFAULT_ADMIN=${CREATE_DEFAULT_ADMIN:-true}

if [[ "${RUN_INIT_DB}" == "true" ]]; then
  echo "[bootstrap] Running init_db.py (this will recreate tables)."
  python3 init_db.py
else
  echo "[bootstrap] Skipping init_db.py (RUN_INIT_DB=${RUN_INIT_DB})."
fi

if [[ "${CREATE_DEFAULT_ADMIN}" == "true" ]]; then
  echo "[bootstrap] Running create_admin.py (will no-op if admin exists)."
  python3 create_admin.py || true
else
  echo "[bootstrap] Skipping create_admin.py (CREATE_DEFAULT_ADMIN=${CREATE_DEFAULT_ADMIN})."
fi

# Handle SageMCP Database persistence
# The database was pre-populated during build at /app/backend/sage_mcp/data/sage.db
# We need to copy it to /data/sage.db (mounted volume) if it doesn't exist there yet
TARGET_DB="/data/sage.db"
SOURCE_DB="/app/backend/sage_mcp/data/sage.db"

if [ ! -f "$TARGET_DB" ]; then
  echo "[bootstrap] Initializing SageMCP database from image..."
  if [ -f "$SOURCE_DB" ]; then
    # Ensure directory exists
    mkdir -p $(dirname "$TARGET_DB")
    cp "$SOURCE_DB" "$TARGET_DB"
    echo "[bootstrap] Database initialized successfully."
  else
    echo "[bootstrap] WARNING: Source database not found at $SOURCE_DB. SageMCP may start with empty DB."
  fi
else
  echo "[bootstrap] SageMCP database found at $TARGET_DB."
fi

exec "$@"
