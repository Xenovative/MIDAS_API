#!/usr/bin/env bash

set -euo pipefail

APP_DIR="/var/www/midas"
SERVICE_NAME="midas"
SERVICE_USER="www-data"
DOMAIN="example.com"
ADDITIONAL_DOMAINS=""
BACKEND_PORT=8000
WORKERS=2
SOURCE_DIR="$(pwd)"
SKIP_SYSTEMD=0
SKIP_NGINX=1
ASSUME_YES=0

usage() {
  cat <<'EOF'
Usage: sudo ./deploy.sh [options]

Options:
  --app-dir PATH        Target directory on the server (default: /var/www/midas)
  --service-name NAME   Systemd service name (default: midas)
  --service-user USER   Linux user to run the app (default: www-data)
  --domain NAME         Public domain for Nginx server_name (default: example.com)
  --backend-port PORT   Internal backend port (default: 8000)
  --workers N           Uvicorn worker count (default: 2)
  --source PATH         Source repo to deploy (default: current directory)
  --skip-systemd        Only sync/build without touching systemd
  --skip-nginx          Explicitly skip Nginx configuration (default)
  --configure-nginx     Enable Nginx configuration
  --yes                 Assume "yes" for prompts
  -h, --help            Show this help
EOF
}

prompt_domains_and_ports() {
  if [[ $ASSUME_YES -eq 1 ]]; then
    return
  fi

  read -r -p "Primary domain (for server_name) [${DOMAIN}]: " input
  if [[ -n ${input} ]]; then
    DOMAIN=${input}
  fi

  read -r -p "Additional domains (space separated, optional): " input
  if [[ -n ${input} ]]; then
    ADDITIONAL_DOMAINS=${input}
  fi

  read -r -p "Backend port [${BACKEND_PORT}]: " input
  if [[ -n ${input} ]]; then
    BACKEND_PORT=${input}
  fi
}

log() {
  echo -e "\033[1;34m[+]\033[0m $*"
}

require_root() {
  if [[ $EUID -ne 0 ]]; then
    echo "Run this script as root (sudo)."
    exit 1
  fi
}

confirm() {
  local prompt=$1
  if [[ $ASSUME_YES -eq 1 ]]; then
    return 0
  fi
  read -r -p "$prompt [y/N]: " response
  [[ $response =~ ^[Yy]$ ]]
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --app-dir)
        APP_DIR="$2"; shift 2 ;;
      --service-name)
        SERVICE_NAME="$2"; shift 2 ;;
      --service-user)
        SERVICE_USER="$2"; shift 2 ;;
      --domain)
        DOMAIN="$2"; shift 2 ;;
      --backend-port)
        BACKEND_PORT="$2"; shift 2 ;;
      --workers)
        WORKERS="$2"; shift 2 ;;
      --source)
        SOURCE_DIR="$2"; shift 2 ;;
      --skip-systemd)
        SKIP_SYSTEMD=1; shift ;;
      --skip-nginx)
        SKIP_NGINX=1; shift ;;
      --configure-nginx)
        SKIP_NGINX=0; shift ;;
      --yes)
        ASSUME_YES=1; shift ;;
      -h|--help)
        usage; exit 0 ;;
      *)
        echo "Unknown option: $1"; usage; exit 1 ;;
    esac
  done
}

install_dependencies() {
  log "Installing OS packages..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y python3 python3-venv python3-pip nodejs npm nginx git curl rsync

  if command -v node >/dev/null 2>&1; then
    local major
    major=$(node -v | sed 's/^v//' | cut -d. -f1)
    if (( major < 18 )); then
      log "Upgrading Node.js to 18.x"
      curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
      apt-get install -y nodejs
    fi
  else
    log "Installing Node.js 18.x"
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
  fi
}

sync_source() {
  log "Syncing source to $APP_DIR"
  mkdir -p "$APP_DIR"
  rsync -a --delete --exclude ".git" --exclude "venv" "$SOURCE_DIR/" "$APP_DIR/"
}

setup_python() {
  log "Setting up Python virtual environment"
  python3 -m venv "$APP_DIR/venv" >/dev/null 2>&1 || true
  # shellcheck disable=SC1091
  source "$APP_DIR/venv/bin/activate"
  pip install --upgrade pip wheel
  pip install -r "$APP_DIR/requirements.txt"
  if [[ ! -f "$APP_DIR/.env" && -f "$APP_DIR/.env.example" ]]; then
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    log "Copied .env.example -> .env. Update secrets before going live."
  fi
  deactivate
}

build_frontend() {
  log "Installing frontend dependencies and building"
  pushd "$APP_DIR/frontend" >/dev/null
  if [[ -f package-lock.json ]]; then
    npm ci --no-progress
  else
    npm install --no-progress
  fi
  npm run build
  popd >/dev/null
}

configure_systemd() {
  if [[ $SKIP_SYSTEMD -eq 1 ]]; then
    return
  fi

  log "Writing systemd unit /etc/systemd/system/${SERVICE_NAME}.service"
  cat <<EOF >/etc/systemd/system/${SERVICE_NAME}.service
[Unit]
Description=MIDAS API (${SERVICE_NAME})
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=-${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port ${BACKEND_PORT} --workers ${WORKERS}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable --now "${SERVICE_NAME}.service"
  systemctl status "${SERVICE_NAME}.service" --no-pager
}

configure_nginx() {
  if [[ $SKIP_NGINX -eq 1 ]]; then
    return
  fi

  local SERVER_NAMES=${DOMAIN}
  if [[ -n ${ADDITIONAL_DOMAINS} ]]; then
    SERVER_NAMES="${SERVER_NAMES} ${ADDITIONAL_DOMAINS}"
  fi

  log "Configuring Nginx vhost /etc/nginx/sites-available/${SERVICE_NAME}.conf"
  cat <<EOF >/etc/nginx/sites-available/${SERVICE_NAME}.conf
server {
    listen 80;
    server_name ${SERVER_NAMES};

    root ${APP_DIR}/frontend/dist;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:${BACKEND_PORT}/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
}
EOF

  ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}.conf" \
    "/etc/nginx/sites-enabled/${SERVICE_NAME}.conf"
  nginx -t
  systemctl reload nginx
}

summary() {
  cat <<EOF

Deployment complete.
- App directory: ${APP_DIR}
- Systemd unit: ${SERVICE_NAME}.service (skip with --skip-systemd)
- Nginx config: /etc/nginx/sites-available/${SERVICE_NAME}.conf (skip with --skip-nginx)

Remember to edit ${APP_DIR}/.env with real API keys and restart the service:
  sudo systemctl restart ${SERVICE_NAME}

Point your DNS A record at this server so ${DOMAIN} resolves correctly.
EOF
}

main() {
  parse_args "$@"
  prompt_domains_and_ports
  require_root
  install_dependencies
  sync_source
  setup_python
  build_frontend
  configure_systemd
  configure_nginx
  summary
}

main "$@"
