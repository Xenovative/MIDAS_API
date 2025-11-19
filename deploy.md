# Deployment Guide

This guide covers various deployment options for MIDAS without Docker.

## Prerequisites

- Python 3.9+
- Node.js 18+
- A server with at least 1GB RAM
- Domain name (optional, for production)

## Option 1: VPS Deployment (Ubuntu/Debian)

### 1. Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Node.js
sudo apt install python3 python3-pip python3-venv nodejs npm nginx -y

# Install Node.js 18+ (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

### 2. Deploy Application

```bash
# Create application directory
sudo mkdir -p /var/www/midas
sudo chown $USER:$USER /var/www/midas
cd /var/www/midas

# Clone or upload your code
git clone <your-repo> .
# OR upload via SCP/SFTP

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
nano .env  # Edit with your API keys

# Build frontend
cd frontend
npm install
npm run build
cd ..
```

### 3. Setup Systemd Service

Create `/etc/systemd/system/midas.service`:

```ini
[Unit]
Description=MIDAS AI Platform
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/midas/backend
Environment="PATH=/var/www/midas/venv/bin"
EnvironmentFile=/var/www/midas/.env
ExecStart=/var/www/midas/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable midas
sudo systemctl start midas
sudo systemctl status midas
```

### 4. Configure Nginx

Create `/etc/nginx/sites-available/midas`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    # Frontend
    location / {
        root /var/www/midas/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Increase timeouts for streaming
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/midas /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Setup SSL (Optional but Recommended)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Option 2: Shared Hosting with cPanel

### 1. Upload Files

- Upload all files via FTP/File Manager
- Place backend in `~/midas/backend`
- Place frontend in `~/public_html/midas`

### 2. Setup Python App

In cPanel:
1. Go to "Setup Python App"
2. Create new application:
   - Python version: 3.9+
   - Application root: `midas/backend`
   - Application URL: `/api`
   - Application startup file: `main.py`
   - Application Entry point: `app`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Build Frontend

Via SSH or Terminal in cPanel:
```bash
cd ~/midas/frontend
npm install
npm run build
cp -r dist/* ~/public_html/midas/
```

### 4. Configure .htaccess

Create `~/public_html/midas/.htaccess`:

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /midas/
  
  # API requests
  RewriteRule ^api/(.*)$ /api/$1 [P,L]
  
  # Frontend routing
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /midas/index.html [L]
</IfModule>
```

## Option 3: Platform-as-a-Service

### Railway.app

1. Create `railway.toml`:
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
```

2. Deploy:
```bash
railway login
railway init
railway up
```

### Render.com

1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: midas-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT"
    
  - type: web
    name: midas-frontend
    env: static
    buildCommand: "cd frontend && npm install && npm run build"
    staticPublishPath: ./frontend/dist
```

2. Connect GitHub repo and deploy

### Heroku

1. Create `Procfile`:
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. Create `heroku.yml`:
```yaml
build:
  languages:
    - python
    - nodejs
run:
  web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

3. Deploy:
```bash
heroku create midas-app
git push heroku main
```

## Option 4: Windows Server (IIS)

### 1. Install Prerequisites

- Python 3.9+
- Node.js 18+
- IIS with URL Rewrite module
- wfastcgi

### 2. Setup Python

```powershell
# Install wfastcgi
pip install wfastcgi
wfastcgi-enable
```

### 3. Configure IIS

1. Create new site in IIS
2. Point to frontend/dist folder
3. Install URL Rewrite module
4. Create `web.config`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI" 
           path="api/*" 
           verb="*" 
           modules="FastCgiModule" 
           scriptProcessor="C:\Python39\python.exe|C:\Python39\Lib\site-packages\wfastcgi.py" 
           resourceType="Unspecified" 
           requireAccess="Script" />
    </handlers>
    <rewrite>
      <rules>
        <rule name="Frontend" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
            <add input="{REQUEST_URI}" pattern="^/api/" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

## Monitoring and Maintenance

### View Logs

```bash
# Systemd logs
sudo journalctl -u midas -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Update Application

```bash
cd /var/www/midas
git pull
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart midas
```

### Backup Database

```bash
# Backup SQLite database
cp backend/midas.db backup/midas_$(date +%Y%m%d).db
```

## Performance Optimization

### 1. Use Gunicorn for Production

```bash
pip install gunicorn

# Update systemd service
ExecStart=/var/www/midas/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
```

### 2. Enable Gzip in Nginx

Add to nginx config:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
```

### 3. Use PostgreSQL for Production

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Update .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/midas
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
sudo journalctl -u midas -n 50

# Test manually
cd /var/www/midas/backend
source ../venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend shows blank page
- Check browser console for errors
- Verify API proxy is working
- Check nginx error logs

### API requests fail
- Verify CORS settings in .env
- Check nginx proxy configuration
- Ensure backend is running

## Security Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Enable HTTPS with SSL certificate
- [ ] Configure firewall (ufw/iptables)
- [ ] Set proper file permissions
- [ ] Keep dependencies updated
- [ ] Enable rate limiting
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity
