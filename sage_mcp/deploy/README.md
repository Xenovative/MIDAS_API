# Sage MCP - VPS Deployment Guide

This guide covers deploying Sage MCP to a Linux VPS for remote access.

## Deployment Options

### Option 1: Stdio over SSH (Recommended for single user)

MCP's native transport is stdio. You can tunnel this over SSH.

### Option 2: HTTP/SSE Transport (For multiple users or web access)

Requires additional setup with an HTTP wrapper.

---

## Quick Deploy (Ubuntu/Debian)

### On your VPS:

```bash
# 1. Upload the deployment script
scp deploy/setup-vps.sh user@your-vps:/tmp/

# 2. SSH into your VPS
ssh user@your-vps

# 3. Run setup
sudo /tmp/setup-vps.sh
```

### Manual file transfer:

```bash
# From your local machine
rsync -avz --exclude node_modules --exclude .git \
  ./ user@your-vps:/opt/sage-mcp/src/

# Copy database
scp data/sage.db user@your-vps:/opt/sage-mcp/data/
```

---

## Option 1: SSH Tunnel (Stdio Transport)

This is the simplest approach - run the MCP server over SSH.

### Claude Desktop Config (Windows connecting to VPS)

```json
{
  "mcpServers": {
    "sage": {
      "command": "ssh",
      "args": [
        "-o", "StrictHostKeyChecking=no",
        "user@your-vps.com",
        "node /opt/sage-mcp/src/dist/index.js"
      ]
    }
  }
}
```

### With SSH Key (Recommended)

1. Generate SSH key if you don't have one:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/sage_mcp_key
   ```

2. Copy to VPS:
   ```bash
   ssh-copy-id -i ~/.ssh/sage_mcp_key user@your-vps.com
   ```

3. Claude Desktop config:
   ```json
   {
     "mcpServers": {
       "sage": {
         "command": "ssh",
         "args": [
           "-i", "C:/Users/YourName/.ssh/sage_mcp_key",
           "-o", "StrictHostKeyChecking=no",
           "-o", "BatchMode=yes",
           "user@your-vps.com",
           "SAGE_DB_PATH=/opt/sage-mcp/data/sage.db node /opt/sage-mcp/src/dist/index.js"
         ]
       }
     }
   }
   ```

### Troubleshooting SSH

```bash
# Test SSH connection
ssh user@your-vps.com "echo 'SSH works'"

# Test MCP server via SSH
ssh user@your-vps.com "echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}' | node /opt/sage-mcp/src/dist/index.js"
```

---

## Option 2: HTTP/SSE Transport

For web-based access or multiple concurrent users, wrap the MCP server with HTTP.

### Install HTTP Transport Wrapper

```bash
# On VPS
cd /opt/sage-mcp/src
npm install @modelcontextprotocol/server-sse express
```

### Create HTTP Server (`src/http-server.ts`)

```typescript
import express from 'express';
import { SSEServerTransport } from '@modelcontextprotocol/server-sse';
import { createServer } from './index.js';

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/sse', async (req, res) => {
  const transport = new SSEServerTransport('/messages', res);
  const server = await createServer();
  await server.connect(transport);
});

app.post('/messages', express.json(), async (req, res) => {
  // Handle incoming messages
});

app.listen(PORT, () => {
  console.log(`Sage MCP HTTP server running on port ${PORT}`);
});
```

### Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/sage-mcp
server {
    listen 443 ssl http2;
    server_name sage.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/sage.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sage.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_cache_bypass $http_upgrade;
        
        # SSE specific
        proxy_buffering off;
        proxy_read_timeout 86400;
    }
}
```

---

## Systemd Service Management

```bash
# Start the service
sudo systemctl start sage-mcp

# Stop the service
sudo systemctl stop sage-mcp

# Restart the service
sudo systemctl restart sage-mcp

# Enable auto-start on boot
sudo systemctl enable sage-mcp

# Check status
sudo systemctl status sage-mcp

# View logs
sudo journalctl -u sage-mcp -f

# View last 100 lines
sudo journalctl -u sage-mcp -n 100
```

---

## Database Management

### Backup Database

```bash
# On VPS
cp /opt/sage-mcp/data/sage.db /opt/sage-mcp/data/sage.db.backup

# Download to local
scp user@your-vps:/opt/sage-mcp/data/sage.db ./backup/
```

### Restore Database

```bash
# Upload new database
scp ./data/sage.db user@your-vps:/opt/sage-mcp/data/

# Fix permissions
ssh user@your-vps "sudo chown sage:sage /opt/sage-mcp/data/sage.db"

# Restart service
ssh user@your-vps "sudo systemctl restart sage-mcp"
```

### Re-import Papers

```bash
ssh user@your-vps "cd /opt/sage-mcp/src && SAGE_DB_PATH=/opt/sage-mcp/data/sage.db npm run import-xml"
```

---

## Security Recommendations

### 1. Firewall (UFW)

```bash
sudo ufw allow ssh
sudo ufw allow 443/tcp  # If using HTTPS
sudo ufw enable
```

### 2. Fail2ban

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### 3. SSH Hardening

```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

### 4. Automatic Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

---

## Monitoring

### Simple Health Check Script

```bash
#!/bin/bash
# /opt/sage-mcp/health-check.sh

RESPONSE=$(echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  timeout 5 node /opt/sage-mcp/src/dist/index.js 2>/dev/null)

if echo "$RESPONSE" | grep -q "search_papers"; then
  echo "OK"
  exit 0
else
  echo "FAIL"
  exit 1
fi
```

### Cron Job for Monitoring

```bash
# Check every 5 minutes, restart if down
*/5 * * * * /opt/sage-mcp/health-check.sh || systemctl restart sage-mcp
```

---

## Updating the Application

```bash
# On VPS
cd /opt/sage-mcp/src

# Pull latest (if using git)
git pull

# Or rsync from local
# (run from local machine)
rsync -avz --exclude node_modules --exclude data ./ user@vps:/opt/sage-mcp/src/

# Rebuild
npm install
npm run build

# Restart
sudo systemctl restart sage-mcp
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
journalctl -u sage-mcp -n 50

# Test manually
sudo -u sage node /opt/sage-mcp/src/dist/index.js
```

### Permission errors

```bash
# Fix ownership
sudo chown -R sage:sage /opt/sage-mcp

# Fix permissions
sudo chmod 755 /opt/sage-mcp
sudo chmod 644 /opt/sage-mcp/data/sage.db
```

### Database locked

```bash
# Check for stale processes
ps aux | grep sage

# Kill if needed
pkill -f "node.*sage-mcp"

# Restart service
sudo systemctl restart sage-mcp
```

### SSH connection issues

```bash
# Test basic SSH
ssh -v user@your-vps.com

# Check SSH agent
ssh-add -l

# Add key to agent
ssh-add ~/.ssh/sage_mcp_key
```
