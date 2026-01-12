# Sage MCP - Full Deployment Script (Windows)
# This script does EVERYTHING: sets up VPS, copies files, builds, and starts service
# Usage: .\deploy\deploy.ps1 -VpsHost "user@your-vps.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    
    [string]$VpsPath = "~/sage-mcp",
    [string]$SshKey = "",
    [switch]$SkipDatabase,
    [switch]$SetupOnly,
    [switch]$SyncOnly
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Sage MCP - Full Deployment" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get local path
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LocalPath = Split-Path -Parent $ScriptDir

Write-Host "Local path:  $LocalPath"
Write-Host "VPS target:  ${VpsHost}:${VpsPath}"
Write-Host ""

# Build SSH args
$SshArgs = @("-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes")
if ($SshKey) {
    $SshArgs = @("-i", $SshKey) + $SshArgs
}

# Test SSH connection
Write-Host "Testing SSH connection..." -ForegroundColor Yellow
try {
    $null = ssh @SshArgs $VpsHost "echo ok" 2>&1
    Write-Host "SSH connection OK" -ForegroundColor Green
} catch {
    Write-Host "SSH connection failed. Check your credentials." -ForegroundColor Red
    exit 1
}

# ============================================
# STEP 1: VPS Setup (install Node.js, create user, etc.)
# ============================================
if (-not $SyncOnly) {
    Write-Host ""
    Write-Host "Step 1: Setting up VPS environment..." -ForegroundColor Cyan
    
    $SetupScript = @'
set -e

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
    echo "Need sudo access"
    exit 1
fi

SUDO=""
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
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

# Create sage user if doesn't exist
if ! id "sage" &>/dev/null; then
    echo "[INFO] Creating sage user..."
    $SUDO useradd -r -m -s /bin/bash sage
else
    echo "[INFO] User sage exists"
fi

# Create directories
echo "[INFO] Creating directories..."
mkdir -p ~/sage-mcp/src
mkdir -p ~/sage-mcp/data

echo "[INFO] VPS environment ready"
'@
    
    Write-Host $SetupScript | ssh @SshArgs $VpsHost "bash -s"
    
    if ($SetupOnly) {
        Write-Host ""
        Write-Host "Setup complete. Run without -SetupOnly to deploy files." -ForegroundColor Green
        exit 0
    }
}

# ============================================
# STEP 2: Copy files to VPS
# ============================================
Write-Host ""
Write-Host "Step 2: Copying files to VPS..." -ForegroundColor Cyan

# Check for rsync
$RsyncCmd = $null
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    $RsyncCmd = "rsync"
} elseif (Test-Path "C:\Program Files\Git\usr\bin\rsync.exe") {
    $RsyncCmd = "C:\Program Files\Git\usr\bin\rsync.exe"
}

# Build exclude list
$Excludes = @(
    "node_modules",
    ".git",
    "*.log",
    ".env",
    ".env.local"
)
if ($SkipDatabase) {
    $Excludes += "data/sage.db"
    $Excludes += "data/sage.db-journal"
    $Excludes += "data/sage.db-wal"
}

if ($RsyncCmd) {
    Write-Host "Using rsync for file transfer..."
    $RsyncExcludes = $Excludes | ForEach-Object { "--exclude=$_" }
    $RsyncArgs = @("-avz", "--progress") + $RsyncExcludes
    
    $SshCmd = "ssh"
    if ($SshKey) {
        $SshCmd = "ssh -i $SshKey"
    }
    $RsyncArgs += "-e", "$SshCmd -o StrictHostKeyChecking=no"
    $RsyncArgs += "$LocalPath/", "${VpsHost}:${VpsPath}/src/"
    
    & $RsyncCmd @RsyncArgs
} else {
    Write-Host "Using tar+scp for file transfer (rsync not found)..."
    
    # Create temp archive
    $TempFile = [System.IO.Path]::GetTempFileName()
    $TempTar = "$TempFile.tar.gz"
    
    # Build tar exclude args
    $TarExcludes = $Excludes | ForEach-Object { "--exclude=$_" }
    
    Push-Location $LocalPath
    Write-Host "Creating archive..."
    tar -czf $TempTar @TarExcludes .
    Pop-Location
    
    Write-Host "Uploading archive..."
    $ScpArgs = @("-o", "StrictHostKeyChecking=no")
    if ($SshKey) { $ScpArgs = @("-i", $SshKey) + $ScpArgs }
    $ScpArgs += $TempTar, "${VpsHost}:/tmp/sage-mcp.tar.gz"
    scp @ScpArgs
    
    Write-Host "Extracting on VPS..."
    ssh @SshArgs $VpsHost "cd ${VpsPath}/src && tar -xzf /tmp/sage-mcp.tar.gz && rm /tmp/sage-mcp.tar.gz"
    
    Remove-Item $TempFile -ErrorAction SilentlyContinue
    Remove-Item $TempTar -ErrorAction SilentlyContinue
}

# Copy database separately if exists and not skipped
if (-not $SkipDatabase) {
    $DbPath = Join-Path $LocalPath "data\sage.db"
    if (Test-Path $DbPath) {
        Write-Host "Copying database..."
        $ScpArgs = @("-o", "StrictHostKeyChecking=no")
        if ($SshKey) { $ScpArgs = @("-i", $SshKey) + $ScpArgs }
        $ScpArgs += $DbPath, "${VpsHost}:${VpsPath}/data/"
        scp @ScpArgs
        Write-Host "Database copied" -ForegroundColor Green
    } else {
        Write-Host "No local database found - will seed on VPS" -ForegroundColor Yellow
    }
}

Write-Host "Files copied" -ForegroundColor Green

# ============================================
# STEP 3: Build on VPS
# ============================================
Write-Host ""
Write-Host "Step 3: Building on VPS..." -ForegroundColor Cyan

$BuildScript = @"
set -e
cd ${VpsPath}/src

echo "[INFO] Installing npm dependencies..."
npm install --production=false 2>&1 | tail -5

echo "[INFO] Building TypeScript..."
npm run build 2>&1 | tail -3

# Seed database if it doesn't exist
if [ ! -f "${VpsPath}/data/sage.db" ]; then
    echo "[INFO] Seeding database..."
    SAGE_DB_PATH="${VpsPath}/data/sage.db" npm run seed 2>&1 | tail -5
fi

echo "[INFO] Build complete"
"@

ssh @SshArgs $VpsHost $BuildScript

# ============================================
# STEP 4: Setup and start systemd service
# ============================================
Write-Host ""
Write-Host "Step 4: Setting up systemd service..." -ForegroundColor Cyan

$ServiceScript = @"
set -e

SUDO=""
if [ "`$EUID" -ne 0 ]; then
    SUDO="sudo"
fi

# Get actual home path (expand ~)
SAGE_HOME=`$(eval echo ${VpsPath})

# Create systemd service file
`$SUDO tee /etc/systemd/system/sage-mcp.service > /dev/null << SERVICEEOF
[Unit]
Description=Sage MCP Academic Research Server
After=network.target

[Service]
Type=simple
User=`$USER
Group=`$USER
WorkingDirectory=`$SAGE_HOME/src
Environment=NODE_ENV=production
Environment=SAGE_DB_PATH=`$SAGE_HOME/data/sage.db
ExecStart=/usr/bin/node `$SAGE_HOME/src/dist/index.js
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sage-mcp

[Install]
WantedBy=multi-user.target
SERVICEEOF

`$SUDO systemctl daemon-reload
`$SUDO systemctl enable sage-mcp
`$SUDO systemctl restart sage-mcp

sleep 2
`$SUDO systemctl status sage-mcp --no-pager || true
"@

ssh @SshArgs $VpsHost $ServiceScript

# ============================================
# Done!
# ============================================
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service is running at: $VpsHost"
Write-Host ""
Write-Host "Commands:"
Write-Host "  Status:  ssh $VpsHost 'sudo systemctl status sage-mcp'"
Write-Host "  Logs:    ssh $VpsHost 'sudo journalctl -u sage-mcp -f'"
Write-Host "  Restart: ssh $VpsHost 'sudo systemctl restart sage-mcp'"
Write-Host ""
Write-Host "To connect Claude Desktop via SSH, add to config:"
Write-Host @"
{
  "mcpServers": {
    "sage": {
      "command": "ssh",
      "args": ["$VpsHost", "node ${VpsPath}/src/dist/index.js"]
    }
  }
}
"@
