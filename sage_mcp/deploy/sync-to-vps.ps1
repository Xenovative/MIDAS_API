# Sage MCP - Windows PowerShell Sync Script
# Usage: .\deploy\sync-to-vps.ps1 -VpsHost "user@your-vps.com"

param(
    [Parameter(Mandatory=$true)]
    [string]$VpsHost,
    
    [string]$VpsPath = "~/sage-mcp",
    [string]$SshKey = "",
    [switch]$SkipDatabase,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sage MCP - Sync to VPS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$LocalPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $LocalPath) { $LocalPath = "." }

Write-Host "Local path: $LocalPath"
Write-Host "VPS target: ${VpsHost}:${VpsPath}"
Write-Host ""

# Build SSH args
$SshArgs = @()
if ($SshKey) {
    $SshArgs += "-i", $SshKey
}
$SshArgs += "-o", "StrictHostKeyChecking=no"

# Rsync exclude patterns
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

# Build rsync command
$RsyncExcludes = $Excludes | ForEach-Object { "--exclude=$_" }

Write-Host "Syncing source files..." -ForegroundColor Yellow

# Check if rsync is available (Git Bash, WSL, or native)
$RsyncCmd = $null
if (Get-Command rsync -ErrorAction SilentlyContinue) {
    $RsyncCmd = "rsync"
} elseif (Test-Path "C:\Program Files\Git\usr\bin\rsync.exe") {
    $RsyncCmd = "C:\Program Files\Git\usr\bin\rsync.exe"
}

if ($RsyncCmd) {
    # Use rsync
    $RsyncArgs = @("-avz", "--progress") + $RsyncExcludes
    if ($SshKey) {
        $RsyncArgs += "-e", "ssh -i $SshKey -o StrictHostKeyChecking=no"
    }
    $RsyncArgs += "$LocalPath/", "${VpsHost}:${VpsPath}/src/"
    
    & $RsyncCmd @RsyncArgs
} else {
    # Fallback to scp
    Write-Host "rsync not found, using scp (slower)..." -ForegroundColor Yellow
    
    # Create temp archive
    $TempZip = [System.IO.Path]::GetTempFileName() + ".tar.gz"
    
    Write-Host "Creating archive..."
    Push-Location $LocalPath
    tar -czf $TempZip --exclude=node_modules --exclude=.git --exclude="data/*.db*" .
    Pop-Location
    
    Write-Host "Uploading..."
    $ScpArgs = @()
    if ($SshKey) { $ScpArgs += "-i", $SshKey }
    $ScpArgs += $TempZip, "${VpsHost}:/tmp/sage-mcp.tar.gz"
    scp @ScpArgs
    
    Write-Host "Extracting on VPS..."
    $SshCmd = "mkdir -p ${VpsPath}/src && cd ${VpsPath}/src && tar -xzf /tmp/sage-mcp.tar.gz && rm /tmp/sage-mcp.tar.gz"
    ssh @SshArgs $VpsHost $SshCmd
    
    Remove-Item $TempZip -ErrorAction SilentlyContinue
}

# Sync database (default behavior, skip with -SkipDatabase)
if (-not $SkipDatabase) {
    Write-Host ""
    Write-Host "Syncing database..." -ForegroundColor Yellow
    
    # Ensure data directory exists on VPS
    ssh @SshArgs $VpsHost "mkdir -p ${VpsPath}/data"
    
    $DbPath = Join-Path $LocalPath "data\sage.db"
    if (Test-Path $DbPath) {
        $ScpArgs = @()
        if ($SshKey) { $ScpArgs += "-i", $SshKey }
        $ScpArgs += "-o", "StrictHostKeyChecking=no"
        $ScpArgs += $DbPath, "${VpsHost}:${VpsPath}/data/"
        scp @ScpArgs
        Write-Host "Database synced successfully" -ForegroundColor Green
    } else {
        Write-Host "Database not found at $DbPath - will seed on VPS" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "Skipping database sync (-SkipDatabase flag set)" -ForegroundColor Yellow
}

# Install dependencies and build on VPS
Write-Host ""
Write-Host "Installing dependencies and building on VPS..." -ForegroundColor Yellow

$BuildCmd = @"
cd ${VpsPath}/src && 
npm install --production=false && 
npm run build && 
sudo chown -R sage:sage ${VpsPath}
"@

ssh @SshArgs $VpsHost $BuildCmd

# Restart service if requested
if ($Restart) {
    Write-Host ""
    Write-Host "Restarting service..." -ForegroundColor Yellow
    ssh @SshArgs $VpsHost "sudo systemctl restart sage-mcp"
    
    Start-Sleep -Seconds 2
    
    Write-Host "Service status:" -ForegroundColor Yellow
    ssh @SshArgs $VpsHost "sudo systemctl status sage-mcp --no-pager"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Sync Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "  - Start service:   ssh $VpsHost 'sudo systemctl start sage-mcp'"
Write-Host "  - Check status:    ssh $VpsHost 'sudo systemctl status sage-mcp'"
Write-Host "  - View logs:       ssh $VpsHost 'sudo journalctl -u sage-mcp -f'"
