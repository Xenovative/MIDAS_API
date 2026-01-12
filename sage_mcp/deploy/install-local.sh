#!/bin/bash
# Sage MCP - Local Install Script
# Run this directly on the VPS where files already exist
# Usage: ./deploy/install-local.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  Sage MCP - Local Install${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# Find the project root (parent of deploy directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
    sudo apt-get install -y nodejs
fi
echo -e "${GREEN}Node.js $(node -v) ready${NC}"

# Install dependencies
echo ""
echo -e "${YELLOW}Installing npm dependencies...${NC}"
npm install

# Build
echo ""
echo -e "${YELLOW}Building TypeScript...${NC}"
npm run build

# Seed database if needed
if [ ! -f "$PROJECT_DIR/data/sage.db" ]; then
    echo ""
    echo -e "${YELLOW}Seeding database...${NC}"
    npm run seed
fi

# Create systemd service
echo ""
echo -e "${YELLOW}Setting up systemd service...${NC}"

sudo tee /etc/systemd/system/sage-mcp.service > /dev/null << EOF
[Unit]
Description=Sage MCP Academic Research Server
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$PROJECT_DIR
Environment=NODE_ENV=production
Environment=SAGE_DB_PATH=$PROJECT_DIR/data/sage.db
ExecStart=/usr/bin/node $PROJECT_DIR/dist/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sage-mcp

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sage-mcp
sudo systemctl restart sage-mcp

sleep 2

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
sudo systemctl status sage-mcp --no-pager || true
echo ""
echo "Commands:"
echo "  Status:  sudo systemctl status sage-mcp"
echo "  Logs:    sudo journalctl -u sage-mcp -f"
echo "  Restart: sudo systemctl restart sage-mcp"
echo ""
echo "To connect Claude Desktop via SSH:"
echo "{
  \"mcpServers\": {
    \"sage\": {
      \"command\": \"ssh\",
      \"args\": [\"root@YOUR_VPS_IP\", \"node $PROJECT_DIR/dist/index.js\"]
    }
  }
}"
