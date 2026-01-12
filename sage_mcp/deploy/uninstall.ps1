# Sage MCP - Remote Uninstall Script (Windows)
# Usage: .\deploy\uninstall.ps1 -VpsHost "user@your-vps.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    
    [string]$SshKey = "",
    [switch]$RemoveUser,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Sage MCP - Uninstall" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Build SSH args
$SshArgs = @("-o", "StrictHostKeyChecking=no")
if ($SshKey) {
    $SshArgs = @("-i", $SshKey) + $SshArgs
}

Write-Host "This will remove from ${VpsHost}:" -ForegroundColor Yellow
Write-Host "  - Systemd service: sage-mcp.service"
Write-Host "  - Application directory: ~/sage-mcp"
if ($RemoveUser) {
    Write-Host "  - User: sage"
}
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "Are you sure? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "Cancelled."
        exit 0
    }
}

$RemoveUserFlag = if ($RemoveUser) { "true" } else { "false" }

$UninstallScript = @"
set -e

SUDO=""
if [ "`$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

echo "[INFO] Stopping service..."
`$SUDO systemctl stop sage-mcp 2>/dev/null || true
`$SUDO systemctl disable sage-mcp 2>/dev/null || true

echo "[INFO] Removing systemd service..."
`$SUDO rm -f /etc/systemd/system/sage-mcp.service
`$SUDO rm -f /etc/systemd/system/sage-mcp@.service
`$SUDO systemctl daemon-reload

# Backup database
if [ -f "`$HOME/sage-mcp/data/sage.db" ]; then
    BACKUP="/tmp/sage-mcp-backup-`$(date +%Y%m%d-%H%M%S).db"
    echo "[INFO] Backing up database to `$BACKUP..."
    cp `$HOME/sage-mcp/data/sage.db "`$BACKUP"
fi

echo "[INFO] Removing application directory..."
rm -rf `$HOME/sage-mcp

if [ "$RemoveUserFlag" = "true" ]; then
    if id "sage" &>/dev/null; then
        echo "[INFO] Removing user sage..."
        `$SUDO userdel -r sage 2>/dev/null || `$SUDO userdel sage
    fi
else
    echo "[INFO] User 'sage' kept. Use -RemoveUser to remove."
fi

echo "[INFO] Uninstall complete"
if [ -n "`$BACKUP" ] && [ -f "`$BACKUP" ]; then
    echo "[INFO] Database backup: `$BACKUP"
fi
"@

ssh @SshArgs $VpsHost $UninstallScript

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Uninstall Complete" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
