#!/bin/bash
# Sage MCP - Full Deployment Script (Linux/macOS)
# This script does EVERYTHING: sets up VPS, copies files, builds, and starts service
# Usage: ./deploy/deploy.sh user@your-vps.com

set -e

# Configuration
VPS_HOST="${1:-}"
VPS_PATH="${2:-~/sage-mcp}"
SSH_KEY="${SSH_KEY:-}"
SKIP_DB="${SKIP_DB:-false}"
SETUP_ONLY="${SETUP_ONLY:-false}"
SYNC_ONLY="${SYNC_ONLY:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ -z "$VPS_HOST" ]; then
    echo -e "${RED}Usage: $0 user@your-vps.com [/opt/sage-mcp]${NC}"
    echo ""
    echo "Environment variables:"
    echo "  SSH_KEY=/path/to/key    - SSH private key"
    echo "  SKIP_DB=true            - Skip database sync"
    echo "  SETUP_ONLY=true         - Only setup VPS, don't deploy"
    echo "  SYNC_ONLY=true          - Only sync files, skip VPS setup"
    exit 1
fi

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  Sage MCP - Full Deployment${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# Get local path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_PATH="$(dirname "$SCRIPT_DIR")"

echo "Local path:  $LOCAL_PATH"
echo "VPS target:  ${VPS_HOST}:${VPS_PATH}"
echo ""

# Build SSH options
SSH_OPTS="-o StrictHostKeyChecking=no -o BatchMode=yes"
if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="-i $SSH_KEY $SSH_OPTS"
fi

# Test SSH connection
echo -e "${YELLOW}Testing SSH connection...${NC}"
if ssh $SSH_OPTS "$VPS_HOST" "echo ok" > /dev/null 2>&1; then
    echo -e "${GREEN}SSH connection OK${NC}"
else
    echo -e "${RED}SSH connection failed. Check your credentials.${NC}"
    exit 1
fi

# ============================================
# STEP 1: VPS Setup
# ============================================
if [ "$SYNC_ONLY" != "true" ]; then
    echo ""
    echo -e "${CYAN}Step 1: Setting up VPS environment...${NC}"
    
    ssh $SSH_OPTS "$VPS_HOST" 'bash -s' << 'SETUPEOF'
set -e

# Check sudo access
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if sudo -n true 2>/dev/null; then
        SUDO="sudo"
    else
        echo "[ERROR] Need sudo access"
        exit 1
    fi
fi

echo "[INFO] Installing system dependencies..."
$SUDO apt-get update -qq
$SUDO apt-get install -y -qq curl build-essential python3 > /dev/null

# Install Node.js if needed
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
    echo "[INFO] Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | $SUDO bash - > /dev/null 2>&1
    $SUDO apt-get install -y -qq nodejs > /dev/null
fi
echo "[INFO] Node.js $(node -v) ready"

# Create directories in home
echo "[INFO] Creating directories..."
mkdir -p ~/sage-mcp/src
mkdir -p ~/sage-mcp/data

echo "[INFO] VPS environment ready"
SETUPEOF

    if [ "$SETUP_ONLY" = "true" ]; then
        echo ""
        echo -e "${GREEN}Setup complete. Run without SETUP_ONLY to deploy files.${NC}"
        exit 0
    fi
fi

# ============================================
# STEP 2: Copy files to VPS
# ============================================
echo ""
echo -e "${CYAN}Step 2: Copying files to VPS...${NC}"

# Build exclude list
EXCLUDES=(
    --exclude='node_modules'
    --exclude='.git'
    --exclude='*.log'
    --exclude='.env'
    --exclude='.env.local'
)

if [ "$SKIP_DB" = "true" ]; then
    EXCLUDES+=(
        --exclude='data/sage.db'
        --exclude='data/sage.db-journal'
        --exclude='data/sage.db-wal'
    )
fi

echo "Using rsync for file transfer..."
rsync -avz --progress \
    "${EXCLUDES[@]}" \
    -e "ssh $SSH_OPTS" \
    "$LOCAL_PATH/" \
    "${VPS_HOST}:${VPS_PATH}/src/"

# Copy database separately if exists and not skipped
if [ "$SKIP_DB" != "true" ]; then
    if [ -f "$LOCAL_PATH/data/sage.db" ]; then
        echo "Copying database..."
        scp $SSH_OPTS "$LOCAL_PATH/data/sage.db" "${VPS_HOST}:${VPS_PATH}/data/"
        echo -e "${GREEN}Database copied${NC}"
    else
        echo -e "${YELLOW}No local database found - will seed on VPS${NC}"
    fi
fi

echo -e "${GREEN}Files copied${NC}"

# ============================================
# STEP 3: Build on VPS
# ============================================
echo ""
echo -e "${CYAN}Step 3: Building on VPS...${NC}"

ssh $SSH_OPTS "$VPS_HOST" "bash -s" << BUILDEOF
set -e
cd ${VPS_PATH}/src

echo "[INFO] Installing npm dependencies..."
npm install --production=false 2>&1 | tail -5

echo "[INFO] Building TypeScript..."
npm run build 2>&1 | tail -3

# Seed database if it doesn't exist
if [ ! -f "${VPS_PATH}/data/sage.db" ]; then
    echo "[INFO] Seeding database..."
    SAGE_DB_PATH="${VPS_PATH}/data/sage.db" npm run seed 2>&1 | tail -5
fi

echo "[INFO] Build complete"
BUILDEOF

# ============================================
# STEP 4: Setup and start systemd service
# ============================================
echo ""
echo -e "${CYAN}Step 4: Setting up systemd service...${NC}"

ssh $SSH_OPTS "$VPS_HOST" "bash -s" << SERVICEEOF
set -e

SUDO=""
if [ "\$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

# Get actual home path (expand ~)
SAGE_HOME=\$(eval echo ${VPS_PATH})

# Create systemd service file
\$SUDO tee /etc/systemd/system/sage-mcp.service > /dev/null << UNITEOF
[Unit]
Description=Sage MCP Academic Research Server
After=network.target

[Service]
Type=simple
User=\$USER
Group=\$USER
WorkingDirectory=\$SAGE_HOME/src
Environment=NODE_ENV=production
Environment=SAGE_DB_PATH=\$SAGE_HOME/data/sage.db
ExecStart=/usr/bin/node \$SAGE_HOME/src/dist/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sage-mcp

[Install]
WantedBy=multi-user.target
UNITEOF

\$SUDO systemctl daemon-reload
\$SUDO systemctl enable sage-mcp
\$SUDO systemctl restart sage-mcp

sleep 2
\$SUDO systemctl status sage-mcp --no-pager || true
SERVICEEOF

# ============================================
# Done!
# ============================================
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "Service is running at: $VPS_HOST"
echo ""
echo "Commands:"
echo "  Status:  ssh $VPS_HOST 'sudo systemctl status sage-mcp'"
echo "  Logs:    ssh $VPS_HOST 'sudo journalctl -u sage-mcp -f'"
echo "  Restart: ssh $VPS_HOST 'sudo systemctl restart sage-mcp'"
echo ""
echo "To connect Claude Desktop via SSH, add to config:"
cat << CONFIGEOF
{
  "mcpServers": {
    "sage": {
      "command": "ssh",
      "args": ["$VPS_HOST", "node ${VPS_PATH}/src/dist/index.js"]
    }
  }
}
CONFIGEOF
