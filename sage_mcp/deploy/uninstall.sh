#!/bin/bash
# Sage MCP - Uninstall Script
# Run on VPS: ./uninstall.sh
# Or remotely: ssh user@vps 'bash -s' < deploy/uninstall.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

APP_NAME="sage-mcp"
APP_DIR="$HOME/sage-mcp"
APP_USER="sage"

echo -e "${CYAN}==========================================${NC}"
echo -e "${CYAN}  Sage MCP - Uninstall${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# Check sudo
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if sudo -n true 2>/dev/null; then
        SUDO="sudo"
    else
        echo -e "${RED}Need sudo access${NC}"
        exit 1
    fi
fi

# Confirm
echo -e "${YELLOW}This will remove:${NC}"
echo "  - Systemd service: ${APP_NAME}.service"
echo "  - Application directory: ${APP_DIR}"
echo "  - User: ${APP_USER} (optional)"
echo ""

if [ "${FORCE:-false}" != "true" ]; then
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
fi

# Stop and disable service
echo ""
echo -e "${YELLOW}Stopping service...${NC}"
$SUDO systemctl stop ${APP_NAME} 2>/dev/null || true
$SUDO systemctl disable ${APP_NAME} 2>/dev/null || true

# Remove service file
echo -e "${YELLOW}Removing systemd service...${NC}"
$SUDO rm -f /etc/systemd/system/${APP_NAME}.service
$SUDO rm -f /etc/systemd/system/${APP_NAME}@.service
$SUDO systemctl daemon-reload

# Backup database before removal (optional)
if [ -f "${APP_DIR}/data/sage.db" ]; then
    BACKUP_PATH="/tmp/sage-mcp-backup-$(date +%Y%m%d-%H%M%S).db"
    echo -e "${YELLOW}Backing up database to ${BACKUP_PATH}...${NC}"
    cp "${APP_DIR}/data/sage.db" "$BACKUP_PATH"
    echo -e "${GREEN}Database backed up${NC}"
fi

# Remove application directory
echo -e "${YELLOW}Removing application directory...${NC}"
$SUDO rm -rf "${APP_DIR}"

# Remove user (optional)
if [ "${REMOVE_USER:-false}" = "true" ]; then
    if id "$APP_USER" &>/dev/null; then
        echo -e "${YELLOW}Removing user ${APP_USER}...${NC}"
        $SUDO userdel -r "$APP_USER" 2>/dev/null || $SUDO userdel "$APP_USER"
    fi
else
    echo -e "${YELLOW}User '${APP_USER}' kept. Set REMOVE_USER=true to remove.${NC}"
fi

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}  Uninstall Complete${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
if [ -n "$BACKUP_PATH" ] && [ -f "$BACKUP_PATH" ]; then
    echo "Database backup saved to: $BACKUP_PATH"
fi
echo ""
echo "To fully clean up, you may also want to:"
echo "  - Remove Node.js: sudo apt remove nodejs"
echo "  - Remove the backup: rm $BACKUP_PATH"
