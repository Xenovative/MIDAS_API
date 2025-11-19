# MIDAS - AI Agentic Platform

A modern, API-first AI platform similar to Open WebUI and LLMstudios, built with FastAPI and React. Simple deployment without Docker orchestration.

## Features

- **Multi-LLM Support**: OpenAI, Anthropic Claude, Google Gemini, and local models via Ollama
- **Modern Chat Interface**: Beautiful, responsive UI built with React and TailwindCSS
- **Agent Capabilities**: Web search, web scraping, calculator, and extensible tool system
- **Conversation Management**: Save and manage multiple chat conversations
- **Streaming Responses**: Real-time streaming for better UX
- **Simple Deployment**: No Docker required - runs on any web server with Python and Node.js

## Architecture

```
MIDAS_API/
├── backend/           # FastAPI backend
│   ├── routes/       # API endpoints
│   ├── models.py     # Database models
│   ├── schemas.py    # Pydantic schemas
│   ├── llm_providers.py  # LLM integrations
│   └── agent_tools.py    # Agent tools
├── frontend/         # React frontend
│   └── src/
│       ├── components/
│       ├── store/
│       └── lib/
└── requirements.txt  # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- API keys for your preferred LLM providers

### Installation

1. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your API keys
```

3. **Install frontend dependencies:**

```bash
cd frontend
npm install
```

### Development

Run backend and frontend in separate terminals:

**Terminal 1 - Backend:**
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Access the app at `http://localhost:3000`

## Configuration

Edit `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-change-this

# LLM API Keys (add the ones you want to use)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite+aiosqlite:///./midas.db

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Production Deployment

### Option 1: Traditional Web Server (Nginx + Systemd)

1. **Build frontend:**
```bash
cd frontend
npm run build
```

2. **Setup systemd service for backend:**

Create `/etc/systemd/system/midas-api.service`:
```ini
[Unit]
Description=MIDAS API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/midas/backend
Environment="PATH=/var/www/midas/venv/bin"
ExecStart=/var/www/midas/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Configure Nginx:**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/midas/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

4. **Start services:**
```bash
sudo systemctl enable midas-api
sudo systemctl start midas-api
sudo systemctl reload nginx
```

### Option 2: Platform-as-a-Service (Heroku, Railway, Render)

1. **Create `Procfile`:**
```
web: cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

2. **Add build script to `package.json`:**
```json
{
  "scripts": {
    "build": "cd frontend && npm install && npm run build"
  }
}
```

3. **Deploy using platform CLI or Git push**

### Option 3: VPS with Simple Setup Script

```bash
#!/bin/bash
# deploy.sh

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# Start backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Serve frontend
cd ../frontend/dist
python -m http.server 3000
```

## API Endpoints

### Conversations
- `GET /conversations/` - List all conversations
- `POST /conversations/` - Create new conversation
- `GET /conversations/{id}` - Get conversation with messages
- `DELETE /conversations/{id}` - Delete conversation
- `PATCH /conversations/{id}` - Update conversation title

### Chat
- `POST /chat/` - Send message (non-streaming)
- `POST /chat/stream` - Send message (streaming)

### Models
- `GET /models/` - List available LLM providers and models

### Tools
- `GET /tools/` - List available agent tools
- `POST /tools/{tool_name}` - Execute a tool

## Adding Custom Tools

Create a new tool in `backend/agent_tools.py`:

```python
class CustomTool(AgentTool):
    name = "custom_tool"
    description = "Description of what this tool does"
    parameters = {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
    
    async def execute(self, param1: str) -> Dict[str, Any]:
        # Your tool logic here
        return {
            "success": True,
            "result": "..."
        }
```

Register it in `AgentToolManager`:
```python
self.tools = {
    # ... existing tools
    "custom_tool": CustomTool()
}
```

## Adding New LLM Providers

Extend `LLMProvider` class in `backend/llm_providers.py`:

```python
class CustomProvider(LLMProvider):
    def __init__(self):
        self.client = CustomClient(api_key=settings.custom_api_key)
    
    def is_available(self) -> bool:
        return self.client is not None
    
    async def chat(self, messages, model, temperature, max_tokens, stream):
        # Implementation
        pass
    
    async def chat_stream(self, messages, model, temperature, max_tokens):
        # Implementation
        pass
```

## Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM with async support
- SQLite - Lightweight database
- OpenAI, Anthropic, Google AI SDKs
- BeautifulSoup4 - Web scraping
- DuckDuckGo Search - Web search

**Frontend:**
- React 18 - UI framework
- Vite - Build tool
- TailwindCSS - Styling
- Zustand - State management
- Lucide React - Icons
- React Markdown - Markdown rendering

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.

## Support

For issues and questions, please open a GitHub issue.
