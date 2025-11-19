#!/usr/bin/env bash
set -euo pipefail

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

exec "$@"
