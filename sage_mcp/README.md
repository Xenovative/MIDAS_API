# Sage MCP - Academic Research Server

An MCP (Model Context Protocol) server that provides LLMs with access to academic papers and periodicals for research-grounded responses.

## Features

- **Full-text search** across papers using SQLite FTS5
- **Topic/publication filtering** for targeted research
- **Paper retrieval** with full content for detailed analysis
- **Extensible database** - add your own papers programmatically

## Tools Available

| Tool | Description |
|------|-------------|
| `search_papers` | Semantic/keyword search across all papers |
| `get_paper` | Retrieve full paper content by ID |
| `list_topics` | Browse available research topics |
| `list_publications` | Browse available journals/sources |
| `get_papers_by_topic` | Filter papers by topic |
| `get_papers_by_publication` | Filter papers by journal |
| `add_paper` | Add new papers to the database |

---

## Quick Start (Local Setup)

### Prerequisites

- **Node.js** 18+ (recommended: 20 LTS)
- **npm** 9+

### 1. Clone/Download and Install

```bash
cd C:\AIapps\SageMCP   # or your chosen directory
npm install
npm run build
```

### 2. Seed the Database

```bash
# Option A: Sample papers (10 ML/AI papers)
npm run seed

# Option B: Import from XML (if you have papers_database.xml)
npm run import-xml
```

### 3. Verify Installation

```bash
npm start
# Should output: "Sage MCP Server running on stdio"
# Press Ctrl+C to stop
```

---

## Connecting to MCP Clients

### Claude Desktop (Windows)

1. **Locate config file:**
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```
   Usually: `C:\Users\<YourName>\AppData\Roaming\Claude\claude_desktop_config.json`

2. **Edit the config** (create if doesn't exist):
   ```json
   {
     "mcpServers": {
       "sage": {
         "command": "node",
         "args": ["C:/AIapps/SageMCP/dist/index.js"]
       }
     }
   }
   ```

3. **Restart Claude Desktop** completely (quit from system tray, reopen)

4. **Verify connection:** Look for the hammer 🔨 icon in Claude's chat input - click it to see available tools

### Claude Desktop (macOS)

1. **Config location:**
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **Config content:**
   ```json
   {
     "mcpServers": {
       "sage": {
         "command": "node",
         "args": ["/Users/<you>/path/to/SageMCP/dist/index.js"]
       }
     }
   }
   ```

### Windsurf / Cascade

Add to your MCP settings (Settings → MCP Servers):

```json
{
  "sage": {
    "command": "node",
    "args": ["C:/AIapps/SageMCP/dist/index.js"]
  }
}
```

### Cline (VS Code Extension)

1. Open VS Code settings
2. Search for "Cline MCP"
3. Add server configuration:
   ```json
   {
     "sage": {
       "command": "node",
       "args": ["C:/AIapps/SageMCP/dist/index.js"]
     }
   }
   ```

### Custom MCP Client (Programmatic)

```typescript
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const transport = new StdioClientTransport({
  command: 'node',
  args: ['C:/AIapps/SageMCP/dist/index.js'],
});

const client = new Client({ name: 'my-client', version: '1.0.0' }, {});
await client.connect(transport);

// List available tools
const tools = await client.listTools();
console.log(tools);

// Call a tool
const result = await client.callTool({
  name: 'search_papers',
  arguments: { query: '神學', limit: 5 }
});
console.log(result);
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SAGE_DB_PATH` | Custom database file path | `./data/sage.db` |

**Example with custom DB path:**

```json
{
  "mcpServers": {
    "sage": {
      "command": "node",
      "args": ["C:/AIapps/SageMCP/dist/index.js"],
      "env": {
        "SAGE_DB_PATH": "D:/Research/my_papers.db"
      }
    }
  }
}
```

---

## Adding Your Own Papers

### Via the MCP Tool

LLMs can use the `add_paper` tool directly to add papers.

### Via XML Import

Place your XML file in `data/` and run:
```bash
npm run import-xml -- ./data/your_papers.xml
```

### Programmatically

```typescript
import { initDb, addPaper } from './dist/db.js';

await initDb();

addPaper({
  title: 'Your Paper Title',
  authors: 'Author One, Author Two',
  abstract: 'Paper abstract...',
  content: 'Full paper content...',
  publication: 'Journal Name',
  publication_date: '2024-01-15',
  doi: '10.1234/example',
  url: 'https://example.com/paper',
  topics: 'Topic1, Topic2',
  keywords: 'keyword1, keyword2, keyword3'
});
```

---

## Database Schema

Papers are stored in SQLite with full-text search indexing:

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Auto-incrementing primary key |
| `title` | TEXT | Paper title |
| `authors` | TEXT | Comma-separated author list |
| `abstract` | TEXT | Paper abstract |
| `content` | TEXT | Full paper text |
| `publication` | TEXT | Journal/conference name |
| `publication_date` | TEXT | Publication date (YYYY-MM-DD) |
| `doi` | TEXT | DOI identifier (optional) |
| `url` | TEXT | URL to paper (optional) |
| `topics` | TEXT | Comma-separated topics |
| `keywords` | TEXT | Comma-separated keywords |

---

## VPS Deployment

Single command deploys everything (from your local machine):

```powershell
# Windows PowerShell
.\deploy\deploy.ps1 -VpsHost "user@your-vps.com"

# Linux/macOS
./deploy/deploy.sh user@your-vps.com
```

This automatically:
1. Installs Node.js and dependencies on VPS
2. Creates `sage` user and directories
3. Copies source files and database
4. Builds the project
5. Sets up and starts systemd service

**Uninstall:**
```powershell
# Windows
.\deploy\uninstall.ps1 -VpsHost "user@your-vps.com"

# Linux/macOS (or directly on VPS)
./deploy/uninstall.sh
```

See [deploy/README.md](deploy/README.md) for detailed options and troubleshooting.

---

## Troubleshooting

### "Cannot find module" errors
```bash
npm run build  # Rebuild TypeScript
```

### Claude Desktop doesn't show tools
1. Check config JSON syntax (use a JSON validator)
2. Ensure path uses forward slashes: `C:/path/to/file` not `C:\path\to\file`
3. Restart Claude Desktop completely (quit from system tray)
4. Check Claude's logs: `%APPDATA%\Claude\logs\`

### Database errors
```bash
# Reset database
rm -rf data/sage.db
npm run seed  # or npm run import-xml
```

### Test MCP server manually
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/index.js
```

---

## License

MIT
