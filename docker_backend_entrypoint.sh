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

# Build SageMCP if dist doesn't exist (volume mount overwrites Docker build)
SAGE_MCP_DIR="/app/backend/sage_mcp"
if [ -d "$SAGE_MCP_DIR" ] && [ -f "$SAGE_MCP_DIR/package.json" ]; then
  if [ ! -d "$SAGE_MCP_DIR/dist" ]; then
    echo "[bootstrap] Building SageMCP (dist not found)..."
    cd "$SAGE_MCP_DIR"
    npm install --silent
    npm run build
    cd /app
    echo "[bootstrap] SageMCP built successfully."
  else
    echo "[bootstrap] SageMCP dist already exists."
  fi
fi

# Handle SageMCP Database persistence
TARGET_DB="/data/sage.db"
SOURCE_XML="$SAGE_MCP_DIR/data/papers_database.xml"

if [ ! -f "$TARGET_DB" ]; then
  echo "[bootstrap] Initializing SageMCP database..."
  if [ -f "$SOURCE_XML" ] && [ -d "$SAGE_MCP_DIR/dist" ]; then
    cd "$SAGE_MCP_DIR"
    SAGE_DB_PATH="$TARGET_DB" npm run import-xml
    cd /app
    echo "[bootstrap] SageMCP database initialized successfully."
  else
    echo "[bootstrap] WARNING: Cannot initialize SageMCP database. XML or dist not found."
  fi
else
  echo "[bootstrap] SageMCP database found at $TARGET_DB."
fi

exec "$@"
