#!/bin/bash
set -e

# Sage MCP VPS Deployment Script
# Tested on: Ubuntu 22.04 LTS, Debian 12
# Usage: curl -sSL https://your-server/setup-vps.sh | bash
#    or: ./setup-vps.sh

echo "=========================================="
echo "  Sage MCP - VPS Deployment Script"
echo "=========================================="

# Configuration
APP_NAME="sage-mcp"
APP_USER="sage"
APP_DIR="$HOME/sage-mcp"
NODE_VERSION="20"
REPO_URL="${SAGE_REPO_URL:-}"  # Set this or copy files manually

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root (sudo ./setup-vps.sh)"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    log_error "Cannot detect OS"
    exit 1
fi

log_info "Detected OS: $OS $VERSION"

# Install Node.js
install_nodejs() {
    log_info "Installing Node.js $NODE_VERSION..."
    
    if command -v node &> /dev/null; then
        CURRENT_NODE=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$CURRENT_NODE" -ge "$NODE_VERSION" ]; then
            log_info "Node.js $(node -v) already installed"
            return
        fi
    fi

    # Install via NodeSource
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
    apt-get install -y nodejs

    log_info "Node.js $(node -v) installed"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    apt-get update
    apt-get install -y \
        build-essential \
        python3 \
        git \
        curl \
        wget
}

# Create application user
create_user() {
    if id "$APP_USER" &>/dev/null; then
        log_info "User $APP_USER already exists"
    else
        log_info "Creating user $APP_USER..."
        useradd -r -m -s /bin/bash "$APP_USER"
    fi
}

# Setup application directory
setup_app() {
    log_info "Setting up application directory..."
    
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/data"
    
    # If repo URL provided, clone it
    if [ -n "$REPO_URL" ]; then
        log_info "Cloning from $REPO_URL..."
        git clone "$REPO_URL" "$APP_DIR/src"
    else
        log_warn "No SAGE_REPO_URL set. Please copy files to $APP_DIR manually."
        log_warn "Expected structure:"
        log_warn "  $APP_DIR/src/          - Source code"
        log_warn "  $APP_DIR/data/sage.db  - Database file"
    fi
    
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
}

# Install npm dependencies and build
build_app() {
    if [ ! -d "$APP_DIR/src" ]; then
        log_warn "Source directory not found. Skipping build."
        return
    fi
    
    log_info "Installing npm dependencies..."
    cd "$APP_DIR/src"
    sudo -u "$APP_USER" npm install
    
    log_info "Building application..."
    sudo -u "$APP_USER" npm run build
    
    # Seed database if empty
    if [ ! -f "$APP_DIR/data/sage.db" ]; then
        log_info "Seeding database..."
        sudo -u "$APP_USER" SAGE_DB_PATH="$APP_DIR/data/sage.db" npm run seed
    fi
}

# Create systemd service
create_systemd_service() {
    log_info "Creating systemd service..."
    
    cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Sage MCP Academic Research Server
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR/src
Environment=NODE_ENV=production
Environment=SAGE_DB_PATH=$APP_DIR/data/sage.db
ExecStart=/usr/bin/node $APP_DIR/src/dist/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$APP_DIR/data
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    log_info "Systemd service created: ${APP_NAME}.service"
}

# Create socket activation for MCP (optional - for stdio transport)
create_socket_service() {
    log_info "Creating socket service for stdio transport..."
    
    cat > /etc/systemd/system/${APP_NAME}@.service << 'EOF'
[Unit]
Description=Sage MCP Instance %i

[Service]
Type=simple
User=sage
Group=sage
WorkingDirectory=/opt/sage-mcp/src
Environment=NODE_ENV=production
Environment=SAGE_DB_PATH=/opt/sage-mcp/data/sage.db
ExecStart=/usr/bin/node /opt/sage-mcp/src/dist/index.js
StandardInput=socket
StandardOutput=socket
StandardError=journal
EOF

    systemctl daemon-reload
}

# Print summary and next steps
print_summary() {
    echo ""
    echo "=========================================="
    echo "  Deployment Complete!"
    echo "=========================================="
    echo ""
    echo "Application directory: $APP_DIR"
    echo "Database location:     $APP_DIR/data/sage.db"
    echo "Service name:          ${APP_NAME}.service"
    echo ""
    echo "Commands:"
    echo "  Start:   systemctl start $APP_NAME"
    echo "  Stop:    systemctl stop $APP_NAME"
    echo "  Status:  systemctl status $APP_NAME"
    echo "  Logs:    journalctl -u $APP_NAME -f"
    echo "  Enable:  systemctl enable $APP_NAME"
    echo ""
    
    if [ ! -d "$APP_DIR/src" ]; then
        echo "NEXT STEPS:"
        echo "1. Copy your source files to $APP_DIR/src/"
        echo "2. Copy your database to $APP_DIR/data/sage.db"
        echo "3. Run: cd $APP_DIR/src && npm install && npm run build"
        echo "4. Run: systemctl start $APP_NAME"
        echo ""
    fi
    
    echo "To connect from a remote MCP client, you'll need to:"
    echo "1. Use SSH tunneling, or"
    echo "2. Set up an HTTP/WebSocket transport (see deploy/README.md)"
    echo ""
}

# Main execution
main() {
    install_dependencies
    install_nodejs
    create_user
    setup_app
    build_app
    create_systemd_service
    create_socket_service
    print_summary
}

main "$@"
